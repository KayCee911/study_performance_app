import pandas as pd

from flask import Blueprint, request, jsonify
from data_processing.transform_survey import transform_survey_data
from models import db, User, Semester, Course, StudyHabit, Performance
from ml.model_loader import predict_gpa
from app import model, imputer

survey_bp = Blueprint("survey", __name__)


@survey_bp.route("/upload-survey", methods=["POST"])
def upload_survey():

    print("FILES:", request.files)

    # ✅ FILE VALIDATION
    if "file" not in request.files:
        return jsonify({"error": "No file part in request"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    # ✅ SAVE TEMP FILE
    file_path = "temp.csv"
    file.save(file_path)

    # ✅ TRANSFORM DATA
    df = transform_survey_data(file_path)

    # ✅ CLEAN DATA (CRITICAL)
    df = df.dropna(subset=["grade", "points"])
    df = df[df["grade"].astype(str).str.lower() != "nan"]

    # ✅ PROCESS USERS
    for username, group in df.groupby("username"):

        # GET OR CREATE USER
        user = User.query.filter_by(email=username).first()

        if not user:
            user = User(email=username, password="temp123")
            db.session.add(user)
            db.session.flush()

        # CREATE SEMESTER
        semester = Semester(
            user_id=user.id,
            name="Survey Semester"
        )
        db.session.add(semester)
        db.session.flush()

        # PROCESS COURSES
        for _, row in group.iterrows():

            # EXTRA SAFETY
            if pd.isna(row["grade"]) or pd.isna(row["points"]):
                continue

            # COURSE
            course = Course(
                semester_id=semester.id,
                course_code=str(row["course"]).strip(),
                unit=3,                 # placeholder for now
                difficulty=row.get("difficulty")         # not yet extracted
            )
            db.session.add(course)
            db.session.flush()

            # STUDY HABIT (currently unavailable → None)
            habit = StudyHabit(
                course_id=course.id,
                study_hours=row.get("study_time"),
                study_method=row.get("study_method")
            )
            db.session.add(habit)

            # PERFORMANCE
            performance = Performance(
                course_id=course.id,
                grade=str(row["grade"]).strip(),
                gpa=float(row["points"])
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

            performance = course.performance
            habit = course.study_habits[0] if course.study_habits else None

            result.append({
                "course_code": course.course_code,
                "grade": performance.grade if performance else None,
                "gpa": performance.gpa if performance else None,
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

    total_points = 0
    total_courses = 0

    for semester in user.semesters:
        for course in semester.courses:

            if course.performance and course.performance.gpa is not None:
                total_points += course.performance.gpa
                total_courses += 1

    if total_courses == 0:
        return jsonify({"gpa": 0})

    gpa = total_points / total_courses

    return jsonify({
        "email": email,
        "gpa": round(gpa, 2)
    })


# ===============================
# ANALYTICS
# ===============================
@survey_bp.route("/analytics/difficulty-vs-gpa", methods=["GET"])
def difficulty_vs_gpa():

    results = []

    courses = Course.query.all()

    for course in courses:
        if course.performance and course.difficulty is not None:

            results.append({
                "difficulty": course.difficulty,
                "gpa": course.performance.gpa
            })

    return jsonify(results)


@survey_bp.route("/analytics/studytime-vs-gpa", methods=["GET"])
def studytime_vs_gpa():

    results = []

    habits = StudyHabit.query.all()

    for habit in habits:
        if habit.study_hours is not None and habit.course.performance:

            results.append({
                "study_hours": habit.study_hours,
                "gpa": habit.course.performance.gpa
            })

    return jsonify(results)


@survey_bp.route("/predict-gpa", methods=["POST"])
def predict():

    data = request.get_json()

    study_hours = data.get("study_hours")
    difficulty = data.get("difficulty")
    study_method = data.get("study_method")

    # VALIDATION
    if study_hours is None or difficulty is None or study_method is None:
        return jsonify({"error": "Missing fields"}), 400

    try:
        prediction = predict_gpa(
            float(study_hours),
            float(difficulty),
            study_method
        )

        return jsonify({
            "predicted_gpa": round(prediction, 2)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    


@survey_bp.route("/predict", methods=["POST"])
def predict_gpa():

    data = request.get_json()

    try:
        study_hours = data.get("study_hours")
        difficulty = data.get("difficulty")
        study_method = data.get("study_method")

        # 🔹 VALIDATION
        if study_hours is None or difficulty is None or study_method is None:
            return jsonify({"error": "Missing fields"}), 400

        # 🔹 CLEAN INPUT (same logic as training)
        study_hours = float(study_hours)
        difficulty = float(difficulty)

        study_method_map = {
            "Active": 1,
            "Passive": 0
        }

        study_method = study_method_map.get(study_method)

        if study_method is None:
            return jsonify({"error": "Invalid study_method"}), 400

        # 🔹 PREPARE INPUT
        X = [[study_hours, difficulty, study_method]]

        # 🔹 APPLY IMPUTER
        X = imputer.transform(X)

        # 🔹 PREDICT
        prediction = model.predict(X)[0]

        return jsonify({
            "predicted_gpa": round(float(prediction), 2)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500