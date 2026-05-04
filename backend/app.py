from flask import Flask, render_template
from config import Config

from extensions import db, mail, migrate
from routes.survey import survey_bp
from routes.auth import auth_bp
from flask_jwt_extended import JWTManager

from ml.retrain import retrain_model


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # =========================
    # JWT CONFIG
    # =========================
    app.config["JWT_SECRET_KEY"] = "futocsc"

    # =========================
    # INIT EXTENSIONS
    # =========================
    db.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    jwt = JWTManager(app)

    # =========================
    # REGISTER BLUEPRINTS
    # =========================
    app.register_blueprint(survey_bp)
    app.register_blueprint(auth_bp)

    # =========================
    # ROUTES
    # =========================
    @app.route("/")
    def home():
        return render_template("upload.html")

    @app.route("/dashboard")
    def dashboard():
        return render_template("dashboard.html")

    # ✅ SAFE MODEL TRAIN (ONLY WHEN CALLED)
    @app.route("/init-model")
    def init_model():
        result = retrain_model()
        return result if isinstance(result, dict) else {"message": "done"}



    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)