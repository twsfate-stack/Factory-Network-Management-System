from flask import Blueprint, jsonify
from ..models import db, ProductionLine
from ..validation import json_body, text_field, commit_record

production_lines = Blueprint("production_lines", __name__)


def get_production_line_summary(line):
    statuses = {switch.status for switch in line.switches}
    status = "OFFLINE" if "OFFLINE" in statuses else "ACTIVE" if "ACTIVE" in statuses else "SPARE" if statuses else None
    combinations = {f"{switch.vendor} {switch.model}" for switch in line.switches}
    return dict(id=line.id, name=line.name, description=line.description,
                total_switches=len(line.switches), status=status,
                switch_models=sorted(combinations, key=str.casefold),
                created_at=line.created_at.isoformat() + "Z", updated_at=line.updated_at.isoformat() + "Z")


@production_lines.get("/production-lines")
def get_production_lines():
    lines = db.session.scalars(db.select(ProductionLine).order_by(ProductionLine.name)).all()
    return jsonify([get_production_line_summary(line) for line in lines])


@production_lines.post("/production-lines")
def create_production_line():
    body = json_body()
    line = ProductionLine(name=text_field(body, "name", "Production Line name", True, 100),
                          description=text_field(body, "description", "Description", maximum=500) or "")
    commit_record(line)
    return jsonify(success=True, data=get_production_line_summary(line)), 201
