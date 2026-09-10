from ipaddress import ip_address
from flask import Blueprint, jsonify, request
from sqlalchemy import or_
from ..models import db, Switch, ProductionLine
from ..validation import json_body, text_field, commit_record, ValidationError

switches = Blueprint("switches", __name__)
STATUSES = {"ACTIVE", "OFFLINE", "SPARE"}


@switches.post("/switches")
def create_switch():
    body = json_body()
    values = {key: text_field(body, key, label, required, maximum) for key, label, required, maximum in [
        ("hostname", "Hostname", True, 150), ("vendor", "Vendor", True, 100), ("model", "Model", True, 150),
        ("asset_id", "Asset ID", False, 150), ("serial_number", "Serial number", False, 150),
        ("ip_address", "IP address", False, 45), ("mac_address", "MAC address", False, 50),
        ("firmware_version", "Firmware", False, 150), ("notes", "Notes", False, 4000)]}
    status = body.get("status")
    if not isinstance(status, str) or status not in STATUSES:
        raise ValidationError("Status must be ACTIVE, OFFLINE or SPARE.")
    line_id = body.get("production_line_id")
    if type(line_id) is not int or db.session.get(ProductionLine, line_id) is None:
        raise ValidationError("Select an existing Production Line.")
    if values["ip_address"]:
        try:
            values["ip_address"] = str(ip_address(values["ip_address"]))
        except ValueError:
            raise ValidationError("Enter a valid IPv4 or IPv6 address.") from None
    switch = Switch(**values, status=status, production_line_id=line_id)
    commit_record(switch)
    return jsonify(success=True, data=switch.to_dict()), 201


@switches.get("/switches")
def get_switches():
    query = db.select(Switch)
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
        query = query.where(Switch.vendor == vendor)
    search = request.args.get("search", "").strip()
    if search:
        query = query.where(or_(*(column.icontains(search, autoescape=True) for column in (Switch.hostname, Switch.asset_id, Switch.model))))
    return jsonify([switch.to_dict() for switch in db.session.scalars(query.order_by(Switch.id)).all()])
