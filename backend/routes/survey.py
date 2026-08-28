import pandas as pd
from flask import Blueprint, request, jsonify
from models import db, User, Semester, Course, StudyHabit, Performance, StudentProfile
from data_processing.transform_survey import transform_survey_data
from ml.recommender_engine import optimize_recommendation, generate_ai_summary
from ml.similarity import get_similar_students
from ml.retrain import retrain_model
from ml.auto_retrain import should_retrain
from flask import current_app
from math import sqrt
import os

survey_bp = Blueprint("survey", __name__)


# ===============================
# UPLOAD SURVEY (FOR MODEL TRAINING ONLY)
# ===============================
@survey_bp.route("/upload-survey", methods=["POST"])
def upload_survey():
    """
    Upload CSV file to train the ML model.
    CSV should NOT create user accounts - only used for model training.
    """
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

        feedback_results = []

        for record in df.to_dict(orient="records"):
            rec = optimize_recommendation(
                current_hours=float(record.get("study_time", 0) or 0),
                difficulty=float(record.get("difficulty", 0) or 0),
                method=str(record.get("study_method", "Passive")),
                unit=float(record.get("unit", 3) or 3),
            )

            feedback_results.append({
                "username": record.get("username", "Unknown"),
                "course": record.get("course", "Unknown"),
                "current_gpa": round(float(rec.get("current_gpa", 0)), 2),
                "improved_gpa": round(float(rec.get("improved_gpa", 0)), 2),
                "projected_gpa": round(float(rec.get("improved_gpa", 0)), 2),
                "recommended_study_hours": int(rec.get("recommended_hours", 0)),
                "recommended_method": rec.get("recommended_method", "Active"),
                "confidence": round(float(rec.get("confidence", 0)), 2),
                "ways_to_improve": rec.get("explanations", []),
                "suggestion": (
                    f"Study {rec.get('recommended_hours', 0)} hrs using {rec.get('recommended_method', 'Active')} "
                    f"to achieve {round(float(rec.get('improved_gpa', 0)), 2)} GPA"
                ),
            })

        summary = generate_ai_summary(
            [{
                "course": r["course"],
                "current_gpa": r["current_gpa"],
                "improved_gpa": r["projected_gpa"]
            } for r in feedback_results]
        )

        average_projected_gpa = round(
            sum(r["projected_gpa"] for r in feedback_results) / len(feedback_results), 2
        ) if feedback_results else 0

        # ✅ Only retrain model - NO user/course creation
        if should_retrain():
            retrain_model()

        # Cleanup
        if os.path.exists(file_path):
            os.remove(file_path)

        return jsonify({
            "message": "CSV uploaded successfully for model training",
            "status": "Model will be retrained if conditions are met",
            "feedback": {
                "summary": summary,
                "average_projected_gpa": average_projected_gpa,
                "recommendations": feedback_results[:10],
                "total_courses": len(feedback_results),
            },
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ===============================
# USER INSIGHTS (PROTECTED)
# ===============================
@survey_bp.route("/user/<email>/insights", methods=["GET"])
def user_insights(email):
    # Public endpoint: return insights for the requested email
    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({"error": "User not found"}), 404

    gpas, hours, diffs = [], [], []
    total_courses = 0

    for sem in user.semesters:
        for c in sem.courses:
            total_courses += 1

            if c.performance:
                if c.performance.gpa is not None:
                    gpas.append(c.performance.gpa)
                elif c.performance.predicted_gpa is not None:
                    gpas.append(c.performance.predicted_gpa)

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
        "total_courses": total_courses
    })


# ===============================
# ML RECOMMEND (PROTECTED)
# ===============================
@survey_bp.route("/ml-recommend/<email>", methods=["GET"])
def ml_recommend(email):
    # Public endpoint: return recommendations for the requested email
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
            habit = c.study_habits[0] if c.study_habits else None
            study_hours = habit.study_hours if habit and habit.study_hours is not None else 0.0
            study_method = habit.study_method if habit and habit.study_method else "Passive"

            rec = optimize_recommendation(
                study_hours,
                c.difficulty or 0,
                study_method,
                c.unit or 3
            )

            current = rec["current_gpa"]
            improved = rec["improved_gpa"]

            # derive risk band: high / medium / low
            if current < 2.5:
                risk_level = "high"
            elif current < 3.5:
                risk_level = "medium"
            else:
                risk_level = "low"

            results.append({
                "course": c.course_code or "Unknown",
                "current_gpa": current,
                "improved_gpa": improved,
                "suggestion": (
                    "Optimal" if improved <= current
                    else f"Study {rec.get('recommended_hours')} hrs using {rec.get('recommended_method')}"
                ),
                "confidence": rec.get("confidence", 0),
                "why": rec.get("explanations", []),
                "peer_insight": peer_message,
                "risk": risk_level
            })

    summary = generate_ai_summary(results)

    return jsonify({
        "results": results,
        "summary": summary
    })


# ===============================
# ADD COURSE MANUALLY WITH PREDICTIONS
# ===============================
@survey_bp.route("/add-course", methods=["POST"])
def add_course():
    """
    Add a course manually for a user and generate ML predictions.

    Request body:
    {
        "course_code": "CSC101",
        "course_name": "Introduction to Programming",
        "unit": 3,
        "difficulty": 2,
        "semester_id": 1,  // optional, or use semester_name for new
        "semester_name": "First Semester 2024"  // optional, creates if not exists
    }
    """
    try:
        # Determine which user the course belongs to: prefer explicit `email` in body
        data_preview = request.get_json(silent=True) or {}
        user_email = data_preview.get('email') or data_preview.get('username')
        if not user_email:
            # fall back to first user in DB
            u = User.query.first()
            user_email = u.email if u else None

        user = User.query.filter_by(email=user_email).first()

        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Get request data
        data = request.get_json()
        course_code = data.get("course_code", "").strip().upper()
        course_name = data.get("course_name", "").strip()
        unit = data.get("unit")
        difficulty = data.get("difficulty")
        semester_id = data.get("semester_id")
        semester_name = (data.get("semester_name") or "").strip()
        study_hours = data.get("study_hours")
        study_method = data.get("study_method", "Passive")
        
        # Validation
        if not course_code:
            return jsonify({"error": "Course code is required"}), 400
        
        if unit is None or difficulty is None:
            return jsonify({"error": "Units and difficulty are required"}), 400
        
        try:
            unit = int(unit)
            difficulty = int(difficulty)
        except (ValueError, TypeError):
            return jsonify({"error": "Units and difficulty must be integers"}), 400

        if study_hours not in (None, ""):
            try:
                study_hours = float(study_hours)
            except (ValueError, TypeError):
                return jsonify({"error": "Study hours must be a number"}), 400

            if study_hours < 0:
                return jsonify({"error": "Study hours cannot be negative"}), 400
        
        if not (1 <= unit <= 5):
            return jsonify({"error": "Units must be between 1 and 5"}), 400
        
        if not (1 <= difficulty <= 5):
            return jsonify({"error": "Difficulty must be between 1 and 5"}), 400
        
        # Handle semester
        semester = None
        
        if semester_id not in (None, ""):
            try:
                semester_id = int(semester_id)
            except (ValueError, TypeError):
                return jsonify({"error": "Invalid semester selected"}), 400

            # Use existing semester
            semester = Semester.query.filter_by(
                id=semester_id,
                user_id=user.id
            ).first()
            
            if not semester:
                return jsonify({"error": "Semester not found"}), 404
        elif semester_name:
            # Create new semester if it doesn't exist
            semester = Semester.query.filter_by(
                user_id=user.id,
                name=semester_name
            ).first()
            
            if not semester:
                semester = Semester(user_id=user.id, name=semester_name)
                db.session.add(semester)
                db.session.flush()
        else:
            # If no semester info provided, try to use the user's latest semester
            semester = Semester.query.filter_by(user_id=user.id).order_by(Semester.id.desc()).first()
            if not semester:
                # Auto-create a default semester so adding a course is seamless
                semester = Semester(user_id=user.id, name="Current")
                db.session.add(semester)
                db.session.flush()
        
        # Check if course already exists
        existing_course = Course.query.filter_by(
            semester_id=semester.id,
            course_code=course_code
        ).first()
        
        if existing_course:
            return jsonify({"error": f"Course {course_code} already exists in this semester"}), 409
        
        # Create course
        course = Course(
            semester_id=semester.id,
            course_code=course_code,
            unit=unit,
            difficulty=difficulty
        )
        db.session.add(course)
        db.session.flush()

        normalized_method = "Passive"
        if study_method:
            method_text = str(study_method).strip().title()
            if method_text == "Mixed":
                normalized_method = "Active"
            elif method_text in ["Active", "Passive"]:
                normalized_method = method_text

        if study_hours is None:
            study_hours = 0.0

        study_habit = StudyHabit(
            course_id=course.id,
            study_hours=float(study_hours),
            study_method=normalized_method,
            focus_score=None
        )
        db.session.add(study_habit)
        
        # ✅ GENERATE PREDICTIONS FOR NEW COURSE
        # Use the optional study input when provided for more accurate recommendations
        try:
            prediction = optimize_recommendation(
                current_hours=float(study_hours),
                difficulty=difficulty,
                method=normalized_method,
                unit=unit
            )
        except Exception as pred_error:
            # If prediction fails, return generic recommendation
            prediction = {
                "current_gpa": 0,
                "improved_gpa": 2.5,
                "recommended_hours": 3,
                "recommended_method": "Active",
                "confidence": 0.6,
                "explanations": ["Start with active study methods"]
            }
        
        # Persist a lightweight performance snapshot so dashboard stats update immediately.
        performance = Performance(
            course_id=course.id,
            grade="P",
            gpa=float(prediction.get("current_gpa", 0) or 0),
            predicted_gpa=float(prediction.get("improved_gpa", prediction.get("current_gpa", 0)) or 0)
        )
        db.session.add(performance)

        # Commit changes
        db.session.commit()
        
        return jsonify({
            "message": f"Course {course_code} added successfully with predictions",
            "course": {
                "id": course.id,
                "code": course.course_code,
                "name": course_name if course_name else course.course_code,
                "unit": course.unit,
                "difficulty": course.difficulty,
                "semester": semester.name
            },
            "prediction": {
                "current_gpa": prediction.get("current_gpa", 0),
                "projected_gpa": prediction.get("improved_gpa", 2.5),
                "recommended_study_hours": prediction.get("recommended_hours", 3),
                "recommended_method": prediction.get("recommended_method", "Active"),
                "confidence": prediction.get("confidence", 0.6),
                "explanations": prediction.get("explanations", []),
                "suggestion": f"Study {prediction.get('recommended_hours', 3)} hours using {prediction.get('recommended_method', 'Active')} method to achieve {prediction.get('improved_gpa', 2.5)} GPA"
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to add course: {str(e)}"}), 500


# ===============================
# GET USER SEMESTERS
# ===============================
@survey_bp.route("/api/semesters", methods=["GET"])
def get_semesters():
    """Get all semesters for the requested user (public endpoint)."""
    try:
        user_email = request.args.get('email') or (User.query.first().email if User.query.first() else None)

        user = User.query.filter_by(email=user_email).first()

        if not user:
            return jsonify({"error": "User not found"}), 404

        semesters = Semester.query.filter_by(user_id=user.id).all()

        return jsonify({
            "semesters": [
                {"id": s.id, "name": s.name}
                for s in semesters
            ]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500