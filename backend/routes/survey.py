import pandas as pd

from flask import Blueprint, request, jsonify
from data_processing.transform_survey import transform_survey_data
from models import db, User, Semester, Course, StudyHabit, Performance, StudentProfile
from ml.model_loader import predict_gpa

survey_bp = Blueprint("survey", __name__)


@survey_bp.route("/upload-survey", methods=["POST"])
def upload_survey():

    print("FILES:", request.files)

    if "file" not in request.files:
        return jsonify({"error": "No file part in request"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    file_path = "temp.csv"
    file.save(file_path)

    df = transform_survey_data(file_path)

    df = df.dropna(subset=["grade", "points"])

    for username, group in df.groupby("username"):

        # ---------- USER ----------
        user = User.query.filter_by(email=username).first()

        if not user:
            user = User(email=username, password="temp123")
            db.session.add(user)
            db.session.flush()

        # ---------- PROFILE ----------
        profile = StudentProfile.query.filter_by(user_id=user.id).first()

        if not profile:
            profile = StudentProfile(
                user_id=user.id,
                student_id_code=username.split("@")[0],
                department="Unknown",
                level=400
            )
            db.session.add(profile)

        # ---------- SEMESTER ----------
        semester = Semester(
            user_id=user.id,
            name="Survey Semester"
        )
        db.session.add(semester)
        db.session.flush()

        # ---------- COURSES ----------
        for _, row in group.iterrows():

            # SAFE VALUES (NO row.get!)
            course_code = row["course"]
            unit = int(row["unit"])
            difficulty = int(row["difficulty"])
            study_hours = float(row["study_time"])
            study_method = str(row["study_method"])
            grade = str(row["grade"])
            gpa = float(row["points"])

            # COURSE
            course = Course(
                semester_id=semester.id,
                course_code=course_code,
                unit=unit,
                difficulty=difficulty
            )
            db.session.add(course)
            db.session.flush()

            # STUDY HABIT
            habit = StudyHabit(
                course_id=course.id,
                study_hours=study_hours,
                study_method=study_method,
                focus_score=None
            )
            db.session.add(habit)

            # PERFORMANCE
            performance = Performance(
                course_id=course.id,
                grade=grade,
                gpa=gpa
            )
            db.session.add(performance)

    db.session.commit()

    return jsonify({
        "message": "Upload successful",
        "users": int(df["username"].nunique())
    })


# ===============================
# USER COURSES
# ===============================
@survey_bp.route("/user/<email>/courses", methods=["GET"])
def get_user_courses(email):

    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({"error": "User not found"}), 404

    result = []

    for semester in user.semesters:
        for course in semester.courses:

            perf = course.performance
            habit = course.study_habits[0] if course.study_habits else None

            result.append({
                "course_code": course.course_code,
                "grade": perf.grade if perf else None,
                "gpa": perf.gpa if perf else None,
                "study_hours": habit.study_hours if habit else None,
                "study_method": habit.study_method if habit else None
            })

    return jsonify(result)


# ===============================
# GPA
# ===============================
@survey_bp.route("/user/<email>/gpa", methods=["GET"])
def get_user_gpa(email):

    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({"error": "User not found"}), 404

    total = 0
    count = 0

    for sem in user.semesters:
        for course in sem.courses:
            if course.performance:
                total += course.performance.gpa
                count += 1

    return jsonify({
        "email": email,
        "gpa": round(total / count, 2) if count else 0
    })


# ===============================
# INSIGHTS
# ===============================
@survey_bp.route("/user/<email>/insights", methods=["GET"])
def user_insights(email):

    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({"error": "User not found"}), 404

    gpas, hours, diffs = [], [], []

    for sem in user.semesters:
        for c in sem.courses:

            if c.performance:
                gpas.append(c.performance.gpa)

            if c.difficulty is not None:
                diffs.append(c.difficulty)

            if c.study_habits:
                h = c.study_habits[0].study_hours
                if h is not None:
                    hours.append(h)

    return jsonify({
        "avg_gpa": round(sum(gpas)/len(gpas), 2) if gpas else 0,
        "avg_study_hours": round(sum(hours)/len(hours), 2) if hours else 0,
        "avg_difficulty": round(sum(diffs)/len(diffs), 2) if diffs else 0,
        "total_courses": len(gpas)
    })


# ===============================
# RECOMMENDATIONS
# ===============================
@survey_bp.route("/recommendations/<email>", methods=["GET"])
def recommendations(email):

    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({"error": "User not found"}), 404

    recs = set()

    for sem in user.semesters:
        for c in sem.courses:

            perf = c.performance
            habit = c.study_habits[0] if c.study_habits else None

            if not perf or not habit:
                continue

            if perf.gpa < 3 and habit.study_hours < 3:
                recs.add(f"Increase study time for {c.course_code}")

            if perf.gpa < 3 and habit.study_method == "Passive":
                recs.add(f"Use Active study method for {c.course_code}")

            if c.difficulty >= 4:
                recs.add(f"{c.course_code} is difficult, allocate more time")

    return jsonify({"recommendations": list(recs)})

from ml.recommender import recommend

@survey_bp.route("/ml-recommend/<email>", methods=["GET"])
def ml_recommend(email):

    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({"error": "User not found"}), 404

    results = []

    for semester in user.semesters:
        for course in semester.courses:

            perf = course.performance
            habit = course.study_habits[0] if course.study_habits else None

            if not perf or not habit:
                continue

            rec = recommend(
                habit.study_hours or 0,
                course.difficulty or 0,
                habit.study_method or "Unknown",
                course.unit or 3
            )

            results.append({
                "course": course.course_code,
                "current_gpa": rec["current_gpa"],
                "improved_gpa": rec["improved_gpa"],
                "suggestion": rec["suggestion"]
            })

    return jsonify(results)