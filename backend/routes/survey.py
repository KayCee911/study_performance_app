import pandas as pd
from flask import Blueprint, request, jsonify
from models import db, User, Semester, Course, StudyHabit, Performance, StudentProfile
from data_processing.transform_survey import transform_survey_data
from ml.recommender_engine import optimize_recommendation, generate_ai_summary
from ml.similarity import get_similar_students
from ml.retrain import retrain_model
from ml.auto_retrain import should_retrain
from math import sqrt
from flask_jwt_extended import jwt_required, get_jwt_identity

survey_bp = Blueprint("survey", __name__)


# ===============================
# UPLOAD SURVEY (PROTECTED)
# ===============================
@survey_bp.route("/upload-survey", methods=["POST"])
@jwt_required()
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

        user = User.query.filter_by(email=username).first()
        if not user:
            user = User(email=username)
            user.set_password("temp123")
            db.session.add(user)
            db.session.flush()

        profile = StudentProfile.query.filter_by(user_id=user.id).first()
        if not profile:
            profile = StudentProfile(
                user_id=user.id,
                student_id_code=username.split("@")[0],
                department="Unknown",
                level=400
            )
            db.session.add(profile)

        semester = Semester.query.filter_by(
            user_id=user.id,
            name="Survey Semester"
        ).first()

        if not semester:
            semester = Semester(user_id=user.id, name="Survey Semester")
            db.session.add(semester)
            db.session.flush()

        for _, row in group.iterrows():

            course_code = str(row["course"]).strip() if pd.notna(row["course"]) else "UNKNOWN"

            existing_course = Course.query.filter_by(
                semester_id=semester.id,
                course_code=course_code
            ).first()

            if existing_course:
                continue

            course = Course(
                semester_id=semester.id,
                course_code=course_code,
                unit=int(row["unit"]) if pd.notna(row["unit"]) else 3,
                difficulty=int(row["difficulty"]) if pd.notna(row["difficulty"]) else 0
            )
            db.session.add(course)
            db.session.flush()

            habit = StudyHabit(
                course_id=course.id,
                study_hours=float(row["study_time"]) if pd.notna(row["study_time"]) else 0.0,
                study_method=str(row["study_method"]).capitalize() if pd.notna(row["study_method"]) else "Unknown"
            )
            db.session.add(habit)

            performance = Performance(
                course_id=course.id,
                grade=str(row["grade"]),
                gpa=float(row["points"])
            )
            db.session.add(performance)

    db.session.commit()

    if should_retrain():
        retrain_model()

    return jsonify({
        "message": "Upload successful",
        "users": int(df["username"].nunique())
    })


# ===============================
# USER INSIGHTS (PROTECTED)
# ===============================
@survey_bp.route("/user/insights", methods=["GET"])
@jwt_required()
def user_insights():

    email = get_jwt_identity()
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
# ML RECOMMENDER (PROTECTED)
# ===============================
@survey_bp.route("/ml-recommend", methods=["GET"])
@jwt_required()
def ml_recommend():

    email = get_jwt_identity()
    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({"error": "User not found"}), 404

    results = []

    similar_students = get_similar_students(email)
    peer_message = "No peer data available yet"

    if isinstance(similar_students, pd.DataFrame) and not similar_students.empty:
        peer_avg = round(similar_students["avg_gpa"].mean(), 2)
        peer_hours = round(similar_students["avg_hours"].mean(), 2)

        peer_message = f"Students like you study ~{peer_hours} hrs and average GPA {peer_avg}."

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

            current = rec["current_gpa"]
            improved = rec["improved_gpa"]

            perf.predicted_gpa = improved

            suggestion = (
                "Current strategy is optimal"
                if improved <= current
                else f"Study {rec.get('recommended_hours', 0)} hrs using {rec.get('recommended_method', 'Unknown')}"
            )

            gap = improved - current

            if current < 2.0:
                risk = "high"
            elif gap > 1.5:
                risk = "medium"
            else:
                risk = "low"

            results.append({
                "course": c.course_code,
                "current_gpa": current,
                "improved_gpa": improved,
                "suggestion": suggestion,
                "confidence": rec.get("confidence", 0),
                "why": rec.get("explanations", []),
                "peer_insight": peer_message,
                "risk": risk
            })

    db.session.commit()

    summary = generate_ai_summary(results)

    return jsonify({
        "results": results,
        "summary": summary
    })


# ===============================
# MODEL ERROR (PROTECTED)
# ===============================
@survey_bp.route("/model-error", methods=["GET"])
@jwt_required()
def model_error():

    email = get_jwt_identity()
    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({"error": "User not found"}), 404

    errors = []
    detailed = []

    for sem in user.semesters:
        for c in sem.courses:

            perf = c.performance

            if not perf or perf.gpa is None or perf.predicted_gpa is None:
                continue

            actual = perf.gpa
            predicted = perf.predicted_gpa

            error = actual - predicted
            errors.append(error)

            detailed.append({
                "course": c.course_code,
                "actual": actual,
                "predicted": predicted,
                "error": round(error, 2)
            })

    if not errors:
        return jsonify({"message": "No prediction data available yet"})

    mae = sum(abs(e) for e in errors) / len(errors)
    rmse = sqrt(sum(e**2 for e in errors) / len(errors))
    bias = sum(errors) / len(errors)

    return jsonify({
        "courses": detailed,
        "metrics": {
            "MAE": round(mae, 3),
            "RMSE": round(rmse, 3),
            "Bias": round(bias, 3)
        }
    })


# ===============================
# AUTO RETRAIN (
# ===============================
@survey_bp.route("/auto-retrain", methods=["POST"])
@jwt_required()
def auto_retrain():

    if not should_retrain():
        return jsonify({"message": "Model is stable"})

    result = retrain_model()

    return jsonify({
        "message": "Model auto-retrained",
        "details": result
    })