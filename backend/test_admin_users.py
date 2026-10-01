import unittest

from app import create_app
from extensions import db
from models import User


class AdminUsersTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config.update(
            TESTING=True,
            SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
        )
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.drop_all()
        db.create_all()

        self.admin = User(email='owner@example.com', is_admin=True)
        self.admin.set_password('secret123')
        db.session.add(self.admin)
        db.session.commit()

        self.client = self.app.test_client()
        self.client.post(
            '/login',
            json={'email': 'owner@example.com', 'password': 'secret123'},
        )

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_admin_can_create_admin_who_can_access_admin_routes(self):
        response = self.client.post(
            '/admin/users',
            json={
                'email': 'new-admin@university.edu',
                'password': 'secret123',
                'is_admin': True,
            },
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.get_json()['user']['is_admin'])

        created_admin = User.query.filter_by(email='new-admin@university.edu').first()
        self.assertIsNotNone(created_admin)
        self.assertTrue(created_admin.is_admin)
        self.assertTrue(created_admin.check_password('secret123'))

        self.client.post(
            '/logout',
            json={},
        )
        login_response = self.client.post(
            '/login',
            json={'email': 'new-admin@university.edu', 'password': 'secret123'},
        )
        self.assertEqual(login_response.status_code, 200, login_response.get_json())
        self.assertTrue(login_response.get_json()['is_admin'])
        self.assertEqual(self.client.get('/admin/users').status_code, 200)

    def test_admin_role_must_be_a_boolean(self):
        response = self.client.post(
            '/admin/users',
            json={
                'email': 'invalid-role@university.edu',
                'password': 'secret123',
                'is_admin': 'true',
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIsNone(User.query.filter_by(email='invalid-role@university.edu').first())


if __name__ == '__main__':
    unittest.main()