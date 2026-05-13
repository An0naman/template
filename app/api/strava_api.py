"""
Strava Integration API
REST endpoints for field mapping and auto-create column support.
"""

from flask import Blueprint, request, jsonify, g
import logging
import json
from datetime import datetime, timezone

from ..db import get_connection, get_system_parameters
from ..services.strava_service import STRAVA_FIELDS

logger = logging.getLogger(__name__)

strava_api_bp = Blueprint("strava_api", __name__, url_prefix="/api/strava")


def get_db():
    if "db" not in g:
        g.db = get_connection()
    return g.db


# ── Field registry ────────────────────────────────────────────────────────────

@strava_api_bp.route("/fields", methods=["GET"])
def api_get_fields():
    """Return the canonical list of Strava activity fields available for mapping."""
    return jsonify({"fields": STRAVA_FIELDS})


# ── Field mapping ─────────────────────────────────────────────────────────────

@strava_api_bp.route("/field_mapping", methods=["GET"])
def api_get_field_mapping():
    """Return the saved field mapping (strava field key -> custom_column_id)."""
    params = get_system_parameters()
    mapping = json.loads(params.get("strava_field_mapping", "{}") or "{}")
    return jsonify({"mapping": mapping})


@strava_api_bp.route("/field_mapping", methods=["POST"])
def api_save_field_mapping():
    """
    Save the field mapping.
    Body: { "mapping": { "distance_km": 7, "moving_time_min": 12, ... } }
    Values are CustomColumn IDs (int) or "" to unmap.
    """
    data = request.get_json() or {}
    mapping = data.get("mapping", {})

    valid_keys = {f["key"] for f in STRAVA_FIELDS}
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
        ("strava_field_mapping", json.dumps(clean)),
    )
    conn.commit()
    return jsonify({"success": True, "mapping": clean})


# ── Auto-create columns ───────────────────────────────────────────────────────

@strava_api_bp.route("/auto_create_columns", methods=["POST"])
def api_auto_create_columns():
    """
    Auto-create CustomColumns for every STRAVA_FIELDS field for each mapped activity type,
    assign them to the given entry types, and save the full field mapping.

    Body: { "activity_type_entry_map": { "Run": 3, "Ride": 4, ... } }
    """
    data = request.get_json() or {}
    params = get_system_parameters()

    activity_type_entry_map = data.get("activity_type_entry_map")
    if not activity_type_entry_map or not isinstance(activity_type_entry_map, dict):
        return jsonify({"success": False, "message": "No activity type mapping provided."}), 400

    conn = get_db()
    cursor = conn.cursor()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    created = []
    existing = []
    assignments_created = []
    assignments_existing = []

    # Probe for unit column (migration may not have run on some envs)
    try:
        cursor.execute("SELECT unit FROM CustomColumn LIMIT 1")
        _has_unit_col = True
    except Exception:
        _has_unit_col = False
    cursor = conn.cursor()

    # Track all columns and assignments for mapping
    all_field_columns = {}
    all_assignments = set()

    for activity_type, entry_type_id in activity_type_entry_map.items():
        try:
            entry_type_id = int(entry_type_id)
        except Exception:
            continue
        for field in STRAVA_FIELDS:
            col_name  = f"strava_{field['key']}"
            col_label = field["label"]
            col_type  = field["column_type"]

            # Create or reuse column
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
                         f"Auto-created by Strava integration ({field['group']})",
                         col_type, "[]", "", 0, field.get("unit", ""), now, now),
                    )
                else:
                    cursor.execute(
                        """INSERT INTO CustomColumn (name, label, description, column_type, `options`,
                               default_value, is_required, created_at, updated_at)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (col_name, col_label,
                         f"Auto-created by Strava integration ({field['group']})",
                         col_type, "[]", "", 0, now, now),
                    )
                col_id = cursor.lastrowid
                created.append({"key": field["key"], "column_id": col_id, "label": col_label})

            all_field_columns[field["key"]] = col_id

            # Assign to entry type if not already done
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
                assignments_created.append({"column_id": col_id, "entry_type_id": entry_type_id, "field_key": field["key"], "activity_type": activity_type})
            else:
                assignments_existing.append({"column_id": col_id, "entry_type_id": entry_type_id, "field_key": field["key"], "activity_type": activity_type})
            all_assignments.add((field["key"], entry_type_id))

    # Save mapping for UI (maps field key to column id)
    mapping = {key: col_id for key, col_id in all_field_columns.items()}
    cursor.execute(
        "INSERT OR REPLACE INTO SystemParameters (parameter_name, parameter_value) VALUES (?, ?)",
        ("strava_field_mapping", json.dumps(mapping)),
    )
    conn.commit()

    return jsonify({
        "success": True,
        "created": created,
        "existing": existing,
        "assignments_created": assignments_created,
        "assignments_existing": assignments_existing,
        "mapping": mapping,
        "message": f"Columns and assignments created for {len(activity_type_entry_map)} activity types. {len(created)} columns created, {len(existing)} reused. {len(assignments_created)} new links, {len(assignments_existing)} reused.",
    })
