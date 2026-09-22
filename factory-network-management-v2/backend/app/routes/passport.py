from io import BytesIO
from urllib.parse import urlsplit
from uuid import UUID
import segno
from flask import Blueprint, current_app, jsonify, send_file, request
from ..models import db, Switch, SwitchMoveHistory

passport = Blueprint("passport", __name__)


def validate_public_base_url(value):
    value = (value or "").strip().rstrip("/")
    if not value:
        return ""
    parsed = urlsplit(value)
    if (parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password
            or parsed.query or parsed.fragment or parsed.path or len(value) > 500
            or any(character.isspace() for character in value)):
        raise ValueError("PUBLIC_BASE_URL must be an HTTP(S) origin, without credentials, a path, query or fragment.")
    parsed.port  # Validate the optional port number.
    return value


def find_passport(uid):
    try:
        canonical = str(UUID(uid))
    except (ValueError, AttributeError):
        return None
    return db.session.scalar(db.select(Switch).where(Switch.passport_uid == canonical))


def passport_url(record):
    base = current_app.config["PUBLIC_BASE_URL"]
    return f"{base}/passport/{record.passport_uid}" if base else None


@passport.get("/passport/<uid>")
def get_passport(uid):
    record = find_passport(uid)
    if record is None:
        return jsonify(success=False, message="Switch Passport not found."), 404
    query = db.select(SwitchMoveHistory).where(SwitchMoveHistory.switch_id == record.id).order_by(SwitchMoveHistory.moved_at.desc(), SwitchMoveHistory.id.desc()).limit(11)
    entries = db.session.scalars(query).all()
    fields = ("catalog_image_url", "catalog_name", "hostname", "serial_number", "asset_id", "vendor", "model", "firmware_version", "ip_address",
              "mac_address", "status", "production_line", "block", "notes", "created_at", "updated_at", "is_deleted", "deleted_at")
    values = record.to_dict()
    history_fields = ("from_production_line_name", "to_production_line_name", "from_block", "to_block", "from_hostname", "to_hostname", "moved_at", "notes")
    history = [{key: entry.to_dict()[key] for key in history_fields} for entry in entries[:10]]
    response = jsonify(passport_uid=record.passport_uid, switch={key: values[key] for key in fields},
                       history=history, has_more_history=len(entries) > 10, passport_url=passport_url(record))
    response.headers["Cache-Control"] = "no-store"
    return response


@passport.get("/passport/<uid>/qr.png")
def get_passport_qr(uid):
    record = find_passport(uid)
    if record is None:
        return jsonify(success=False, message="Switch Passport not found."), 404
    url = passport_url(record)
    if not url:
        return jsonify(success=False, message="QR printing is unavailable until PUBLIC_BASE_URL is configured."), 503
    image = BytesIO()
    segno.make_qr(url, error="m").save(image, kind="png", scale=8, border=4)
    image.seek(0)
    response = send_file(image, mimetype="image/png", download_name=f"FNMS_{record.passport_uid}_QR.png", as_attachment=request.args.get("download") == "1", max_age=0)
    response.headers["Cache-Control"] = "no-store"
    return response
