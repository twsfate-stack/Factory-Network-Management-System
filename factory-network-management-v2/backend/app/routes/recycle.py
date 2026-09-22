from flask import Blueprint, jsonify
from ..models import db, Switch
from ..timezone import utcnow
from ..validation import json_body, ValidationError
from .security import begin_write, verify_pin

recycle = Blueprint("recycle", __name__)


def selected_records(body, deleted):
    ids = body.get("switch_ids")
    if not isinstance(ids, list) or not 1 <= len(ids) <= 500 or any(type(value) is not int or value < 1 for value in ids) or len(set(ids)) != len(ids):
        raise ValidationError("Select between 1 and 500 distinct switches.")
    records = db.session.scalars(db.select(Switch).where(Switch.id.in_(ids))).all()
    if len(records) != len(ids) or any(row.is_deleted != deleted for row in records):
        raise ValidationError("One or more selected switches are unavailable or have changed. Refresh and try again.")
    return records


@recycle.post("/switches/delete")
def delete_switches():
    body = json_body()
    begin_write()
    verify_pin(body)
    records = selected_records(body, False)
    db.session.execute(db.update(Switch).where(Switch.id.in_([row.id for row in records])).values(is_deleted=True, deleted_at=utcnow(), updated_at=Switch.updated_at))
    db.session.commit()
    return jsonify(success=True, deleted_count=len(records))


@recycle.post("/switches/restore")
def restore_switches():
    body = json_body()
    begin_write()
    records = selected_records(body, True)
    restoring_ids = [row.id for row in records]
    candidates = db.session.scalars(db.select(Switch).where(db.or_(Switch.is_deleted.is_(False), Switch.id.in_(restoring_ids)))).all()
    # Existing global unique constraints reserve serial/asset even while deleted.
    # Check the full restore batch as well as active rows before changing anything.
    for row in records:
        for key, label in (("hostname", "Hostname"), ("serial_number", "Serial Number"), ("asset_id", "Asset ID")):
            value = getattr(row, key)
            if value and any(other.id != row.id and (getattr(other, key) or "").casefold() == value.casefold() for other in candidates):
                raise ValidationError(f"Cannot restore {row.hostname} because {label} {value} is already in use.")
    db.session.execute(db.update(Switch).where(Switch.id.in_(restoring_ids)).values(is_deleted=False, deleted_at=None, updated_at=Switch.updated_at))
    db.session.commit()
    return jsonify(success=True, restored_count=len(records))
