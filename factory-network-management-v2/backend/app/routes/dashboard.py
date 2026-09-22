from flask import Blueprint, jsonify
from sqlalchemy import func
from ..models import db, Switch

dashboard = Blueprint("dashboard", __name__)


@dashboard.get("/dashboard")
def get_dashboard_summary():
    counts = dict(db.session.execute(db.select(Switch.status, func.count(Switch.id)).where(Switch.is_deleted.is_(False)).group_by(Switch.status)).all())
    return jsonify(total_switches=sum(counts.values()), active=counts.get("ACTIVE", 0),
                   offline=counts.get("OFFLINE", 0), spare=counts.get("SPARE", 0))
