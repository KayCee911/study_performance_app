import os

from app import create_app
from extensions import db
from models import User

app = create_app()

DEFAULT_ADMIN_EMAIL = "admin@local.test"
DEFAULT_ADMIN_PASSWORD = "Secret123"

admin_email = (os.getenv("ADMIN_EMAIL") or DEFAULT_ADMIN_EMAIL).strip().lower()
admin_password = os.getenv("ADMIN_PASSWORD") or DEFAULT_ADMIN_PASSWORD

with app.app_context():
    db.create_all()

    admin = User.query.filter_by(email=admin_email).first()
    if not admin:
        admin = User(email=admin_email, is_admin=True)
        admin.set_password(admin_password)
        db.session.add(admin)
    else:
        admin.is_admin = True
        admin.set_password(admin_password)

    db.session.commit()
    print(f"Admin ready: email={admin.email}")
