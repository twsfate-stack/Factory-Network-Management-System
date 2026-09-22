import re
from datetime import timedelta
from flask import Blueprint, jsonify
from sqlalchemy import text
from werkzeug.security import generate_password_hash, check_password_hash
from ..models import db, SecuritySettings
from ..timezone import utcnow
from ..validation import json_body, ValidationError

security = Blueprint("security", __name__)


def begin_write():
    # Serialize PIN changes and destructive requests across SQLite connections.
    db.session.execute(text("BEGIN IMMEDIATE"))


def pin_value(body, key):
    value = body.get(key)
    if not isinstance(value, str) or re.fullmatch(r"[0-9]{6}", value) is None:
        raise ValidationError("PIN must contain exactly 6 digits.")
    return value


def new_pin(body):
    value = pin_value(body, "new_pin")
    if value != pin_value(body, "confirm_pin"):
        raise ValidationError("New PIN and confirmation must match.")
    return value


def verify_pin(body, key="pin", message="Incorrect PIN."):
    settings = db.session.get(SecuritySettings, 1)
    if settings is None:
        raise ValidationError("Delete PIN is not configured. Please set a 6-digit Delete PIN in Settings before deleting switches.")
    now = utcnow().replace(tzinfo=None)
    if settings.locked_until and settings.locked_until > now:
        raise ValidationError("Too many incorrect PIN attempts. Please try again in one minute.")
    value = pin_value(body, key)
    if not check_password_hash(settings.delete_pin_hash, value):
        settings.failed_attempts += 1
        if settings.failed_attempts >= 5:
            settings.failed_attempts = 0
            settings.locked_until = now + timedelta(minutes=1)
        db.session.commit()
        raise ValidationError(message)
    settings.failed_attempts = 0
    settings.locked_until = None
    return settings


@security.get("/settings/delete-pin/status")
def pin_status():
    response = jsonify(pin_configured=db.session.get(SecuritySettings, 1) is not None)
    response.headers["Cache-Control"] = "no-store"
    return response


@security.post("/settings/delete-pin/setup")
def setup_pin():
    body = json_body()
    value = new_pin(body)
    begin_write()
    if db.session.get(SecuritySettings, 1) is not None:
        raise ValidationError("Delete PIN is already configured. Use Change PIN.")
    db.session.add(SecuritySettings(id=1, delete_pin_hash=generate_password_hash(value)))
    db.session.commit()
    return jsonify(success=True, pin_configured=True), 201


@security.post("/settings/delete-pin/change")
def change_pin():
    body = json_body()
    value = new_pin(body)
    begin_write()
    settings = verify_pin(body, "current_pin", "Incorrect current PIN.")
    settings.delete_pin_hash = generate_password_hash(value)
    db.session.commit()
    return jsonify(success=True, message="Delete PIN updated successfully.")
