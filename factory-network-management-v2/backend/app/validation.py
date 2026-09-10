from flask import request
from sqlalchemy.exc import IntegrityError
from .models import db


class ValidationError(ValueError):
    pass


def json_body():
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        raise ValidationError("Send a JSON object with the required fields.")
    return body


def text_field(body, key, label, required=False, maximum=150):
    value = body.get(key)
    if value is None:
        value = ""
    if not isinstance(value, str):
        raise ValidationError(f"{label} must be text.")
    value = value.strip()
    if required and not value:
        raise ValidationError(f"{label} cannot be empty.")
    if len(value) > maximum:
        raise ValidationError(f"{label} must be {maximum} characters or fewer.")
    return value or None


def commit_record(record):
    db.session.add(record)
    try:
        db.session.commit()
    except IntegrityError as error:
        db.session.rollback()
        # Database constraints also protect against concurrent duplicate submissions.
        detail = str(error.orig).lower()
        for key, label in (("asset_id", "Asset ID"), ("serial_number", "Serial number"), ("ip_address", "IP address"), ("production_lines.name", "Production Line name")):
            if key in detail:
                raise ValidationError(f"{label} already exists.") from None
        raise ValidationError("The record conflicts with existing data. Check the selected Production Line and field values.") from None
