from flask import Blueprint, jsonify
from sqlalchemy import text
from ..models import db, Switch, ProductionLine, SwitchMoveHistory
from ..timezone import utcnow, iso_thailand
from ..validation import json_body, text_field, ValidationError

moves = Blueprint("moves", __name__)


@moves.post("/switches/<int:switch_id>/move")
def move_switch(switch_id):
    body = json_body()
    hostname = text_field(body, "hostname", "Hostname", True, 150)
    block = text_field(body, "block", "Block", maximum=100)
    notes = text_field(body, "notes", "Move note", maximum=4000)
    line_id = body.get("production_line_id")
    if type(line_id) is not int:
        raise ValidationError("Select an existing Production Line.")
    # Serialize moves with delete/status operations; history and relocation commit together.
    db.session.execute(text("BEGIN IMMEDIATE"))
    switch = db.session.get(Switch, switch_id)
    if switch is None:
        db.session.rollback()
        return jsonify(success=False, message="Switch not found."), 404
    if switch.is_deleted:
        raise ValidationError("Restore this switch before moving it.")
    destination = db.session.get(ProductionLine, line_id)
    if destination is None:
        raise ValidationError("Select an existing Production Line.")
    if "expected_updated_at" in body and body["expected_updated_at"] != iso_thailand(switch.updated_at):
        raise ValidationError("This switch has changed. Close Move and reopen it to review the current location.")
    if (switch.production_line_id, switch.block, switch.hostname) == (line_id, block, hostname):
        raise ValidationError("No changes to move.")
    now = utcnow()
    history = SwitchMoveHistory(switch_id=switch.id,
        from_production_line_id=switch.production_line_id, from_production_line_name=switch.production_line.name,
        to_production_line_id=destination.id, to_production_line_name=destination.name,
        from_block=switch.block, to_block=block, from_hostname=switch.hostname, to_hostname=hostname,
        moved_at=now, notes=notes)
    switch.production_line = destination
    switch.block = block
    switch.hostname = hostname
    switch.updated_at = now
    db.session.add(history)
    db.session.commit()
    return jsonify(success=True, message="Switch moved successfully.", data=switch.to_dict())


@moves.get("/switches/<int:switch_id>/moves")
def get_switch_moves(switch_id):
    if db.session.get(Switch, switch_id) is None:
        return jsonify(success=False, message="Switch not found."), 404
    query = db.select(SwitchMoveHistory).where(SwitchMoveHistory.switch_id == switch_id).order_by(SwitchMoveHistory.id)
    return jsonify([entry.to_dict() for entry in db.session.scalars(query)])
