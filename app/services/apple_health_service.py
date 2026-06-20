# Apple Health integration removed. Use garmin_service.py for health data integration.
import json
import logging
import re
import time
from datetime import datetime, timezone

import requests

from ..db import get_connection

logger = logging.getLogger(__name__)


CANONICAL_METRIC_KEYS = {
    "measured_at",
    "weight_kg",
    "sleep_hours",
    "heart_rate_resting",
    "heart_rate_avg",
    "hrv_ms",
    "steps",
}


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


def _first_present(source, *keys):
    for key in keys:
        if key in source and source[key] not in (None, ""):
            return source[key]
    return None


def _to_snake_case(value):
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", str(value or ""))
    value = value.replace("-", "_").replace(" ", "_")
    value = re.sub(r"[^a-zA-Z0-9_]", "", value)
    value = re.sub(r"_+", "_", value).strip("_").lower()
    return value


def _to_label(key):
    return " ".join(part.capitalize() for part in str(key).replace("-", "_").split("_") if part)


def _candidate_score(candidate):
    aliases = (
        "measured_at", "measuredAt", "timestamp", "date",
        "weight_kg", "weightKg", "weight", "body_weight_kg", "bodyMass",
        "sleep_hours", "sleepHours", "sleep_duration_hours", "sleepDurationHours",
        "heart_rate_resting", "restingHeartRate", "resting_heart_rate", "rhr",
        "heart_rate_avg", "averageHeartRate", "avgHeartRate", "avg_heart_rate",
        "hrv_ms", "hrvMs", "hrv",
        "steps", "stepCount",
    )
    return sum(1 for alias in aliases if alias in candidate and candidate[alias] not in (None, ""))


def _find_best_metric_object(payload):
    best = payload if isinstance(payload, dict) else None
    best_score = _candidate_score(best) if isinstance(best, dict) else -1

    def walk(node):
        nonlocal best, best_score
        if isinstance(node, dict):
            score = _candidate_score(node)
            if score > best_score:
                best = node
                best_score = score
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(payload)
    return best


def _extract_metrics(payload):
    candidate = _find_best_metric_object(payload) if isinstance(payload, (dict, list)) else payload
    if not isinstance(candidate, dict):
        candidate = {}

    metrics = {
        "measured_at": _first_present(
            candidate,
            "measured_at",
            "measuredAt",
            "timestamp",
            "date",
            "recordedAt",
            "startDate",
            "start_date",
            "sampleStartDate",
            "sample_start_date",
            "endDate",
            "end_date",
        ),
        "weight_kg": _as_float(_first_present(candidate, "weight_kg", "weightKg", "weight", "body_weight_kg", "bodyMass", "bodyMassKg")),
        "sleep_hours": _as_float(_first_present(candidate, "sleep_hours", "sleepHours", "sleep_duration_hours", "sleepDurationHours")),
        "heart_rate_resting": _as_float(_first_present(candidate, "heart_rate_resting", "restingHeartRate", "resting_heart_rate", "rhr")),
        "heart_rate_avg": _as_float(_first_present(candidate, "heart_rate_avg", "averageHeartRate", "avgHeartRate", "avg_heart_rate")),
        "hrv_ms": _as_float(_first_present(candidate, "hrv_ms", "hrvMs", "hrv")),
        "steps": _as_float(_first_present(candidate, "steps", "stepCount")),
    }

    # Keep additional primitive payload keys so they can be mapped dynamically.
    alias_keys = {
        "measured_at", "measuredAt", "timestamp", "date", "recordedAt", "startDate", "start_date", "sampleStartDate", "sample_start_date", "endDate", "end_date",
        "weight_kg", "weightKg", "weight", "body_weight_kg", "bodyMass", "bodyMassKg",
        "sleep_hours", "sleepHours", "sleep_duration_hours", "sleepDurationHours",
        "heart_rate_resting", "restingHeartRate", "resting_heart_rate", "rhr",
        "heart_rate_avg", "averageHeartRate", "avgHeartRate", "avg_heart_rate",
        "hrv_ms", "hrvMs", "hrv",
        "steps", "stepCount",
    }

    for raw_key, raw_value in candidate.items():
        if raw_key in alias_keys:
            continue
        if isinstance(raw_value, (dict, list)):
            continue
        normalized_key = _to_snake_case(raw_key)
        if not normalized_key or normalized_key in metrics:
            continue

        if isinstance(raw_value, bool):
            metrics[normalized_key] = raw_value
        elif isinstance(raw_value, (int, float)):
            metrics[normalized_key] = float(raw_value)
        elif isinstance(raw_value, str) and raw_value.strip() != "":
            metrics[normalized_key] = raw_value.strip()

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
    _set_system_param(conn, "apple_health_last_payload_raw", json.dumps(payload))

    # Persist non-canonical discovered fields so settings can map newly seen payload keys.
    discovered_raw = _get_system_param(conn, "apple_health_discovered_fields") or "[]"
    try:
        discovered = json.loads(discovered_raw)
    except Exception:
        discovered = []
    if not isinstance(discovered, list):
        discovered = []

    by_key = {str(item.get("key")): item for item in discovered if isinstance(item, dict) and item.get("key")}
    for key, value in normalized.items():
        if key in CANONICAL_METRIC_KEYS or value is None:
            continue
        by_key[key] = {
            "key": key,
            "label": _to_label(key),
            "column_type": "number" if isinstance(value, (int, float)) and not isinstance(value, bool) else "text",
            "group": "Additional Metrics",
            "unit": "",
        }

    _set_system_param(conn, "apple_health_discovered_fields", json.dumps(list(by_key.values())))
    _set_system_param(conn, "apple_health_last_source", source)
    _set_system_param(conn, "apple_health_last_sync_timestamp", int(time.time()))
    conn.commit()
    return normalized


def _apply_field_mapping(
    entry_id: int,
    metrics: dict,
    field_mapping: dict,
    conn,
    entry_type_id: int | None = None,
    only_changed_from_history: bool = False,
) -> None:
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
        if only_changed_from_history and entry_type_id:
            previous_value = _latest_value_for_column(conn, entry_type_id, int(column_id), exclude_entry_id=entry_id)
            if previous_value is not None and str(previous_value) == str(value):
                continue
        try:
            # Use DB-agnostic upsert logic so this works on both MariaDB and MariaDB.
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


def _date_part(dt_str):
    """Return the YYYY-MM-DD portion of an ISO timestamp string, or None."""
    if not dt_str:
        return None
    return str(dt_str)[:10]


def _hour_parts(dt_str):
    """Return (day, hour) from ISO-like datetime strings, else (None, None)."""
    if not dt_str:
        return None, None
    text = str(dt_str)
    match = re.match(r"^(\d{4}-\d{2}-\d{2})[T ](\d{2})", text)
    if not match:
        return None, None
    return match.group(1), match.group(2)


def _metrics_changed(existing_entry_id, new_metrics, field_mapping, conn):
    """Return True if any mapped metric value differs from what is stored."""
    if not field_mapping:
        return False
    cursor = conn.cursor()
    cursor.execute(
        "SELECT custom_column_id, value FROM CustomColumnValue WHERE entry_id = ?",
        (existing_entry_id,),
    )
    rows = cursor.fetchall()
    stored = {str(row["custom_column_id"]): row["value"] for row in (rows or [])}
    for field_key, column_id in field_mapping.items():
        if not column_id:
            continue
        new_value = new_metrics.get(field_key)
        if new_value is None:
            continue
        old_value = stored.get(str(column_id))
        if old_value is None or str(new_value) != str(old_value):
            return True
    return False


def _latest_value_for_column(conn, entry_type_id: int, custom_column_id: int, exclude_entry_id: int | None = None):
    cursor = conn.cursor()
    sql = (
        "SELECT ccv.value "
        "FROM CustomColumnValue ccv "
        "JOIN Entry e ON e.id = ccv.entry_id "
        "WHERE e.entry_type_id = ? AND ccv.custom_column_id = ?"
    )
    params = [entry_type_id, custom_column_id]
    if exclude_entry_id:
        sql += " AND ccv.entry_id <> ?"
        params.append(exclude_entry_id)
    sql += " ORDER BY ccv.updated_at DESC, ccv.id DESC LIMIT 1"
    cursor.execute(sql, tuple(params))
    row = cursor.fetchone()
    return row["value"] if row else None


def _has_history_change(metrics, field_mapping, conn, entry_type_id: int) -> bool:
    """Return True if any mapped metric changed versus the latest stored value."""
    if not field_mapping:
        return True

    saw_mapped_value = False
    for field_key, column_id in field_mapping.items():
        if not column_id:
            continue
        value = metrics.get(field_key)
        if value is None:
            continue
        saw_mapped_value = True
        previous_value = _latest_value_for_column(conn, entry_type_id, int(column_id))
        if previous_value is None or str(previous_value) != str(value):
            return True

    return False if saw_mapped_value else True


def _get_or_create_entry(conn, metrics, entry_type_id, field_mapping):
    """Return (entry_id, created, updated) using measured_at hour as primary dedup key."""
    measured_at = metrics.get("measured_at")
    day = _date_part(measured_at)
    hour_day, hour = _hour_parts(measured_at)
    created_at = measured_at or datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    if hour_day and hour:
        title_date = f"{hour_day} {hour}:00"
    else:
        title_date = day or created_at
    title = f"Apple Health Sync {title_date}"

    cursor = conn.cursor()

    # Prefer hour-level dedup when measured_at is provided.
    if hour_day and hour:
        iso_like = f"{hour_day}T{hour}:%"
        space_like = f"{hour_day} {hour}:%"
        cursor.execute(
            """
            SELECT id FROM Entry
            WHERE entry_type_id = ? AND (commenced_at LIKE ? OR commenced_at LIKE ?)
            ORDER BY id DESC LIMIT 1
            """,
            (entry_type_id, iso_like, space_like),
        )
        row = cursor.fetchone()
        if row:
            existing_id = row["id"]
            if _metrics_changed(existing_id, metrics, field_mapping, conn):
                logger.info("Apple Health: updating existing entry %d for hour=%s %s:00", existing_id, hour_day, hour)
                return existing_id, False, True
            logger.info("Apple Health: no changes for hour=%s %s:00, skipping", hour_day, hour)
            return existing_id, False, False

    # Fallback for legacy payloads: same day + entry type.
    if day:
        cursor.execute(
            """
            SELECT id FROM Entry
            WHERE entry_type_id = ? AND title = ?
            ORDER BY id DESC LIMIT 1
            """,
            (entry_type_id, title),
        )
        row = cursor.fetchone()
        if row:
            existing_id = row["id"]
            if _metrics_changed(existing_id, metrics, field_mapping, conn):
                logger.info("Apple Health: updating existing entry %d for day=%s", existing_id, day)
                return existing_id, False, True
            else:
                logger.info("Apple Health: no changes for day=%s, skipping", day)
                return existing_id, False, False

    # No entry yet for this hour/day: only create if at least one mapped value changed from history.
    if not _has_history_change(metrics, field_mapping, conn, entry_type_id):
        logger.info("Apple Health: no mapped metric changes since last stored values, skipping new entry")
        return None, False, False

    description_lines = ["Apple Health sync"]
    for key, label in (
        ("weight_kg", "Weight (kg)"),
        ("sleep_hours", "Sleep (hours)"),
        ("heart_rate_resting", "Resting Heart Rate"),
        ("heart_rate_avg", "Average Heart Rate"),
        ("hrv_ms", "HRV (ms)"),
        ("steps", "Steps"),
    ):
        value = metrics.get(key)
        if value is not None:
            description_lines.append(f"{label}: {value}")

    cursor.execute(
        """
        INSERT INTO Entry (title, description, created_at, entry_type_id, status, commenced_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (title, "\n".join(description_lines), created_at, entry_type_id, "Completed", measured_at or created_at),
    )
    return cursor.lastrowid, True, False


def _create_entry_for_metrics(conn, metrics: dict) -> tuple:
    """Return (entry_id, created, updated) or (None, False, False)."""
    entry_type_id = _get_system_param(conn, "apple_health_entry_type_id")
    if not entry_type_id:
        logger.info("Apple Health: no entry type configured; payload stored without creating entry")
        return None, False, False

    try:
        entry_type_id = int(entry_type_id)
    except (TypeError, ValueError):
        logger.warning("Apple Health: invalid configured entry type id %r", entry_type_id)
        return None, False, False

    field_mapping = json.loads(_get_system_param(conn, "apple_health_field_mapping") or "{}")
    return _get_or_create_entry(conn, metrics, entry_type_id, field_mapping)


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
        entry_id, created, updated = _create_entry_for_metrics(conn, normalized)
        field_mapping = json.loads(_get_system_param(conn, "apple_health_field_mapping") or "{}")
        entry_type_raw = _get_system_param(conn, "apple_health_entry_type_id")
        try:
            entry_type_id = int(entry_type_raw) if entry_type_raw else None
        except (TypeError, ValueError):
            entry_type_id = None
        if entry_id and (created or updated):
            _apply_field_mapping(
                entry_id,
                normalized,
                field_mapping,
                conn,
                entry_type_id=entry_type_id,
                only_changed_from_history=created,
            )
            conn.commit()

        if created:
            action = "Entry created"
        elif updated:
            action = "Entry updated with changed values"
        else:
            action = "No changes detected, entry not modified"

        return {
            "status": "success",
            "message": f"Apple Health payload received. {action}.",
            "data": normalized,
            "entry_id": entry_id,
            "created": created,
            "updated": updated,
        }
    finally:
        conn.close()
