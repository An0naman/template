"""
Anycubic 3D Printer API
REST endpoints for the Anycubic integration settings section.
"""

from flask import Blueprint, request, jsonify, g
import logging
import json
from datetime import datetime, timezone

import os
from flask import current_app
from ..db import get_connection, get_system_parameters
from ..services.anycubic_service import (
    get_printer_status, test_connection, format_duration, PRINTER_FIELDS, download_print_file
)

logger = logging.getLogger(__name__)

anycubic_api_bp = Blueprint("anycubic_api", __name__, url_prefix="/api/anycubic")


def get_db():
    if "db" not in g:
        g.db = get_connection()
    return g.db


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_anycubic_params() -> dict:
    params = get_system_parameters()
    return {
        "enabled":             params.get("anycubic_enabled", "false") == "true",
        "api_type":            params.get("anycubic_api_type", "kobra2_local"),
        "ip":                  params.get("anycubic_printer_ip", ""),
        "port":                params.get("anycubic_printer_port", "80"),
        "api_key":             params.get("anycubic_api_key", ""),
        "polling_enabled":     params.get("anycubic_polling_enabled", "false") == "true",
        "polling_interval":    int(params.get("anycubic_polling_interval", "30")),
        "auto_create_entries": params.get("anycubic_auto_create_entries", "false") == "true",
        "fetch_file":          params.get("anycubic_fetch_file", "false") == "true",
        "entry_type_id":       params.get("anycubic_entry_type_id", ""),
        "field_mapping":       json.loads(params.get("anycubic_field_mapping", "{}") or "{}"),
    }


def _apply_field_mapping(entry_id: int, status: dict, field_mapping: dict, conn) -> None:
    """
    Write printer status values into CustomColumnValue rows according to the saved mapping.
    field_mapping: { "printer_field_key": custom_column_id (int), ... }
    """
    if not field_mapping:
        return
    cursor = conn.cursor()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    for field_key, column_id in field_mapping.items():
        if not column_id:
            continue
        value = status.get(field_key)
        if value is None:
            continue
        try:
            cursor.execute(
                """INSERT INTO CustomColumnValue (custom_column_id, entry_id, value, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?)
                   ON CONFLICT(custom_column_id, entry_id)
                   DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at""",
                (int(column_id), entry_id, str(value), now, now),
            )
        except Exception as exc:
            logger.warning("Failed to write custom column value (%s -> col %s): %s", field_key, column_id, exc)


# ── Field registry ────────────────────────────────────────────────────────────

@anycubic_api_bp.route("/fields", methods=["GET"])
def api_get_fields():
    """Return the canonical list of printer fields available for mapping."""
    return jsonify({"fields": PRINTER_FIELDS})


# ── Field mapping ─────────────────────────────────────────────────────────────

@anycubic_api_bp.route("/field_mapping", methods=["GET"])
def api_get_field_mapping():
    """Return the saved field mapping (printer field key -> custom_column_id)."""
    params = get_system_parameters()
    mapping = json.loads(params.get("anycubic_field_mapping", "{}") or "{}")
    return jsonify({"mapping": mapping})


@anycubic_api_bp.route("/field_mapping", methods=["POST"])
def api_save_field_mapping():
    """
    Save the field mapping.
    Body: { "mapping": { "filament_used_mm": 7, "elapsed_time": 12, ... } }
    Values are CustomColumn IDs (int) or "" to unmap.
    """
    data = request.get_json() or {}
    mapping = data.get("mapping", {})

    valid_keys = {f["key"] for f in PRINTER_FIELDS}
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
        ("anycubic_field_mapping", json.dumps(clean)),
    )
    conn.commit()
    return jsonify({"success": True, "mapping": clean})


@anycubic_api_bp.route("/auto_create_columns", methods=["POST"])
def api_auto_create_columns():
    """
    Auto-create a CustomColumn for every PRINTER_FIELDS field, assign them all to the
    configured entry type, and save the full field mapping automatically.

    Body (optional): { "entry_type_id": 3 }
    """
    data = request.get_json() or {}
    cfg = _get_anycubic_params()
    entry_type_id = int(data.get("entry_type_id") or cfg["entry_type_id"] or 0)
    if not entry_type_id:
        return jsonify({"success": False, "message": "No entry type configured."}), 400

    conn = get_db()
    cursor = conn.cursor()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    created = []
    existing = []

    # Detect whether the unit column exists yet (migration may not have run)
    try:
        cursor.execute("SELECT unit FROM CustomColumn LIMIT 1")
        _has_unit_col = True
    except Exception:
        _has_unit_col = False
    # Reset cursor state after the probe (some drivers leave it dirty on exception)
    cursor = conn.cursor()

    for field in PRINTER_FIELDS:
        col_name  = f"printer_{field['key']}"
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
                     f"Auto-created by Anycubic integration ({field['group']})",
                     col_type, "[]", "", 0, field.get("unit", ""), now, now),
                )
            else:
                cursor.execute(
                    """INSERT INTO CustomColumn (name, label, description, column_type, `options`,
                           default_value, is_required, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (col_name, col_label,
                     f"Auto-created by Anycubic integration ({field['group']})",
                     col_type, "[]", "", 0, now, now),
                )
            col_id = cursor.lastrowid
            created.append({"key": field["key"], "column_id": col_id, "label": col_label})

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

    all_fields = created + existing
    mapping = {item["key"]: item["column_id"] for item in all_fields}
    cursor.execute(
        "INSERT OR REPLACE INTO SystemParameters (parameter_name, parameter_value) VALUES (?, ?)",
        ("anycubic_field_mapping", json.dumps(mapping)),
    )
    conn.commit()

    return jsonify({
        "success": True,
        "created": created,
        "existing": existing,
        "mapping": mapping,
        "message": f"Created {len(created)} columns, found {len(existing)} existing. All mapped.",
    })


# ── Connection test ───────────────────────────────────────────────────────────

@anycubic_api_bp.route("/test_connection", methods=["POST"])
def api_test_connection():
    data    = request.get_json() or {}
    api_type = data.get("api_type", "kobra2_local")
    ip      = data.get("ip", "").strip()
    port    = data.get("port", "80").strip()
    api_key = data.get("api_key", "").strip()

    if not ip:
        return jsonify({"success": False, "message": "IP address is required."}), 400

    result = test_connection(api_type, ip, port, api_key)
    return jsonify(result)


# ── Live status ───────────────────────────────────────────────────────────────

@anycubic_api_bp.route("/status", methods=["GET"])
def api_printer_status():
    cfg = _get_anycubic_params()
    if not cfg["enabled"]:
        return jsonify({"success": False, "message": "Anycubic integration is disabled."}), 400

    status = get_printer_status(cfg["api_type"], cfg["ip"], cfg["port"], cfg["api_key"])
    return jsonify({"success": True, "status": status})


# ── Ingest ────────────────────────────────────────────────────────────────────

@anycubic_api_bp.route("/ingest", methods=["POST"])
def api_ingest_print_job():
    """
    Create an Entry for a finished print job and populate all mapped custom columns.

    Body:
      {
        "file_name": "benchy.gcode",
        "duration_seconds": 3600,
        "filament_used_mm": 1234.5,
        "notes": "...",
        "entry_type_id": 3,           // optional override
        "status_snapshot": { ... }    // full status dict (passed by poll_and_ingest)
      }
    """
    data = request.get_json() or {}
    cfg  = _get_anycubic_params()

    entry_type_id = data.get("entry_type_id") or cfg.get("entry_type_id")
    if not entry_type_id:
        return jsonify({"success": False,
                        "message": "No entry type configured. Set it in Anycubic settings."}), 400

    file_name       = (data.get("file_name") or "Unnamed Print").strip()
    duration_sec    = int(data.get("duration_seconds") or 0)
    filament_mm     = float(data.get("filament_used_mm") or 0)
    notes_text      = data.get("notes", "")
    printer_model   = data.get("printer_model") or get_system_parameters().get("anycubic_printer_model", "")
    status_snapshot = data.get("status_snapshot") or {}
    fetch_file      = bool(data.get("fetch_file", False))

    # Build merged status for field mapping
    merged_status = {
        "file_name":          file_name,
        "elapsed_time":       duration_sec,
        "elapsed_formatted":  format_duration(duration_sec),
        "filament_used_mm":   filament_mm,
        "filament_used_m":    round(filament_mm / 1000, 3),
        "filament_used_g":    round(filament_mm * 0.00292, 2),
        "printer_model":      printer_model,
    }
    merged_status.update(status_snapshot)

    conn   = get_db()
    cursor = conn.cursor()
    now    = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        "INSERT INTO Entry (title, description, entry_type_id, created_at, status) VALUES (?, ?, ?, ?, ?)",
        (file_name, f"Print job ingested from Anycubic printer ({printer_model}).",
         int(entry_type_id), now, "active"),
    )
    entry_id = cursor.lastrowid

    # Write mapped printer fields -> custom column values
    _apply_field_mapping(entry_id, merged_status, cfg["field_mapping"], conn)

    # Human-readable note
    note_lines = [f"**File:** {file_name}"]
    if printer_model:
        note_lines.append(f"**Printer:** {printer_model}")
    if duration_sec:
        note_lines.append(f"**Duration:** {format_duration(duration_sec)}")
    if filament_mm:
        note_lines.append(
            f"**Filament used:** {filament_mm:.1f} mm "
            f"({filament_mm / 1000:.2f} m / ~{filament_mm * 0.00292:.1f} g)"
        )
    if status_snapshot.get("layer_total"):
        note_lines.append(
            f"**Layers:** {status_snapshot.get('layer_current', '?')} / {status_snapshot['layer_total']}"
        )
    if status_snapshot.get("hotend_temp"):
        note_lines.append(
            f"**Temps:** Hotend {status_snapshot['hotend_temp']}°C, "
            f"Bed {status_snapshot.get('bed_temp', '?')}°C"
        )
    if notes_text:
        note_lines.append(f"\n{notes_text}")

    cursor.execute(
        "INSERT INTO Note (entry_id, note_title, note_text, type, created_at, file_paths) VALUES (?, ?, ?, ?, ?, ?)",
        (entry_id, "Print Job Details", "\n".join(note_lines), "General", now, ""),
    )
    note_id = cursor.lastrowid

    # Optionally download the .gcode file and attach it to the note
    attached_file = None
    if fetch_file and cfg.get("ip") and file_name:
        try:
            file_bytes, safe_name = download_print_file(
                cfg["api_type"], cfg["ip"], cfg["port"], cfg["api_key"], file_name
            )
            upload_dir = current_app.config.get("UPLOAD_FOLDER", "uploads")
            os.makedirs(upload_dir, exist_ok=True)
            dest_name = f"note_{note_id}_{safe_name}"
            dest_path = os.path.join(upload_dir, dest_name)
            with open(dest_path, "wb") as fh:
                fh.write(file_bytes)
            rel_path = f"uploads/{dest_name}"
            cursor.execute("UPDATE Note SET file_paths = ? WHERE id = ?", (rel_path, note_id))
            attached_file = rel_path
            logger.info("Attached gcode file %s to Note #%s", rel_path, note_id)
        except Exception as exc:
            logger.warning("Could not download gcode file '%s': %s", file_name, exc)

    conn.commit()

    logger.info("Anycubic print job ingested as Entry #%s: %s", entry_id, file_name)
    return jsonify({
        "success": True,
        "entry_id": entry_id,
        "attached_file": attached_file,
        "message": f"Print job '{file_name}' saved as entry #{entry_id}.",
    })


# ── Poll and auto-ingest ──────────────────────────────────────────────────────

@anycubic_api_bp.route("/poll_and_ingest", methods=["POST"])
def api_poll_and_ingest():
    """Poll printer; if print just completed, create entry with all mapped fields."""
    cfg = _get_anycubic_params()
    if not cfg["enabled"]:
        return jsonify({"success": False, "message": "Anycubic integration is disabled."}), 400

    status = get_printer_status(cfg["api_type"], cfg["ip"], cfg["port"], cfg["api_key"])

    if status.get("state") not in ("complete", "finished"):
        return jsonify({
            "success": True,
            "action": "none",
            "message": f"Printer state is '{status.get('state')}' — no completed print to ingest.",
            "status": status,
        })

    if not cfg["auto_create_entries"] or not cfg["entry_type_id"]:
        return jsonify({
            "success": True,
            "action": "skipped",
            "message": "Completed print detected but auto-create entries is disabled.",
            "status": status,
        })

    with current_app.test_request_context(
        "/api/anycubic/ingest", method="POST",
        json={
            "file_name":        status.get("file_name", "Unnamed Print"),
            "duration_seconds": status.get("elapsed_time", 0),
            "filament_used_mm": status.get("filament_used_mm", 0),
            "entry_type_id":    cfg["entry_type_id"],
            "printer_model":    status.get("printer_model", ""),
            "status_snapshot":  status,
            "fetch_file":       cfg.get("fetch_file", False),
        },
    ):
        resp = api_ingest_print_job()

    resp_data = resp.get_json() if hasattr(resp, "get_json") else {}
    return jsonify({"success": True, "action": "ingested", "entry": resp_data, "status": status})
