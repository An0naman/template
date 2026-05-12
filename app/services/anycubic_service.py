"""
Anycubic 3D Printer Service
Handles communication with Anycubic printers via local network APIs.

Supported API types:
  - kobra2_local : Anycubic Kobra 2 / Kobra Neo / Kobra Plus / Kobra Max series
                   local HTTP API on port 80.
  - moonraker    : Klipper / Moonraker-based firmware (Kobra 3, Kobra S1, custom builds).
  - octoprint    : OctoPrint REST API (any printer running OctoPrint).
  - manual       : No automatic polling; data entered manually via the UI.
"""

import logging
import requests

logger = logging.getLogger(__name__)

# ── Timeout used for all outbound printer requests ──────────────────────────
REQUEST_TIMEOUT = 5  # seconds

# ── Field registry ────────────────────────────────────────────────────────────
# Canonical list of every field this service can return.
# Used by the UI to build the field-mapping table (printer field → custom column).
# column_type mirrors CustomColumn.column_type values so the UI can auto-create columns.
PRINTER_FIELDS = [
    # ── Print job ──────────────────────────────────────────────────────────
    {"key": "file_name",          "label": "File / Model Name",             "column_type": "text",   "group": "Print Job",    "unit": ""},
    {"key": "progress",           "label": "Progress",                      "column_type": "number", "group": "Print Job",    "unit": "%"},
    {"key": "elapsed_time",       "label": "Elapsed Time",                  "column_type": "number", "group": "Print Job",    "unit": "s"},
    {"key": "elapsed_formatted",  "label": "Elapsed Time (formatted)",      "column_type": "text",   "group": "Print Job",    "unit": ""},
    {"key": "remaining_time",     "label": "Remaining Time",                "column_type": "number", "group": "Print Job",    "unit": "s"},
    {"key": "remaining_formatted","label": "Remaining Time (formatted)",    "column_type": "text",   "group": "Print Job",    "unit": ""},
    {"key": "layer_current",      "label": "Current Layer",                 "column_type": "number", "group": "Print Job",    "unit": ""},
    {"key": "layer_total",        "label": "Total Layers",                  "column_type": "number", "group": "Print Job",    "unit": ""},
    {"key": "filament_used_mm",   "label": "Filament Used",                 "column_type": "number", "group": "Print Job",    "unit": "mm"},
    {"key": "filament_used_m",    "label": "Filament Used",                 "column_type": "number", "group": "Print Job",    "unit": "m"},
    {"key": "filament_used_g",    "label": "Filament Used (~1.75mm PLA)",   "column_type": "number", "group": "Print Job",    "unit": "g"},
    # ── Temperatures ───────────────────────────────────────────────────────
    {"key": "hotend_temp",        "label": "Hotend Temperature",            "column_type": "number", "group": "Temperatures", "unit": "°C"},
    {"key": "hotend_target",      "label": "Hotend Target Temperature",     "column_type": "number", "group": "Temperatures", "unit": "°C"},
    {"key": "bed_temp",           "label": "Bed Temperature",               "column_type": "number", "group": "Temperatures", "unit": "°C"},
    {"key": "bed_target",         "label": "Bed Target Temperature",        "column_type": "number", "group": "Temperatures", "unit": "°C"},
    {"key": "chamber_temp",       "label": "Chamber Temperature",           "column_type": "number", "group": "Temperatures", "unit": "°C"},
    {"key": "chamber_target",     "label": "Chamber Target Temperature",    "column_type": "number", "group": "Temperatures", "unit": "°C"},
    # ── Motion / speeds ────────────────────────────────────────────────────
    {"key": "print_speed_pct",    "label": "Print Speed",                   "column_type": "number", "group": "Motion",       "unit": "%"},
    {"key": "flow_rate_pct",      "label": "Flow Rate",                     "column_type": "number", "group": "Motion",       "unit": "%"},
    {"key": "fan_speed_pct",      "label": "Part Cooling Fan Speed",        "column_type": "number", "group": "Motion",       "unit": "%"},
    {"key": "pos_x",              "label": "Toolhead X Position",           "column_type": "number", "group": "Motion",       "unit": "mm"},
    {"key": "pos_y",              "label": "Toolhead Y Position",           "column_type": "number", "group": "Motion",       "unit": "mm"},
    {"key": "pos_z",              "label": "Toolhead Z Position",           "column_type": "number", "group": "Motion",       "unit": "mm"},
    # ── Printer info ───────────────────────────────────────────────────────
    {"key": "state",              "label": "Printer State",                 "column_type": "text",   "group": "Printer Info", "unit": ""},
    {"key": "printer_model",      "label": "Printer Model",                 "column_type": "text",   "group": "Printer Info", "unit": ""},
    {"key": "firmware_version",   "label": "Firmware Version",              "column_type": "text",   "group": "Printer Info", "unit": ""},
]


# ── Kobra 2 / Kobra Neo / Kobra Plus / Kobra Max ────────────────────────────

def _kobra2_status(ip: str, port: str) -> dict:
    """
    Poll a Kobra 2-series printer.
    Returns a normalised status dict (see _normalise_status).
    """
    base = f"http://{ip}:{port}"
    status = {}

    # --- printer info ---
    try:
        r = requests.get(f"{base}/machine/system_info", timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        info = r.json()
        status["printer_model"] = info.get("model", "")
        status["firmware_version"] = info.get("firmware_version", "")
    except Exception as exc:
        logger.warning("Kobra2 system_info failed: %s", exc)

    # --- current state ---
    try:
        r = requests.get(f"{base}/machine/state", timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        state_data = r.json()
        status["state"] = state_data.get("state", "unknown")
    except Exception as exc:
        logger.warning("Kobra2 state failed: %s", exc)
        status["state"] = "unknown"

    # --- print job info ---
    try:
        r = requests.get(f"{base}/machine/info", timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        machine = r.json()
        status["file_name"] = machine.get("filename", "")
        status["progress"] = machine.get("progress", 0)
        status["elapsed_time"] = machine.get("print_time", 0)
        status["remaining_time"] = machine.get("time_remaining", 0)
        status["layer_current"] = machine.get("current_layer", 0)
        status["layer_total"] = machine.get("total_layers", 0)
        status["print_speed_pct"] = machine.get("print_speed", 100)
        status["flow_rate_pct"] = machine.get("flow_rate", 100)
        fil_mm = machine.get("filament_used", 0)
        status["filament_used_mm"] = fil_mm
        status["filament_used_m"] = round(fil_mm / 1000, 3) if fil_mm else 0
        # ~1.75mm PLA density ≈ 1.24 g/cm³ → πr²×L×ρ, simplified: mm * 0.00292
        status["filament_used_g"] = round(fil_mm * 0.00292, 2) if fil_mm else 0
    except Exception as exc:
        logger.warning("Kobra2 machine/info failed: %s", exc)

    # --- temperatures ---
    try:
        r = requests.get(f"{base}/machine/temperature", timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        temps = r.json()
        status["hotend_temp"] = temps.get("nozzle_temp", 0)
        status["hotend_target"] = temps.get("nozzle_target", 0)
        status["bed_temp"] = temps.get("bed_temp", 0)
        status["bed_target"] = temps.get("bed_target", 0)
        status["chamber_temp"] = temps.get("chamber_temp", 0)
        status["chamber_target"] = temps.get("chamber_target", 0)
    except Exception as exc:
        logger.warning("Kobra2 temperature failed: %s", exc)

    # --- fan speed ---
    try:
        r = requests.get(f"{base}/machine/fan", timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        fan = r.json()
        status["fan_speed_pct"] = round(fan.get("speed", 0) * 100, 1)
    except Exception:
        pass

    return _normalise_status(status)


# ── Moonraker / Klipper ──────────────────────────────────────────────────────

def _moonraker_status(ip: str, port: str) -> dict:
    """
    Poll a Moonraker-equipped printer (Klipper firmware).
    https://moonraker.readthedocs.io/en/latest/web_api/
    """
    base = f"http://{ip}:{port}"
    status = {}

    # --- combined object query ---
    try:
        r = requests.get(
            f"{base}/printer/objects/query",
            params={
                "print_stats": None,
                "extruder": None,
                "heater_bed": None,
                "heater_chamber": None,
                "toolhead": None,
                "fan": None,
                "gcode_move": None,
                "virtual_sdcard": None,
                "display_status": None,
            },
            timeout=REQUEST_TIMEOUT,
        )
        r.raise_for_status()
        obj = r.json().get("result", {}).get("status", {})

        # print stats
        ps = obj.get("print_stats", {})
        status["state"] = ps.get("state", "unknown")
        status["file_name"] = ps.get("filename", "")
        status["elapsed_time"] = ps.get("print_duration", 0)
        status["layer_current"] = ps.get("info", {}).get("current_layer") or 0
        status["layer_total"] = ps.get("info", {}).get("total_layer") or 0
        fil_mm = ps.get("filament_used", 0)
        status["filament_used_mm"] = round(fil_mm, 2) if fil_mm else 0
        status["filament_used_m"] = round(fil_mm / 1000, 3) if fil_mm else 0
        status["filament_used_g"] = round(fil_mm * 0.00292, 2) if fil_mm else 0

        # temperatures
        ext = obj.get("extruder", {})
        status["hotend_temp"] = round(ext.get("temperature", 0), 1)
        status["hotend_target"] = round(ext.get("target", 0), 1)

        bed = obj.get("heater_bed", {})
        status["bed_temp"] = round(bed.get("temperature", 0), 1)
        status["bed_target"] = round(bed.get("target", 0), 1)

        chamber = obj.get("heater_chamber", {})
        status["chamber_temp"] = round(chamber.get("temperature", 0), 1)
        status["chamber_target"] = round(chamber.get("target", 0), 1)

        # fan
        fan = obj.get("fan", {})
        status["fan_speed_pct"] = round((fan.get("speed", 0) or 0) * 100, 1)

        # toolhead position
        th = obj.get("toolhead", {})
        pos = th.get("position", [0, 0, 0, 0])
        status["pos_x"] = round(pos[0], 2) if len(pos) > 0 else 0
        status["pos_y"] = round(pos[1], 2) if len(pos) > 1 else 0
        status["pos_z"] = round(pos[2], 2) if len(pos) > 2 else 0

        # gcode move — speed factor & extrude factor
        gm = obj.get("gcode_move", {})
        status["print_speed_pct"] = round((gm.get("speed_factor", 1.0) or 1.0) * 100, 1)
        status["flow_rate_pct"] = round((gm.get("extrude_factor", 1.0) or 1.0) * 100, 1)

        # progress via virtual_sdcard
        vsd = obj.get("virtual_sdcard", {})
        status["progress"] = round((vsd.get("progress", 0) or 0) * 100, 1)

    except Exception as exc:
        logger.warning("Moonraker combined query failed: %s", exc)
        status["state"] = "unreachable"

    # --- printer info ---
    try:
        r = requests.get(f"{base}/printer/info", timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        info = r.json().get("result", {})
        status["firmware_version"] = info.get("software_version", "")
        status["printer_model"] = info.get("hostname", "")
    except Exception:
        pass

    return _normalise_status(status)


# ── OctoPrint ────────────────────────────────────────────────────────────────

def _octoprint_status(ip: str, port: str, api_key: str) -> dict:
    """
    Poll an OctoPrint instance.
    https://docs.octoprint.org/en/master/api/
    """
    base = f"http://{ip}:{port}"
    headers = {"X-Api-Key": api_key} if api_key else {}
    status = {}

    try:
        r = requests.get(f"{base}/api/printer", headers=headers, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        data = r.json()

        temps = data.get("temperature", {})
        tool = temps.get("tool0", {})
        bed = temps.get("bed", {})
        chamber = temps.get("chamber", {})
        status["hotend_temp"] = round(tool.get("actual", 0), 1)
        status["hotend_target"] = round(tool.get("target", 0), 1)
        status["bed_temp"] = round(bed.get("actual", 0), 1)
        status["bed_target"] = round(bed.get("target", 0), 1)
        status["chamber_temp"] = round(chamber.get("actual", 0), 1)
        status["chamber_target"] = round(chamber.get("target", 0), 1)

        printer_state = data.get("state", {}).get("text", "unknown").lower()
        state_map = {
            "printing": "printing",
            "paused": "paused",
            "operational": "idle",
            "error": "error",
            "cancelling": "paused",
            "finishing": "printing",
        }
        status["state"] = state_map.get(printer_state, printer_state)

    except Exception as exc:
        logger.warning("OctoPrint /api/printer failed: %s", exc)
        status["state"] = "unreachable"

    try:
        r = requests.get(f"{base}/api/job", headers=headers, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        job = r.json()
        status["file_name"] = (job.get("job", {}).get("file", {}).get("name") or "")
        progress = job.get("progress", {})
        status["progress"] = round((progress.get("completion") or 0), 1)
        status["elapsed_time"] = progress.get("printTime") or 0
        status["remaining_time"] = progress.get("printTimeLeft") or 0
        # OctoPrint reports filament in mm³ per tool; convert to mm length (1.75mm dia)
        fil_info = job.get("job", {}).get("filament", {})
        fil_mm3 = sum(t.get("length", 0) or 0 for t in fil_info.values()) if isinstance(fil_info, dict) else 0
        status["filament_used_mm"] = round(fil_mm3, 2)
        status["filament_used_m"] = round(fil_mm3 / 1000, 3)
        status["filament_used_g"] = round(fil_mm3 * 0.00292, 2)
    except Exception as exc:
        logger.warning("OctoPrint /api/job failed: %s", exc)

    try:
        r = requests.get(f"{base}/api/printer/command", headers=headers, timeout=REQUEST_TIMEOUT)
        # Fan / speed not directly exposed in OctoPrint REST without plugins; leave as 0
    except Exception:
        pass

    try:
        r = requests.get(f"{base}/api/version", headers=headers, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        ver = r.json()
        status["firmware_version"] = ver.get("server", "")
    except Exception:
        pass

    return _normalise_status(status)


# ── Normalisation helper ─────────────────────────────────────────────────────

def _normalise_status(raw: dict) -> dict:
    """
    Ensure every key expected by the UI / field registry is present.
    """
    elapsed = int(raw.get("elapsed_time") or 0)
    remaining = int(raw.get("remaining_time") or 0)
    fil_mm = raw.get("filament_used_mm", 0) or 0
    return {
        # print job
        "state":              raw.get("state", "unknown"),
        "file_name":          raw.get("file_name", ""),
        "progress":           raw.get("progress", 0),
        "elapsed_time":       elapsed,
        "elapsed_formatted":  format_duration(elapsed),
        "remaining_time":     remaining,
        "remaining_formatted": format_duration(remaining),
        "layer_current":      raw.get("layer_current", 0),
        "layer_total":        raw.get("layer_total", 0),
        "filament_used_mm":   round(float(fil_mm), 2),
        "filament_used_m":    raw.get("filament_used_m", round(fil_mm / 1000, 3)),
        "filament_used_g":    raw.get("filament_used_g", round(fil_mm * 0.00292, 2)),
        # temperatures
        "hotend_temp":        raw.get("hotend_temp", 0),
        "hotend_target":      raw.get("hotend_target", 0),
        "bed_temp":           raw.get("bed_temp", 0),
        "bed_target":         raw.get("bed_target", 0),
        "chamber_temp":       raw.get("chamber_temp", 0),
        "chamber_target":     raw.get("chamber_target", 0),
        # motion
        "print_speed_pct":    raw.get("print_speed_pct", 100),
        "flow_rate_pct":      raw.get("flow_rate_pct", 100),
        "fan_speed_pct":      raw.get("fan_speed_pct", 0),
        "pos_x":              raw.get("pos_x", 0),
        "pos_y":              raw.get("pos_y", 0),
        "pos_z":              raw.get("pos_z", 0),
        # printer info
        "printer_model":      raw.get("printer_model", ""),
        "firmware_version":   raw.get("firmware_version", ""),
    }


# ── Public API ───────────────────────────────────────────────────────────────

def get_printer_status(api_type: str, ip: str, port: str = "80", api_key: str = "") -> dict:
    """
    Fetch the current printer status and return a normalised dict.

    Returns a dict with keys:
      state, printer_model, firmware_version, file_name, progress,
      elapsed_time, remaining_time, layer_current, layer_total,
      hotend_temp, hotend_target, bed_temp, bed_target

    On any hard failure the dict will still contain all keys with safe defaults
    and state == 'unreachable'.
    """
    if not ip:
        return _normalise_status({"state": "not_configured"})

    try:
        if api_type == "kobra2_local":
            return _kobra2_status(ip, port)
        elif api_type == "moonraker":
            return _moonraker_status(ip, port)
        elif api_type == "octoprint":
            return _octoprint_status(ip, port, api_key)
        else:
            return _normalise_status({"state": "manual"})
    except Exception as exc:
        logger.error("Unexpected error polling printer: %s", exc, exc_info=True)
        return _normalise_status({"state": "unreachable"})


def download_print_file(
    api_type: str, ip: str, port: str, api_key: str, file_name: str
) -> tuple:
    """
    Download the .gcode file from the printer.

    Returns (bytes_content, suggested_filename) or raises an exception on failure.

    Per-API endpoints:
      Moonraker  : GET /server/files/gcodes/{filename}
      OctoPrint  : GET /downloads/files/local/{filename}
      Kobra2     : GET /sdcard/{filename}  (common on ACME/Kobra2 series)
    """
    if not ip or not file_name:
        raise ValueError("IP and file_name are required.")

    # Sanitise: strip directory components the printer might include
    safe_name = file_name.split("/")[-1].split("\\")[-1]
    if not safe_name:
        raise ValueError("Invalid file name.")

    headers = {}
    if api_type == "moonraker":
        import urllib.parse
        url = f"http://{ip}:{port}/server/files/gcodes/{urllib.parse.quote(safe_name)}"
    elif api_type == "octoprint":
        import urllib.parse
        url = f"http://{ip}:{port}/downloads/files/local/{urllib.parse.quote(safe_name)}"
        if api_key:
            headers["X-Api-Key"] = api_key
    elif api_type == "kobra2_local":
        import urllib.parse
        url = f"http://{ip}:{port}/sdcard/{urllib.parse.quote(safe_name)}"
    else:
        raise ValueError(f"File download not supported for api_type '{api_type}'.")

    r = requests.get(url, headers=headers, timeout=30, stream=True)
    r.raise_for_status()
    return r.content, safe_name


def test_connection(api_type: str, ip: str, port: str = "80", api_key: str = "") -> dict:
    """
    Quick connectivity test. Returns {'success': bool, 'message': str}.
    """
    if not ip:
        return {"success": False, "message": "No IP address configured."}

    status = get_printer_status(api_type, ip, port, api_key)
    if status["state"] in ("unreachable", "not_configured"):
        return {"success": False, "message": f"Could not reach printer at {ip}:{port}. Check IP, port, and printer power."}
    return {"success": True, "message": f"Connected. Printer state: {status['state']}"}


def format_duration(seconds: int) -> str:
    """Convert seconds to a human-readable h:mm:ss string."""
    if not seconds:
        return "0:00:00"
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h}:{m:02d}:{s:02d}"
