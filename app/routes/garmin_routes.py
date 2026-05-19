import logging

from flask import Blueprint, jsonify, request

from ..db import get_connection
from ..services.garmin_service import sync_garmin_data

garmin_routes_bp = Blueprint("garmin_routes", __name__)
logger = logging.getLogger(__name__)


def _get_system_param(conn, param_name):
    cursor = conn.cursor()
    cursor.execute("SELECT parameter_value FROM SystemParameters WHERE parameter_name = ?", (param_name,))
    row = cursor.fetchone()
    return row["parameter_value"] if row else None


def _set_system_param(conn, param_name, param_value):
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO SystemParameters (parameter_name, parameter_value) VALUES (?, ?)",
        (param_name, str(param_value)),
    )
    conn.commit()


@garmin_routes_bp.route("/garmin/sync", methods=["POST"])
def garmin_sync():
    try:
        data = request.get_json(silent=True) or {}
        target_date = data.get("date")
        result = sync_garmin_data(target_date=target_date)
        code = 200 if result.get("status") != "error" else 500
        return jsonify(result), code
    except Exception as e:
        logger.error(f"Garmin sync route error: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@garmin_routes_bp.route("/garmin/clear_last_sync", methods=["POST"])
def garmin_clear_last_sync():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM SystemParameters WHERE parameter_name IN ('garmin_last_sync_timestamp','garmin_last_sync_date')"
        )
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": "Garmin last sync cleared."})
    except Exception as e:
        logger.error(f"Garmin clear sync error: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@garmin_routes_bp.route("/garmin/save_config", methods=["POST"])
def garmin_save_config():
    """Save Garmin credentials to SystemParameters."""
    try:
        data = request.get_json(silent=True) or {}
        username = data.get("username", "").strip()
        password = data.get("password", "").strip()
        if not username or not password:
            return jsonify({"status": "error", "message": "Username and password are required."}), 400
        conn = get_connection()
        _set_system_param(conn, "garmin_username", username)
        _set_system_param(conn, "garmin_password", password)
        conn.close()
        return jsonify({"status": "success", "message": "Garmin credentials saved."})
    except Exception as e:
        logger.error(f"Garmin save config error: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500
