from flask import Blueprint, request, jsonify
from data_processing.transform_survey import transform_survey_data
from models import db, Student, Course

survey_bp = Blueprint("survey", __name__)

@survey_bp.route("/upload-survey", methods=["POST"])
def upload_survey():

    file = request.files["file"]
    file_path = "temp.csv"
    file.save(file_path)

    df = transform_survey_data(file_path)

    for username, group in df.groupby("Username"):

        student = Student(username=username)
        db.session.add(student)
        db.session.flush()

        for _, row in group.iterrows():

            course = Course(
                student_id=student.id,
                course_no=row["course_no"],
                course_code=row["course_code"],
                difficulty=row["difficulty"],
                grade=row["grade"],
                points=row["points"]
            )

            db.session.add(course)

    db.session.commit()

    return jsonify({
        "message": "Upload successful",
        "students": len(df["Username"].unique())
    })