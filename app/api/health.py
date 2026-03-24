from flask import Blueprint, jsonify

from app.core.extensions import db, redis_client

health_bp = Blueprint("health", __name__)


@health_bp.route("/health/live")
def liveness():
    return jsonify({"status": "ok"})


@health_bp.route("/health/ready")
def readiness():
    errors = []

    try:
        redis_client.ping()
    except Exception:
        errors.append("redis")

    try:
        db.session.execute(db.text("SELECT 1"))
    except Exception:
        errors.append("database")

    if errors:
        return jsonify({"status": "unavailable", "errors": errors}), 503

    return jsonify({"status": "ready"})
