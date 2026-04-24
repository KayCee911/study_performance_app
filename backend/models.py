from extensions import db
from datetime import datetime


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)

    profile = db.relationship("StudentProfile", backref="user", uselist=False, cascade="all, delete")
    semesters = db.relationship("Semester", backref="user", cascade="all, delete")


class StudentProfile(db.Model):
    __tablename__ = "student_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # 👇 ADD THIS (CRITICAL for survey linkage)
    username = db.Column(db.String(255), nullable=True)

    student_id_code = db.Column(db.String(50), unique=True)
    department = db.Column(db.String(100))
    level = db.Column(db.Integer)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Semester(db.Model):
    __tablename__ = "semesters"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    name = db.Column(db.String(50), nullable=False)

    courses = db.relationship("Course", backref="semester", cascade="all, delete")


class Course(db.Model):
    __tablename__ = "courses"

    id = db.Column(db.Integer, primary_key=True)
    semester_id = db.Column(db.Integer, db.ForeignKey("semesters.id"), nullable=False)

    # 👇 MATCHES YOUR CSV
    course_code = db.Column(db.String(50), nullable=True)

    # (optional for later ML)
    unit = db.Column(db.Float, nullable=True)
    difficulty = db.Column(db.Integer, nullable=True)

    study_habits = db.relationship("StudyHabit", backref="course", cascade="all, delete")
    performance = db.relationship("Performance", backref="course", uselist=False, cascade="all, delete")


class StudyHabit(db.Model):
    __tablename__ = "study_habits"

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)

    study_hours = db.Column(db.Float)
    study_method = db.Column(db.String(50))
    focus_score = db.Column(db.Float)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Performance(db.Model):
    __tablename__ = "performances"

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)

    grade = db.Column(db.String(2))

    # 👇 IMPORTANT: this is actually "points" from your CSV
    gpa = db.Column(db.Float)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)