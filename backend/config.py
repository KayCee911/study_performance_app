import os

class Config:
    SECRET_KEY = 'futocsc'

    SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://postgres:wunnykel@localhost/study_performance_db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'oparakelechi27@gmail.com'
    MAIL_PASSWORD = 'WunnyKel00##'