from flask import Blueprint, request, jsonify
from models import db, User
from utils.validators import is_valid_email
from utils.tokens import generate_reset_token, verify_reset_token

auth_bp = Blueprint("auth", __name__)


# =========================
# REGISTER
# =========================
@auth_bp.route("/register", methods=["POST"])
def register():

    data = request.json
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    if not is_valid_email(email):
        return jsonify({"error": "Invalid email format"}), 400

    if len(password) < 6:
        return jsonify({"error": "Password too short"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "User already exists"}), 400

    user = User(email=email)
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "User registered successfully"})


# =========================
# LOGIN
# =========================
@auth_bp.route("/login", methods=["POST"])
def login():

    data = request.json
    email = data.get("email")
    password = data.get("password")

    user = User.query.filter_by(email=email).first()

    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid credentials"}), 401

    return jsonify({
        "message": "Login successful",
        "email": user.email
    })


# =========================
# FORGOT PASSWORD
# =========================
@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():

    email = request.json.get("email")

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    token = generate_reset_token(email)

    reset_link = f"http://localhost:5000/reset-password/{token}"

    return jsonify({
        "message": "Reset link generated",
        "reset_link": reset_link  # remove in production
    })


# =========================
# RESET PASSWORD
# =========================
@auth_bp.route("/reset-password/<token>", methods=["POST"])
def reset_password(token):

    email = verify_reset_token(token)

    if not email:
        return jsonify({"error": "Invalid or expired token"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    new_password = request.json.get("password")

    if not new_password or len(new_password) < 6:
        return jsonify({"error": "Password too short"}), 400

    user.set_password(new_password)
    db.session.commit()

    return jsonify({"message": "Password reset successful"})