from app import create_app
from extensions import db
from models import User, Semester
from flask_jwt_extended import create_access_token

app = create_app()
app.config.update(TESTING=True, SQLALCHEMY_DATABASE_URI='sqlite:///:memory:', JWT_SECRET_KEY='test-secret')

with app.app_context():
    db.drop_all()
    db.create_all()
    user = User(email='x@example.com')
    user.set_password('123456')
    db.session.add(user)
    db.session.commit()
    sem = Semester(user_id=user.id, name='First')
    db.session.add(sem)
    db.session.commit()
    token = create_access_token(identity=user.email)
    client = app.test_client()
    resp = client.post('/add-course', json={'course_code':'CSC101','course_name':'Intro','unit':3,'difficulty':2,'semester_id':sem.id,'study_hours':4.5,'study_method':'Active'}, headers={'Authorization': f'Bearer {token}'})
    print('status', resp.status_code)
    print(resp.text)
