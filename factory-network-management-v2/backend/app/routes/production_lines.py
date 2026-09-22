from flask import Blueprint, jsonify
from sqlalchemy import text
from ..models import db, ProductionLine, ProductionLineModel
from ..timezone import iso_thailand
from ..validation import json_body, text_field, commit_record, ValidationError

production_lines = Blueprint("production_lines", __name__)


def get_production_line_summary(line):
    records = [switch for switch in line.switches if not switch.is_deleted]
    statuses = {switch.status for switch in records}
    status = "NO SWITCH" if not records else "WORKING" if "ACTIVE" in statuses else "NOT WORKING"
    combinations = {switch.catalog.name if switch.catalog else f"{switch.vendor} {switch.model}" for switch in records}
    return dict(id=line.id, name=line.name, description=line.description,
                total_switches=len(records), status=status, model_names=[entry.model_name for entry in line.model_entries],
                switch_models=sorted(combinations, key=str.casefold),
                created_at=iso_thailand(line.created_at), updated_at=iso_thailand(line.updated_at))


@production_lines.get("/production-lines")
def get_production_lines():
    lines = db.session.scalars(db.select(ProductionLine).order_by(ProductionLine.name)).all()
    return jsonify([get_production_line_summary(line) for line in lines])


@production_lines.post("/production-lines")
def create_production_line():
    body = json_body()
    line = ProductionLine(name=text_field(body, "name", "Production Line name", True, 100),
                          description=text_field(body, "description", "Description", maximum=500) or "")
    set_model_names(line, validate_model_names(body.get("model_names", [])))
    commit_record(line)
    return jsonify(success=True, data=get_production_line_summary(line)), 201


def validate_model_names(values):
    if not isinstance(values, list) or len(values) > 50:
        raise ValidationError("Model Names must be a list of up to 50 names.")
    names, seen = [], set()
    for value in values:
        if not isinstance(value, str) or not value.strip() or len(value.strip()) > 150:
            raise ValidationError("Each Model Name must contain 1 to 150 characters.")
        value = value.strip()
        if value.casefold() in seen:
            raise ValidationError("Duplicate Model Names are not allowed.")
        seen.add(value.casefold())
        names.append(value)
    return names


def set_model_names(line, names):
    existing = {entry.model_name.casefold(): entry for entry in line.model_entries}
    entries = []
    for position, name in enumerate(names):
        entry = existing.get(name.casefold()) or ProductionLineModel()
        entry.model_name = name
        entry.position = position
        entries.append(entry)
    line.model_entries = entries


@production_lines.patch("/production-lines/<int:line_id>")
def edit_production_line(line_id):
    body = json_body()
    values = {}
    if "name" in body:
        values["name"] = text_field(body, "name", "Production Line name", True, 100)
    if "description" in body:
        values["description"] = text_field(body, "description", "Description", maximum=500) or ""
    names = validate_model_names(body["model_names"]) if "model_names" in body else None
    if not values and names is None:
        raise ValidationError("Provide Production Line information to update.")
    db.session.execute(text("BEGIN IMMEDIATE"))
    line = db.session.get(ProductionLine, line_id)
    if line is None:
        db.session.rollback()
        return jsonify(success=False, message="Production Line not found."), 404
    for key, value in values.items():
        setattr(line, key, value)
    if names is not None and names != [entry.model_name for entry in line.model_entries]:
        set_model_names(line, names)
        from ..timezone import utcnow
        line.updated_at = utcnow()
    commit_record(line)
    return jsonify(success=True, data=get_production_line_summary(line))
