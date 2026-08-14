import os

class Config:
    SECRET_KEY = 'a_super_secure_long_secret_key_for_eduportal_2026_!@#$%^&*()_+abcdefghijklmnopqrstuvwxyz'
    JWT_SECRET_KEY = 'a_super_secure_long_jwt_secret_key_for_eduportal_2026_!@#$%^&*()_+abcdefghijklmnopqrstuvwxyz'

    SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://postgres:wunnykel@localhost/study_performance_db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'oparakelechi27@gmail.com'
    MAIL_PASSWORD = 'WunnyKel00##'