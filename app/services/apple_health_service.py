import json
import logging
import time
from datetime import datetime, timezone

import requests

from ..db import get_connection

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


def _as_float(value):
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _extract_metrics(payload):
    metrics = {
        "measured_at": payload.get("measured_at") or payload.get("timestamp") or payload.get("date"),
        "weight_kg": _as_float(payload.get("weight_kg") or payload.get("weight") or payload.get("body_weight_kg")),
        "sleep_hours": _as_float(payload.get("sleep_hours") or payload.get("sleep_duration_hours")),
        "heart_rate_resting": _as_float(payload.get("heart_rate_resting") or payload.get("resting_heart_rate") or payload.get("rhr")),
        "heart_rate_avg": _as_float(payload.get("heart_rate_avg") or payload.get("avg_heart_rate")),
        "hrv_ms": _as_float(payload.get("hrv_ms") or payload.get("hrv")),
        "steps": _as_float(payload.get("steps")),
    }
    return metrics


def _normalize_payload(payload):
    if isinstance(payload, list):
        if not payload:
            raise ValueError("Payload list is empty")
        candidate = payload[-1]
    elif isinstance(payload, dict):
        if "data" in payload and isinstance(payload["data"], list) and payload["data"]:
            candidate = payload["data"][-1]
        else:
            candidate = payload
    else:
        raise ValueError("Payload must be a JSON object or list")

    if not isinstance(candidate, dict):
        raise ValueError("Could not find an object containing metrics")

    return _extract_metrics(candidate)


def _store_payload(conn, payload, source):
    normalized = _normalize_payload(payload)
    _set_system_param(conn, "apple_health_last_payload", json.dumps(normalized))
    _set_system_param(conn, "apple_health_last_source", source)
    _set_system_param(conn, "apple_health_last_sync_timestamp", int(time.time()))
    conn.commit()
    return normalized


def _apply_field_mapping(entry_id: int, metrics: dict, field_mapping: dict, conn) -> None:
    """Write Apple Health metric values into CustomColumnValue rows per the saved mapping."""
    if not field_mapping:
        return
    cursor = conn.cursor()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    for field_key, column_id in field_mapping.items():
        if not column_id:
            continue
        value = metrics.get(field_key)
        if value is None:
            continue
        try:
            # Use DB-agnostic upsert logic so this works on both SQLite and MariaDB.
            cursor.execute(
                "UPDATE CustomColumnValue SET value = ?, updated_at = ? WHERE custom_column_id = ? AND entry_id = ?",
                (str(value), now, int(column_id), entry_id),
            )
            if cursor.rowcount and cursor.rowcount > 0:
                continue
            cursor.execute(
                """INSERT INTO CustomColumnValue (custom_column_id, entry_id, value, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (int(column_id), entry_id, str(value), now, now),
            )
        except Exception as exc:
            logger.warning("Apple Health: failed to write col value (%s -> col %s): %s", field_key, column_id, exc)


def sync_apple_health_data():
    conn = get_connection()
    try:
        enabled = str(_get_system_param(conn, "apple_health_enabled") or "0").lower()
        if enabled not in ("1", "true", "yes", "on"):
            return {"status": "skipped", "message": "Apple Health integration disabled"}

        source_url = _get_system_param(conn, "apple_health_source_url")
        if not source_url:
            return {
                "status": "skipped",
                "message": "No Apple Health source URL configured. Use push endpoint or set a source URL.",
            }

        headers = {}
        token = _get_system_param(conn, "apple_health_source_token")
        if token:
            headers["Authorization"] = f"Bearer {token}"

        response = requests.get(source_url, headers=headers, timeout=20)
        response.raise_for_status()

        payload = response.json()
        normalized = _store_payload(conn, payload, "pull")

        return {
            "status": "success",
            "message": "Apple Health data synced successfully",
            "data": normalized,
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"Apple Health pull error: {e}")
        return {"status": "error", "message": f"Failed to fetch Apple Health source: {e}"}
    except Exception as e:
        logger.error(f"Apple Health sync error: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}
    finally:
        conn.close()


def store_apple_health_push(payload):
    conn = get_connection()
    try:
        normalized = _store_payload(conn, payload, "push")
        return {
            "status": "success",
            "message": "Apple Health payload received",
            "data": normalized,
        }
    finally:
        conn.close()
