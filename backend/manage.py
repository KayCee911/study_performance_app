from app import create_app
from extensions import db
from flask_migrate import Migrate
from flask.cli import FlaskGroup

app = create_app()
cli = FlaskGroup(app)

if __name__ == "__main__":
    cli()