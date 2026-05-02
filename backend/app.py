from flask import Flask, render_template
from config import Config

from extensions import db, mail, migrate
from routes.survey import survey_bp
from routes.auth import auth_bp
from ml.retrain import retrain_model





def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # INIT EXTENSIONS
    db.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)   # ✅ ONLY THIS

    # REGISTER BLUEPRINTS
    app.register_blueprint(survey_bp)
    app.register_blueprint(auth_bp)

    @app.route("/")
    def home():
        return render_template("upload.html")

    @app.route("/dashboard")
    def dashboard():
        return render_template("dashboard.html")
    
   

    with app.app_context():
        retrain_model()

    return app

    


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)