from flask import Flask
from config import Config
from extensions import db, mail, migrate
from auth.routes import auth

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)

    app.register_blueprint(auth)


    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)