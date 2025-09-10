from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from .models import db, User
from .auth import auth_bp, init_login
from .routes import main_bp
import click


def create_app():
    app = Flask(__name__, instance_relative_config=False)

    # Load config
    app.config.from_object("config.DevConfig")

    # Extensions
    db.init_app(app)
    init_login(app)

    # Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    # CLI commands
    register_cli(app)

    with app.app_context():
        db.create_all()

    return app


def register_cli(app: Flask):
    @app.cli.command("init-db")
    def init_db():
        """Initialize database tables."""
        from .models import db  # local import to ensure app context
        db.drop_all()
        db.create_all()
        click.echo("Database initialized.")

    @app.cli.command("create-admin")
    @click.option("--username", required=True, help="Admin username")
    @click.option("--password", required=True, help="Admin password")
    @click.option("--role", default="admin", help="Role: admin/doctor/nurse/clerk")
    def create_admin(username, password, role):
        """Create an admin (or specified role) user."""
        from .models import User, db
        if User.query.filter_by(username=username).first():
            click.echo("User already exists.")
            return
        user = User(username=username, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo(f"User '{username}' created with role '{role}'.")

