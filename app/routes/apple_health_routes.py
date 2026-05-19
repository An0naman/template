# Apple Health routes removed. Use garmin_routes.py for health data integration.
import logging

from flask import Blueprint, jsonify, request

from ..db import get_connection
from ..services.apple_health_service import store_apple_health_push, sync_apple_health_data

apple_health_routes_bp = Blueprint("apple_health_routes", __name__)
logger = logging.getLogger(__name__)


def _get_system_param(conn, param_name):
    cursor = conn.cursor()
    cursor.execute("SELECT parameter_value FROM SystemParameters WHERE parameter_name = ?", (param_name,))
    row = cursor.fetchone()
    return row["parameter_value"] if row else None


@apple_health_routes_bp.route('/apple-health/sync', methods=['POST'])
def apple_health_sync():
    try:
        result = sync_apple_health_data()
        code = 200 if result.get("status") != "error" else 500
        return jsonify(result), code
    except Exception as e:
        logger.error(f"Apple Health sync route error: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@apple_health_routes_bp.route('/apple-health/clear_last_sync', methods=['POST'])
def apple_health_clear_last_sync():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM SystemParameters WHERE parameter_name IN ('apple_health_last_sync_timestamp','apple_health_last_payload','apple_health_last_source')"
        )
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": "Apple Health last sync cleared."})
    except Exception as e:
        logger.error(f"Apple Health clear sync error: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@apple_health_routes_bp.route('/apple-health/push', methods=['POST'])
def apple_health_push():
    try:
        conn = get_connection()
        configured_key = _get_system_param(conn, 'apple_health_api_key')
        conn.close()

        provided_key = request.headers.get('X-Apple-Health-Key')
        if configured_key and provided_key != configured_key:
            return jsonify({"status": "error", "message": "Invalid API key"}), 401

        payload = request.get_json(silent=True)
        if payload is None:
            return jsonify({"status": "error", "message": "Invalid JSON payload"}), 400

        result = store_apple_health_push(payload)
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Apple Health push error: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500
