from app import create_app
from extensions import db
from models import User

app = create_app()

with app.app_context():
    # create tables if missing (safe in dev)
    db.create_all()

    admin = User.query.filter_by(email='admin@example.com').first()
    if not admin:
        admin = User(email='admin@example.com', is_admin=True)
        admin.set_password('adminpass')
        db.session.add(admin)
        db.session.commit()

    print('Admin ready: email=admin@example.com password=adminpass')
