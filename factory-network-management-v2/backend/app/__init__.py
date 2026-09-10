import os
import sqlite3
from pathlib import Path
from flask import Flask, jsonify
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from .routes.health import health
from .models import db
from .validation import ValidationError


@event.listens_for(Engine, "connect")
def configure_sqlite(connection, _):
    if isinstance(connection, sqlite3.Connection):
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA busy_timeout=5000")


def create_app(test_config=None):
    app = Flask(__name__)
    database_path = Path(os.environ.get("FACTORY_DATABASE_PATH", Path(__file__).resolve().parents[1] / "data" / "factory_network.db")).resolve()
    app.config.update(SQLALCHEMY_DATABASE_URI=f"sqlite:///{database_path.as_posix()}", SQLALCHEMY_TRACK_MODIFICATIONS=False, MAX_CONTENT_LENGTH=64 * 1024)
    if test_config:
        app.config.update(test_config)
    if not test_config or "SQLALCHEMY_DATABASE_URI" not in test_config:
        database_path.parent.mkdir(parents=True, exist_ok=True)
    db.init_app(app)
    from .routes.production_lines import production_lines
    from .routes.switches import switches
    from .routes.dashboard import dashboard
    app.register_blueprint(health, url_prefix="/api")
    for blueprint in (production_lines, switches, dashboard):
        app.register_blueprint(blueprint, url_prefix="/api")

    @app.errorhandler(ValidationError)
    def invalid(error):
        return jsonify(success=False, message=str(error)), 400

    @app.errorhandler(SQLAlchemyError)
    def database_error(error):
        db.session.rollback()
        app.logger.exception("Database operation failed")
        return jsonify(success=False, message="Unable to save or load data. Please try again."), 503

    @app.errorhandler(413)
    def too_large(error):
        return jsonify(success=False, message="The submitted form is too large."), 413

    with app.app_context():
        db.create_all()
    return app
