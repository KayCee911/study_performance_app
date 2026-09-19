import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
os.makedirs(INSTANCE_DIR, exist_ok=True)

class Config:
    SECRET_KEY = 'a_super_secure_long_secret_key_for_eduportal_2026_!@#$%^&*()_+abcdefghijklmnopqrstuvwxyz'
    JWT_SECRET_KEY = 'a_super_secure_long_jwt_secret_key_for_eduportal_2026_!@#$%^&*()_+abcdefghijklmnopqrstuvwxyz'

    DATABASE_URL = os.getenv("DATABASE_URL")
    DEFAULT_SQLITE_DB = os.path.join(INSTANCE_DIR, "study_performance.db")
    SQLALCHEMY_DATABASE_URI = DATABASE_URL or f"sqlite:///{DEFAULT_SQLITE_DB}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    if SQLALCHEMY_DATABASE_URI.startswith("sqlite"):
        SQLALCHEMY_ENGINE_OPTIONS = {"connect_args": {"check_same_thread": False}}

    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'oparakelechi27@gmail.com'
    MAIL_PASSWORD = 'kelechi'