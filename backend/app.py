from flask import Flask, render_template
from config import Config

from extensions import db, mail, migrate, login_manager
from routes.survey import survey_bp
from routes.auth import auth_bp
from routes.admin import admin_bp

from ml.retrain import retrain_model


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize Flask-Login
    login_manager.login_view = 'auth.login_page'
    login_manager.init_app(app)
    
    # User loader for Flask-Login
    from models import User
    @login_manager.user_loader
    def load_user(user_id):
        try:
            return User.query.get(int(user_id))
        except Exception:
            return None

    # =========================
    # INIT EXTENSIONS
    # =========================
    db.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)

    # =========================
    # REGISTER BLUEPRINTS
    # =========================
    app.register_blueprint(survey_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)

    # =========================
    # ROUTES
    # =========================
    @app.route("/")
    def home():
        return render_template("upload.html")

    @app.route("/dashboard")
    def dashboard():
        # Page is public; dashboard data fetched via public endpoints
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