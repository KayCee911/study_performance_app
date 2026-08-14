from flask import Blueprint, jsonify, request, render_template
from models import db, User, Semester, Course, StudentProfile
from utils.validators import is_valid_email
from flask_jwt_extended import jwt_required, get_jwt_identity

admin_bp = Blueprint("admin", __name__)


def get_current_admin():
    current_email = get_jwt_identity()
    if not current_email:
        return None
    return User.query.filter_by(email=current_email).first()


@admin_bp.route("/admin/dashboard", methods=["GET"])
@jwt_required()
def admin_dashboard():
    current_admin = get_current_admin()
    if not current_admin or not current_admin.is_admin:
        return jsonify({"error": "Admin access required"}), 403
    return render_template("admin-dashboard.html")


@admin_bp.route("/admin/users", methods=["GET"])
@jwt_required()
def list_users():
    current_admin = get_current_admin()
    if not current_admin or not current_admin.is_admin:
        return jsonify({"error": "Admin access required"}), 403

    users = User.query.order_by(User.created_at.desc()).all()
    return jsonify([
        {
            "id": user.id,
            "email": user.email,
            "is_admin": user.is_admin,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }
        for user in users
    ])


@admin_bp.route("/admin/users", methods=["POST"])
@jwt_required()
def create_user():
    current_admin = get_current_admin()
    if not current_admin or not current_admin.is_admin:
        return jsonify({"error": "Admin access required"}), 403

    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    is_admin = bool(data.get("is_admin", False))

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    if not is_valid_email(email):
        return jsonify({"error": "Invalid email format"}), 400

    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "User already exists"}), 400

    user = User(email=email, is_admin=is_admin)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return jsonify({
        "message": "User created successfully",
        "user": {"id": user.id, "email": user.email, "is_admin": user.is_admin}
    }), 201


@admin_bp.route("/admin/users/<int:user_id>", methods=["DELETE"])
@jwt_required()
def delete_user(user_id):
    current_admin = get_current_admin()
    if not current_admin or not current_admin.is_admin:
        return jsonify({"error": "Admin access required"}), 403

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    if user.id == current_admin.id:
        return jsonify({"error": "You cannot delete your own admin account"}), 400

    db.session.delete(user)
    db.session.commit()

    return jsonify({"message": "User deleted successfully"})


@admin_bp.route("/admin/semesters", methods=["GET"])
@jwt_required()
def list_semesters():
    current_admin = get_current_admin()
    if not current_admin or not current_admin.is_admin:
        return jsonify({"error": "Admin access required"}), 403

    semesters = Semester.query.order_by(Semester.id.desc()).all()
    return jsonify([
        {"id": s.id, "name": s.name, "user_id": s.user_id}
        for s in semesters
    ])


@admin_bp.route("/admin/courses", methods=["GET"])
@jwt_required()
def list_courses():
    current_admin = get_current_admin()
    if not current_admin or not current_admin.is_admin:
        return jsonify({"error": "Admin access required"}), 403

    courses = Course.query.order_by(Course.id.desc()).all()
    return jsonify([
        {
            "id": c.id,
            "course_code": c.course_code,
            "unit": c.unit,
            "difficulty": c.difficulty,
            "semester_id": c.semester_id,
        }
        for c in courses
    ])


@admin_bp.route("/admin/courses", methods=["POST"])
@jwt_required()
def add_course():
    current_admin = get_current_admin()
    if not current_admin or not current_admin.is_admin:
        return jsonify({"error": "Admin access required"}), 403

    data = request.get_json(silent=True) or {}
    semester_id = data.get("semester_id")
    course_code = (data.get("course_code") or "").strip()
    unit = data.get("unit")
    difficulty = data.get("difficulty")

    if not semester_id:
        return jsonify({"error": "semester_id is required"}), 400

    semester = Semester.query.get(semester_id)
    if not semester:
        return jsonify({"error": "Semester not found"}), 404

    course = Course(
        semester_id=semester_id,
        course_code=course_code or "GEN",
        unit=unit,
        difficulty=difficulty,
    )
    db.session.add(course)
    db.session.commit()

    return jsonify({"message": "Course added successfully", "course": {"id": course.id, "course_code": course.course_code}}), 201


@admin_bp.route("/admin/students", methods=["GET"])
@jwt_required()
def list_students_data():
    current_admin = get_current_admin()
    if not current_admin or not current_admin.is_admin:
        return jsonify({"error": "Admin access required"}), 403

    profiles = (
        db.session.query(StudentProfile, User)
        .join(User, StudentProfile.user_id == User.id)
        .all()
    )

    result = []
    for profile, user in profiles:
        result.append(
            {
                "student_id": profile.id,
                "email": user.email,
                "username": profile.username,
                "student_id_code": profile.student_id_code,
                "department": profile.department,
                "level": profile.level,
                "created_at": profile.created_at.isoformat() if profile.created_at else None,
            }
        )

    return jsonify(result)
