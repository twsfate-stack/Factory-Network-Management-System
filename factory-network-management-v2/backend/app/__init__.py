import os
import sqlite3
from pathlib import Path
from flask import Flask, jsonify, request
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from .routes.health import health
from .models import db
from .validation import ValidationError
from .schema import upgrade_schema


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
    from .routes.passport import passport, validate_public_base_url
    from .routes.frontend import frontend
    app.config["PUBLIC_BASE_URL"] = validate_public_base_url(app.config.get("PUBLIC_BASE_URL", os.environ.get("PUBLIC_BASE_URL", "")))
    db.init_app(app)
    from .routes.production_lines import production_lines
    from .routes.switches import switches
    from .routes.dashboard import dashboard
    from .routes.security import security
    from .routes.recycle import recycle
    from .routes.moves import moves
    from .routes.catalog import catalog
    from .routes.inventory_transfer import inventory_transfer
    app.register_blueprint(health, url_prefix="/api")
    for blueprint in (production_lines, switches, dashboard, security, recycle, moves, passport, catalog, inventory_transfer):
        app.register_blueprint(blueprint, url_prefix="/api")

    from .catalog_images import media
    app.register_blueprint(media, url_prefix="/api")
    app.register_blueprint(frontend)

    @app.before_request
    def upload_limits():
        if request.endpoint in ("inventory_transfer.preview_import", "inventory_transfer.confirm_import"):
            request.max_content_length = 6 * 1024 * 1024
            request.max_form_parts = 3
        if request.endpoint in ("catalog.create_catalog", "catalog.edit_catalog") and request.mimetype == "multipart/form-data":
            request.max_content_length = 6 * 1024 * 1024
            request.max_form_parts = 12


    @app.errorhandler(ValidationError)
    def invalid(error):
        db.session.rollback()
        return jsonify(success=False, message=str(error)), 400

    @app.errorhandler(SQLAlchemyError)
    def database_error(error):
        db.session.rollback()
        app.logger.exception("Database operation failed")
        return jsonify(success=False, message="Unable to save or load data. Please try again."), 503

    @app.errorhandler(413)
    def too_large(error):
        return jsonify(success=False, message="Upload must be 5 MB or smaller; form fields must also fit the upload limit."), 413

    with app.app_context():
        default_images = Path(db.engine.url.database).resolve().parent / "uploads" / "switch-catalog" if db.engine.url.database != ":memory:" else Path(app.instance_path) / "uploads" / "switch-catalog"
        app.config["CATALOG_IMAGE_DIR"] = Path(app.config.get("CATALOG_IMAGE_DIR") or os.environ.get("CATALOG_IMAGE_DIR") or default_images).resolve()
        db.create_all()
        upgrade_schema(db.engine)
    return app
