from flask import Blueprint, request, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash


from models import db, User
from utils.token import generate_token, confirm_token
from utils.email import send_email 

auth = Blueprint('auth', __name__)



#register route

@auth.route('/register', methods=['POST'])
def register():
    email = request.form['email']
    password = generate_password_hash(request.form['password'])

    user = User(email=email, password=password)
    db.session.add(user)
    db.session.commit()

    token = generate_token(email)
    link = url_for('auth.verify_email', token=token, _external=True)

    send_email(email, 'Verify Your Email', f'Click here: {link}')

    return "Check your email to verify your account"



#email verification route

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


#login route

from werkzeug.security import check_password_hash

@auth.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']

    user = User.query.filter_by(email=email).first()

    if not user:
        return "User not found"

    if not user.is_verified:
        return "Please verify your email first"

    if check_password_hash(user.password, password):
        return "Login successful"

    return "Incorrect password"



#forgot tpassword route

@auth.route('/forgot-password', methods=['POST'])
def forgot_password():
    email = request.form['email']
    user = User.query.filter_by(email=email).first()

    if user:
        token = generate_token(email)
        link = url_for('auth.reset_password', token=token, _external=True)

        send_email(email, 'Reset Password', f'Click here: {link}')

    return "If email exists, reset link sent"



#reset password route

@auth.route('/reset/<token>', methods=['POST'])
def reset_password(token):
    try:
        email = confirm_token(token)
    except:
        return "Invalid or expired token"

    user = User.query.filter_by(email=email).first()

    if user:
        new_password = generate_password_hash(request.form['password'])
        user.password = new_password
        db.session.commit()

    return "Password updated"