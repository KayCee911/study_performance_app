import pandas as pd
from flask import Blueprint, request, jsonify
from models import db, User, Semester, Course, StudyHabit, Performance, StudentProfile
from data_processing.transform_survey import transform_survey_data
from ml.recommender_engine import optimize_recommendation, generate_ai_summary
from ml.similarity import get_similar_students
from ml.retrain import retrain_model
from ml.auto_retrain import should_retrain
from math import sqrt
import os

survey_bp = Blueprint("survey", __name__)


# ===============================
# UPLOAD SURVEY
# ===============================
@survey_bp.route("/upload-survey", methods=["POST"])
def upload_survey():

    try:
        if "file" not in request.files:
            return jsonify({"error": "No file part in request"}), 400

        file = request.files["file"]

        if file.filename == "":
            return jsonify({"error": "No selected file"}), 400

        file_path = "temp.csv"
        file.save(file_path)

        df = transform_survey_data(file_path)

        if df.empty:
            return jsonify({"error": "No valid data"}), 400

        df = df.dropna(subset=["grade", "points"])

        users_created = 0
        courses_created = 0

        for username, group in df.groupby("username"):

            user = User.query.filter_by(email=username).first()

            if not user:
                user = User(email=username)
                user.set_password("temp123")
                db.session.add(user)
                db.session.flush()
                users_created += 1

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

                course_code = str(row.get("course", "")).strip().upper()

                if not course_code:
                    continue

                existing = Course.query.filter_by(
                    semester_id=semester.id,
                    course_code=course_code
                ).first()

                if existing:
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
                    study_hours=float(row["study_time"]) if pd.notna(row["study_time"]) else 0,
                    study_method=str(row.get("study_method", "Passive")).capitalize()
                )
                db.session.add(habit)

                performance = Performance(
                    course_id=course.id,
                    grade=str(row["grade"]),
                    gpa=float(row["points"])
                )
                db.session.add(performance)

                courses_created += 1

        db.session.commit()

        if os.path.exists(file_path):
            os.remove(file_path)

        if should_retrain():
            retrain_model()

        return jsonify({
            "message": "Upload successful",
            "users_created": users_created,
            "courses_created": courses_created
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# ===============================
# USER INSIGHTS (FIXED)
# ===============================
@survey_bp.route("/user/<email>/insights", methods=["GET"])
def user_insights(email):   # ✅ FIXED PARAM

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
# ML RECOMMEND (FIXED ROUTE)
# ===============================
@survey_bp.route("/ml-recommend/<email>", methods=["GET"])
def ml_recommend(email):   # ✅ MATCH FRONTEND

    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({"error": "User not found"}), 404

    results = []

    similar_students = get_similar_students(email)
    peer_message = "No peer data available"

    if isinstance(similar_students, pd.DataFrame) and not similar_students.empty:
        peer_avg = round(similar_students["avg_gpa"].mean(), 2)
        peer_hours = round(similar_students["avg_hours"].mean(), 2)
        peer_message = f"Students like you study ~{peer_hours} hrs and avg GPA {peer_avg}"

    for sem in user.semesters:
        for c in sem.courses:

            if not c.performance or not c.study_habits:
                continue

            habit = c.study_habits[0]
            perf = c.performance

            rec = optimize_recommendation(
                habit.study_hours or 0,
                c.difficulty or 0,
                habit.study_method or "Unknown",
                c.unit or 3
            )

            current = rec["current_gpa"]
            improved = rec["improved_gpa"]

            results.append({
                "course": c.course_code,
                "current_gpa": current,
                "improved_gpa": improved,
                "suggestion": (
                    "Optimal" if improved <= current
                    else f"Study {rec.get('recommended_hours')} hrs using {rec.get('recommended_method')}"
                ),
                "confidence": rec.get("confidence", 0),
                "why": rec.get("explanations", []),
                "peer_insight": peer_message,
                "risk": "high" if current < 2 else "low"
            })

    summary = generate_ai_summary(results)

    return jsonify({
        "results": results,
        "summary": summary
    })