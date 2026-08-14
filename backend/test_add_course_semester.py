import unittest
from app import create_app
from extensions import db
from models import User, Semester, Course, StudyHabit
from flask_jwt_extended import create_access_token


class AddCourseSemesterTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config.update(
            TESTING=True,
            SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
            JWT_SECRET_KEY='test-secret-key-for-courses',
        )
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.drop_all()
        db.create_all()
        self.user = User(email='semester@example.com')
        self.user.set_password('secret')
        db.session.add(self.user)
        db.session.commit()
        self.semester = Semester(user_id=self.user.id, name='First Semester 2024')
        db.session.add(self.semester)
        db.session.commit()
        self.token = create_access_token(identity=self.user.email)
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_existing_semester_with_optional_study_fields(self):
        response = self.client.post(
            '/add-course',
            json={
                'course_code': 'CSC101',
                'course_name': 'Intro to Programming',
                'unit': 3,
                'difficulty': 2,
                'semester_id': self.semester.id,
                'semester_name': None,
                'study_hours': 4.5,
                'study_method': 'Active',
            },
            headers={'Authorization': f'Bearer {self.token}'}
        )

        self.assertEqual(response.status_code, 201)
        payload = response.get_json()
        self.assertEqual(payload['course']['code'], 'CSC101')

        course = Course.query.filter_by(semester_id=self.semester.id, course_code='CSC101').first()
        self.assertIsNotNone(course)

        habit = StudyHabit.query.filter_by(course_id=course.id).first()
        self.assertIsNotNone(habit)
        self.assertEqual(habit.study_hours, 4.5)
        self.assertEqual(habit.study_method, 'Active')

    def test_dashboard_data_works_without_performance_record(self):
        course = Course(semester_id=self.semester.id, course_code='CSC202', unit=3, difficulty=2)
        db.session.add(course)
        db.session.flush()

        habit = StudyHabit(course_id=course.id, study_hours=5.0, study_method='Active', focus_score=None)
        db.session.add(habit)
        db.session.commit()

        response = self.client.get(
            '/user/semester@example.com/insights',
            headers={'Authorization': f'Bearer {self.token}'}
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload['total_courses'], 1)

        response = self.client.get(
            '/ml-recommend/semester@example.com',
            headers={'Authorization': f'Bearer {self.token}'}
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertGreaterEqual(len(payload['results']), 1)


if __name__ == '__main__':
    unittest.main()
