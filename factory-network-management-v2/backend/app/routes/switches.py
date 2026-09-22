from ipaddress import ip_address
from flask import Blueprint, jsonify, request
from sqlalchemy import or_, text, func
from ..models import db, Switch, ProductionLine, SwitchCatalog
from ..validation import json_body, text_field, commit_record, ValidationError


switches = Blueprint("switches", __name__)
from ..switch_creation import STATUSES, selected_catalog, validate_switch_creation


@switches.patch("/switches/<int:switch_id>")
def edit_switch(switch_id):
    body = json_body()
    db.session.execute(text("BEGIN IMMEDIATE"))
    switch = db.session.get(Switch, switch_id)
    if switch is None:
        db.session.rollback()
        return jsonify(success=False, message="Switch not found."), 404
    if switch.is_deleted:
        raise ValidationError("Restore this switch before editing it.")
    if any(key in body for key in ("production_line_id", "block")):
        raise ValidationError("Use Move Switch to change Production Line or Block.")
    for key, label, required, maximum in [
        ("hostname", "Hostname", True, 150), ("serial_number", "Serial number", False, 150),
        ("asset_id", "Asset ID", False, 150), ("ip_address", "IP address", False, 45),
        ("mac_address", "MAC address", False, 50), ("firmware_version", "Firmware", False, 150),
        ("notes", "Notes", False, 4000)]:
        if key in body:
            value = text_field(body, key, label, required, maximum)
            if key == "ip_address" and value:
                try:
                    value = str(ip_address(value))
                except ValueError:
                    raise ValidationError("Enter a valid IPv4 or IPv6 address.") from None
            setattr(switch, key, value)
    if "catalog_id" in body:
        switch.catalog = selected_catalog(body["catalog_id"])
    if "status" in body:
        if not isinstance(body["status"], str) or body["status"] not in STATUSES:
            raise ValidationError("Status must be ACTIVE, OFFLINE or SPARE.")
        switch.status = body["status"]
    commit_record(switch)
    return jsonify(success=True, data=switch.to_dict())


@switches.post("/switches")
def create_switch():
    body = json_body()
    db.session.execute(text("BEGIN IMMEDIATE"))
    switch = Switch(**validate_switch_creation(body))
    commit_record(switch)
    return jsonify(success=True, data=switch.to_dict()), 201


@switches.get("/switches")
def get_switches():
    deleted = request.args.get("deleted", "false")
    if deleted not in ("true", "false"):
        raise ValidationError("Deleted filter must be true or false.")
    query = db.select(Switch).outerjoin(Switch.catalog).where(Switch.is_deleted.is_(deleted == "true"))
    line = request.args.get("production_line", "").strip()
    if line:
        if not line.isdecimal():
            raise ValidationError("Production Line filter must be an ID.")
        query = query.where(Switch.production_line_id == int(line))
    status = request.args.get("status", "")
    if status:
        if status not in STATUSES:
            raise ValidationError("Status must be ACTIVE, OFFLINE or SPARE.")
        query = query.where(Switch.status == status)
    vendor = request.args.get("vendor", "").strip()
    if vendor:
        query = query.where(func.coalesce(SwitchCatalog.vendor, Switch.vendor) == vendor)
    search = request.args.get("search", "").strip()
    if search:
        query = query.join(Switch.production_line).where(or_(*(column.icontains(search, autoescape=True) for column in (Switch.hostname, Switch.serial_number, Switch.asset_id, func.coalesce(SwitchCatalog.vendor, Switch.vendor), func.coalesce(SwitchCatalog.model, Switch.model), SwitchCatalog.name, Switch.ip_address, Switch.block, ProductionLine.name))))
    return jsonify([switch.to_dict() for switch in db.session.scalars(query.order_by(Switch.id)).all()])


@switches.get("/switches/<int:switch_id>")
def get_switch(switch_id):
    switch = db.session.get(Switch, switch_id)
    if switch is None:
        return jsonify(success=False, message="Switch not found."), 404
    return jsonify(switch.to_dict())


@switches.patch("/switches/<int:switch_id>/status")
def update_switch_status(switch_id):
    body = json_body()
    status = body.get("status")
    if not isinstance(status, str) or status not in STATUSES:
        raise ValidationError("Status must be ACTIVE, OFFLINE or SPARE.")
    # Serialize with soft delete so a deleted record cannot be modified by a racing request.
    db.session.execute(text("BEGIN IMMEDIATE"))
    switch = db.session.get(Switch, switch_id)
    if switch is None:
        db.session.rollback()
        return jsonify(success=False, message="Switch not found."), 404
    if switch.is_deleted:
        raise ValidationError("Restore this switch before changing its status.")
    if switch.status != status:
        switch.status = status
    db.session.commit()
    return jsonify(success=True, data=switch.to_dict())
