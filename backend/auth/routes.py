from flask import Blueprint, request, jsonify, url_for
from werkzeug.security import generate_password_hash, check_password_hash

from models import db, User
from utils.tokens import generate_token, confirm_token
from backend.utils.validators import send_email 

auth = Blueprint('auth', __name__)


def get_request_data():
    return request.get_json() if request.is_json else request.form


# REGISTER
@auth.route('/register', methods=['POST'])
def register():
    data = request.get_json() if request.is_json else request.form

    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    # CHECK DUPLICATE
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"error": "Email already registered"}), 400

    hashed_password = generate_password_hash(password)

    user = User(email=email, password=hashed_password)
    db.session.add(user)
    db.session.commit()

    #  EMAIL (SAFE)
    token = generate_token(email)
    link = url_for('auth.verify_email', token=token, _external=True)

    try:
        send_email(email, 'Verify Your Email', f'Click here: {link}')
    except Exception as e:
        print("Email failed:", str(e))

    return jsonify({"message": "Registration successful (email may not send in dev)"})




# VERIFY EMAIL
@auth.route('/verify/<token>')
def verify_email(token):
    try:
        email = confirm_token(token)
    except:
        return "Invalid or expired token"

    user = User.query.filter_by(email=email).first()

    if user:
        user.is_verified = True
        db.session.commit()

    return "Email verified successfully!"


# -------------------------
# LOGIN
# -------------------------
@auth.route('/login', methods=['POST'])
def login():
    data = get_request_data()

    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({"error": "User not found"}), 404

    if not user.is_verified:
        return jsonify({"error": "Please verify your email first"}), 403

    if check_password_hash(user.password, password):
        return jsonify({"message": "Login successful"})

    return jsonify({"error": "Incorrect password"}), 401


# -------------------------
# FORGOT PASSWORD
# -------------------------
@auth.route('/forgot-password', methods=['POST'])
def forgot_password():
    data = get_request_data()

    email = data.get('email')

    user = User.query.filter_by(email=email).first()

    if user:
        token = generate_token(email)
        link = url_for('auth.reset_password', token=token, _external=True)

        send_email(email, 'Reset Password', f'Click here: {link}')

    return jsonify({"message": "If email exists, reset link sent"})


# -------------------------
# RESET PASSWORD
# -------------------------
@auth.route('/reset/<token>', methods=['POST'])
def reset_password(token):
    try:
        email = confirm_token(token)
    except:
        return "Invalid or expired token"

    data = get_request_data()
    new_password = data.get('password')

    user = User.query.filter_by(email=email).first()

    if user:
        user.password = generate_password_hash(new_password)
        db.session.commit()

    return jsonify({"message": "Password updated"})