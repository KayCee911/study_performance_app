import pandas as pd

from flask import Blueprint, request, jsonify
from data_processing.transform_survey import transform_survey_data
from models import db, User, Semester, Course, StudyHabit, Performance, StudentProfile
from ml.recommender_engine import optimize_recommendation, generate_ai_summary
from ml.similarity import get_similar_students
from ml.evaluate import evaluate_model

survey_bp = Blueprint("survey", __name__)


# ===============================
# UPLOAD SURVEY
# ===============================
@survey_bp.route("/upload-survey", methods=["POST"])
def upload_survey():

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
            user = User(email=username) 
            user.set_password("temp123")
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
        semester = Semester.query.filter_by(
            user_id=user.id,
            name="Survey Semester"
        ).first()

        if not semester:
            semester = Semester(user_id=user.id, name="Survey Semester")
            db.session.add(semester)
            db.session.flush()

        # ---------- COURSES ----------
        for _, row in group.iterrows():

            course_code = str(row["course"]).strip() if pd.notna(row["course"]) else "UNKNOWN"

            # 🔥 Prevent duplicates
            existing_course = Course.query.filter_by(
                semester_id=semester.id,
                course_code=course_code
            ).first()

            if existing_course:
                continue

            unit = int(row["unit"]) if pd.notna(row["unit"]) else 3
            difficulty = int(row["difficulty"]) if pd.notna(row["difficulty"]) else 0
            study_hours = float(row["study_time"]) if pd.notna(row["study_time"]) else 0.0
            study_method = (
                str(row["study_method"]).strip().capitalize()
                if pd.notna(row["study_method"]) else "Unknown"
            )

            grade = str(row["grade"]).strip()
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

            # HABIT
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
# COURSES
# ===============================
@survey_bp.route("/user/<email>/courses", methods=["GET"])
def get_user_courses(email):

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    result = []

    for sem in user.semesters:
        for c in sem.courses:

            perf = c.performance
            habit = c.study_habits[0] if c.study_habits else None

            result.append({
                "course_code": c.course_code,
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

    total, count = 0, 0

    for sem in user.semesters:
        for c in sem.courses:
            if c.performance and c.performance.gpa is not None:
                total += c.performance.gpa
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

            if c.performance and c.performance.gpa is not None:
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
# ML RECOMMENDER 
# ===============================
@survey_bp.route("/ml-recommend/<email>", methods=["GET"])
def ml_recommend(email):

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    results = []

    # =========================
    # CLUSTERING 
    # =========================
    similar_students = get_similar_students(email)

    peer_message = "No peer data available yet"

    if isinstance(similar_students, pd.DataFrame) and not similar_students.empty:

        if "avg_gpa" in similar_students.columns:

            peer_avg = round(similar_students["avg_gpa"].mean(), 2)
            peer_hours = round(similar_students["avg_hours"].mean(), 2)

            user_row = similar_students[
            similar_students["username"] == email.lower()
        ]

            rank_text = ""

            if not user_row.empty and "rank" in similar_students.columns:
                user_rank = int(user_row.iloc[0]["rank"])
                total = len(similar_students)

                rank_text = f" You rank {user_rank}/{total} in your peer group."

            peer_message = (
            f"Students like you study ~{peer_hours} hrs "
            f"and average GPA {peer_avg}.{rank_text}"
        )

    # =========================
    # COURSE LOOP
    # =========================
    for sem in user.semesters:
        for c in sem.courses:

            perf = c.performance
            habit = c.study_habits[0] if c.study_habits else None

            if not perf or not habit:
                continue

            rec = optimize_recommendation(
                habit.study_hours or 0,
                c.difficulty or 0,
                habit.study_method or "Unknown",
                c.unit or 3
            )

            suggestion = (
                "Current strategy is optimal"
                if rec["improved_gpa"] <= rec["current_gpa"]
                else f"Study {rec['recommended_hours']} hrs using {rec['recommended_method']}"
            )

            results.append({
                "course": c.course_code,
                "current_gpa": rec["current_gpa"],
                "improved_gpa": rec["improved_gpa"],
                "suggestion": suggestion,
                "confidence": rec.get("confidence", 0),
                "why": rec.get("explanations", []),
                "peer_insight": peer_message
            })

    summary = generate_ai_summary(results)

    return jsonify({
        "results": results,
        "summary": summary
    })


@survey_bp.route("/evaluate-model", methods=["GET"])
def evaluate():

    file_path = "temp.csv"

    df = transform_survey_data(file_path)
    df = df.dropna(subset=["points"])

    metrics = evaluate_model(df)

    return jsonify(metrics)