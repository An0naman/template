"""
Garmin Connect Integration API
REST endpoints for field mapping and auto-create column support.
"""

from flask import Blueprint, request, jsonify, g
import logging
import json
from datetime import datetime, timezone

from ..db import get_connection, get_system_parameters
from ..services.garmin_service import GARMIN_FIELDS

logger = logging.getLogger(__name__)

garmin_api_bp = Blueprint("garmin_api", __name__, url_prefix="/api/garmin")


def get_db():
    if "db" not in g:
        g.db = get_connection()
    return g.db


# ── Field registry ─────────────────────────────────────────────────────────────

@garmin_api_bp.route("/fields", methods=["GET"])
def api_get_fields():
    """Return all available Garmin fields for mapping."""
    return jsonify({"fields": GARMIN_FIELDS})


# ── Field mapping ──────────────────────────────────────────────────────────────

@garmin_api_bp.route("/field_mapping", methods=["GET"])
def api_get_field_mapping():
    """Return the saved field mapping (garmin field key -> custom_column_id)."""
    params = get_system_parameters()
    mapping = json.loads(params.get("garmin_field_mapping", "{}") or "{}")
    return jsonify({"mapping": mapping})


@garmin_api_bp.route("/field_mapping", methods=["POST"])
def api_save_field_mapping():
    """
    Save the field mapping.
    Body: { "mapping": { "total_steps": 7, "resting_heart_rate": 12, ... } }
    Values are CustomColumn IDs (int) or "" to unmap.
    """
    data = request.get_json() or {}
    mapping = data.get("mapping", {})

    valid_keys = {f["key"] for f in GARMIN_FIELDS}
    clean = {}
    for k, v in mapping.items():
        if k not in valid_keys:
            continue
        if v == "" or v is None:
            clean[k] = ""
        else:
            try:
                clean[k] = int(v)
            except (TypeError, ValueError):
                pass

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO SystemParameters (parameter_name, parameter_value) VALUES (?, ?)",
        ("garmin_field_mapping", json.dumps(clean)),
    )
    conn.commit()
    return jsonify({"success": True, "mapping": clean})


# ── Auto-create columns ────────────────────────────────────────────────────────

@garmin_api_bp.route("/auto_create_columns", methods=["POST"])
def api_auto_create_columns():
    """
    Auto-create CustomColumns for every GARMIN_FIELDS entry,
    assign them to the given entry type, and save the full field mapping.
    Body: { "entry_type_id": 5 }
    """
    data = request.get_json() or {}

    entry_type_id = data.get("entry_type_id")
    if not entry_type_id:
        return jsonify({"success": False, "message": "No entry type ID provided."}), 400

    try:
        entry_type_id = int(entry_type_id)
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "Invalid entry type ID."}), 400

    conn = get_db()
    cursor = conn.cursor()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    created = []
    existing = []
    assignments_created = []
    assignments_existing = []

    # Probe for unit column presence
    try:
        cursor.execute("SELECT unit FROM CustomColumn LIMIT 1")
        _has_unit_col = True
    except Exception:
        _has_unit_col = False
    cursor = conn.cursor()

    all_field_columns = {}

    for field in GARMIN_FIELDS:
        col_name  = f"garmin_{field['key']}"
        col_label = field["label"]
        col_type  = field["column_type"]

        cursor.execute("SELECT id FROM CustomColumn WHERE name = ?", (col_name,))
        row = cursor.fetchone()
        if row:
            col_id = row["id"]
            existing.append({"key": field["key"], "column_id": col_id, "label": col_label})
        else:
            if _has_unit_col:
                cursor.execute(
                    """INSERT INTO CustomColumn (name, label, description, column_type, `options`,
                           default_value, is_required, unit, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (col_name, col_label,
                     f"Auto-created by Garmin integration ({field['group']})",
                     col_type, "[]", "", 0, field.get("unit", ""), now, now),
                )
            else:
                cursor.execute(
                    """INSERT INTO CustomColumn (name, label, description, column_type, `options`,
                           default_value, is_required, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (col_name, col_label,
                     f"Auto-created by Garmin integration ({field['group']})",
                     col_type, "[]", "", 0, now, now),
                )
            col_id = cursor.lastrowid
            created.append({"key": field["key"], "column_id": col_id, "label": col_label})

        all_field_columns[field["key"]] = col_id

        cursor.execute(
            "SELECT id FROM CustomColumnAssignment WHERE custom_column_id=? AND entry_type_id=?",
            (col_id, entry_type_id),
        )
        if not cursor.fetchone():
            cursor.execute(
                """INSERT INTO CustomColumnAssignment
                       (custom_column_id, entry_type_id, section_placement, display_order, is_visible, created_at)
                   VALUES (?, ?, 'form_fields', 0, 1, ?)""",
                (col_id, entry_type_id, now),
            )
            assignments_created.append({"column_id": col_id, "entry_type_id": entry_type_id, "field_key": field["key"]})
        else:
            assignments_existing.append({"column_id": col_id, "entry_type_id": entry_type_id, "field_key": field["key"]})

    # Save entry_type_id for auto-entry creation on sync
    cursor.execute(
        "INSERT OR REPLACE INTO SystemParameters (parameter_name, parameter_value) VALUES (?, ?)",
        ("garmin_entry_type_id", str(entry_type_id)),
    )

    # Save mapping
    mapping = {key: col_id for key, col_id in all_field_columns.items()}
    cursor.execute(
        "INSERT OR REPLACE INTO SystemParameters (parameter_name, parameter_value) VALUES (?, ?)",
        ("garmin_field_mapping", json.dumps(mapping)),
    )
    conn.commit()

    return jsonify({
        "success": True,
        "created": created,
        "existing": existing,
        "assignments_created": assignments_created,
        "assignments_existing": assignments_existing,
        "mapping": mapping,
        "message": (
            f"{len(created)} columns created, {len(existing)} reused. "
            f"{len(assignments_created)} new assignments, {len(assignments_existing)} reused."
        ),
    })


# ── Test pull ──────────────────────────────────────────────────────────────────

@garmin_api_bp.route("/test_pull", methods=["GET"])
def api_test_pull():
    """
    Dry-run fetch: login, pull all data sources for the given date, flatten,
    and return every GARMIN_FIELDS entry with its resolved value.
    Nothing is written to the database.
    Query param: ?date=YYYY-MM-DD  (default: today)
    """
    from ..services.garmin_service import GARMIN_FIELDS, _flatten_garmin_data, _get_system_param
    from datetime import date as _date

    try:
        from garminconnect import Garmin
    except ImportError:
        return jsonify({"success": False, "message": "garminconnect library not installed."}), 500

    target_date = request.args.get("date") or _date.today().isoformat()

    conn = get_connection()
    username = _get_system_param(conn, "garmin_username")
    password = _get_system_param(conn, "garmin_password")
    conn.close()

    if not username or not password:
        return jsonify({"success": False, "message": "Garmin credentials not configured."}), 400

    try:
        client = Garmin(username, password)
        client.login()
    except Exception as e:
        return jsonify({"success": False, "message": f"Garmin login failed: {e}"}), 400

    errors = []

    def _fetch(label, fn):
        try:
            return fn()
        except Exception as exc:
            errors.append(f"{label}: {exc}")
            return None

    stats              = _fetch("stats",              lambda: client.get_stats_and_body(target_date))
    sleep_data         = _fetch("sleep",              lambda: client.get_sleep_data(target_date))
    body_data          = _fetch("body",               lambda: client.get_body_composition(target_date))
    hrv_data           = _fetch("hrv",                lambda: client.get_hrv_data(target_date))
    bp_data            = _fetch("bp",                 lambda: client.get_blood_pressure(target_date, target_date))
    training_status    = _fetch("training_status",    lambda: client.get_training_status(target_date))
    training_readiness = _fetch("training_readiness", lambda: client.get_training_readiness(target_date))
    hydration_data     = _fetch("hydration",          lambda: client.get_hydration_data(target_date))
    fitness_age_data   = _fetch("fitness_age",        lambda: client.get_fitnessage_data(target_date))
    endurance_data     = _fetch("endurance",          lambda: client.get_endurance_score(target_date))
    hill_data          = _fetch("hill",               lambda: client.get_hill_score(target_date))

    if isinstance(body_data, dict) and "totalAverage" in body_data:
        body_data = body_data["totalAverage"]

    flat = _flatten_garmin_data(
        stats, sleep_data, None, body_data, hrv_data, None, None, bp_data,
        training_status_data=training_status,
        training_readiness_data=training_readiness,
        hydration_data=hydration_data,
        fitness_age_data=fitness_age_data,
        endurance_data=endurance_data,
        hill_data=hill_data,
    )

    results = [
        {
            "key":   f["key"],
            "label": f["label"],
            "group": f["group"],
            "unit":  f.get("unit", ""),
            "value": flat.get(f["key"]),
        }
        for f in GARMIN_FIELDS
    ]

    return jsonify({
        "success":          True,
        "date":             target_date,
        "fields_with_data": len(flat),
        "total_fields":     len(GARMIN_FIELDS),
        "errors":           errors,
        "results":          results,
    })
