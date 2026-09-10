from flask import Blueprint, jsonify

health = Blueprint("health", __name__)


@health.get("/health")
def get_health():
    return jsonify(status="ok", application="Factory Network Management System")
