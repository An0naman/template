import requests
import time
import json
import logging
from datetime import datetime, timezone
from ..db import get_connection

logger = logging.getLogger(__name__)

STRAVA_AUTH_URL = "https://www.strava.com/oauth/token"
STRAVA_API_URL  = "https://www.strava.com/api/v3"

# ── Field registry ────────────────────────────────────────────────────────────
# Each entry maps a key in the Strava activity dict (or computed field) to a
# CustomColumn definition.  These are used for auto-create and field mapping.
STRAVA_FIELDS = [
    # Core activity info
    {"key": "name",                  "label": "Activity Name",        "column_type": "text",   "group": "Activity",  "unit": ""},
    {"key": "sport_type",            "label": "Sport Type",           "column_type": "text",   "group": "Activity",  "unit": ""},
    {"key": "start_date_local",      "label": "Start Date (Local)",   "column_type": "text",   "group": "Activity",  "unit": ""},
    {"key": "description",           "label": "Description",          "column_type": "textarea","group": "Activity", "unit": ""},
    # Distance & time
    {"key": "distance_km",           "label": "Distance",             "column_type": "number", "group": "Distance & Time", "unit": "km"},
    {"key": "moving_time_min",       "label": "Moving Time",          "column_type": "number", "group": "Distance & Time", "unit": "min"},
    {"key": "elapsed_time_min",      "label": "Elapsed Time",         "column_type": "number", "group": "Distance & Time", "unit": "min"},
    {"key": "total_elevation_gain",  "label": "Elevation Gain",       "column_type": "number", "group": "Distance & Time", "unit": "m"},
    # Speed
    {"key": "average_speed_kmh",     "label": "Average Speed",        "column_type": "number", "group": "Speed",     "unit": "km/h"},
    {"key": "max_speed_kmh",         "label": "Max Speed",            "column_type": "number", "group": "Speed",     "unit": "km/h"},
    # Heart rate
    {"key": "average_heartrate",     "label": "Average Heart Rate",   "column_type": "number", "group": "Heart Rate","unit": "bpm"},
    {"key": "max_heartrate",         "label": "Max Heart Rate",       "column_type": "number", "group": "Heart Rate","unit": "bpm"},
    # Power (cycling)
    {"key": "average_watts",         "label": "Average Power",        "column_type": "number", "group": "Power",     "unit": "W"},
    {"key": "max_watts",             "label": "Max Power",            "column_type": "number", "group": "Power",     "unit": "W"},
    {"key": "kilojoules",            "label": "Energy (kJ)",          "column_type": "number", "group": "Power",     "unit": "kJ"},
    # Cadence
    {"key": "average_cadence",       "label": "Average Cadence",      "column_type": "number", "group": "Cadence",   "unit": "rpm"},
    # Calories & effort
    {"key": "calories",              "label": "Calories",             "column_type": "number", "group": "Effort",    "unit": "kcal"},
    {"key": "suffer_score",          "label": "Suffer Score",         "column_type": "number", "group": "Effort",    "unit": ""},
    {"key": "average_temp",          "label": "Average Temperature",  "column_type": "number", "group": "Effort",    "unit": "°C"},
    # Social
    {"key": "kudos_count",           "label": "Kudos",                "column_type": "number", "group": "Social",    "unit": ""},
    {"key": "comment_count",         "label": "Comments",             "column_type": "number", "group": "Social",    "unit": ""},
    {"key": "achievement_count",     "label": "Achievements",         "column_type": "number", "group": "Social",    "unit": ""},
    {"key": "pr_count",              "label": "PRs",                  "column_type": "number", "group": "Social",    "unit": ""},
    # Meta
    {"key": "strava_id",             "label": "Strava Activity ID",   "column_type": "text",   "group": "Meta",      "unit": ""},
    {"key": "strava_url",            "label": "Strava URL",           "column_type": "url",    "group": "Meta",      "unit": ""},
    {"key": "gear_id",               "label": "Gear ID",              "column_type": "text",   "group": "Meta",      "unit": ""},
]


def _activity_to_field_dict(activity: dict) -> dict:
    """Flatten a raw Strava activity dict into the keys used in STRAVA_FIELDS."""
    strava_id = str(activity.get("id", ""))
    return {
        "name":                 activity.get("name", ""),
        "sport_type":           activity.get("sport_type") or activity.get("type", ""),
        "start_date_local":     activity.get("start_date_local", ""),
        "description":          activity.get("description") or "",
        "distance_km":          round(activity.get("distance", 0) / 1000, 3),
        "moving_time_min":      round(activity.get("moving_time", 0) / 60, 1),
        "elapsed_time_min":     round(activity.get("elapsed_time", 0) / 60, 1),
        "total_elevation_gain": activity.get("total_elevation_gain", 0),
        "average_speed_kmh":    round(activity.get("average_speed", 0) * 3.6, 2),
        "max_speed_kmh":        round(activity.get("max_speed", 0) * 3.6, 2),
        "average_heartrate":    activity.get("average_heartrate"),
        "max_heartrate":        activity.get("max_heartrate"),
        "average_watts":        activity.get("average_watts"),
        "max_watts":            activity.get("max_watts"),
        "kilojoules":           activity.get("kilojoules"),
        "average_cadence":      activity.get("average_cadence"),
        "calories":             activity.get("calories"),
        "suffer_score":         activity.get("suffer_score"),
        "average_temp":         activity.get("average_temp"),
        "kudos_count":          activity.get("kudos_count", 0),
        "comment_count":        activity.get("comment_count", 0),
        "achievement_count":    activity.get("achievement_count", 0),
        "pr_count":             activity.get("pr_count", 0),
        "strava_id":            strava_id,
        "strava_url":           f"https://www.strava.com/activities/{strava_id}" if strava_id else "",
        "gear_id":              activity.get("gear_id") or "",
    }


def _apply_field_mapping(entry_id: int, field_values: dict, field_mapping: dict, conn) -> None:
    """Write Strava field values into CustomColumnValue rows per the saved mapping."""
    if not field_mapping:
        return
    cursor = conn.cursor()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    for field_key, column_id in field_mapping.items():
        if not column_id:
            continue
        value = field_values.get(field_key)
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
            logger.warning("Strava: failed to write col value (%s -> col %s): %s", field_key, column_id, exc)

def get_system_param(conn, param_name):
    cursor = conn.cursor()
    cursor.execute("SELECT parameter_value FROM SystemParameters WHERE parameter_name = ?", (param_name,))
    row = cursor.fetchone()
    return row['parameter_value'] if row else None

def set_system_param(conn, param_name, param_value):
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO SystemParameters (parameter_name, parameter_value) VALUES (?, ?)", (param_name, param_value))
    conn.commit()

def refresh_access_token(conn, client_id, client_secret, refresh_token):
    payload = {
        'client_id': client_id,
        'client_secret': client_secret,
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token'
    }
    
    try:
        response = requests.post(STRAVA_AUTH_URL, data=payload)
        response.raise_for_status()
        data = response.json()
        
        new_access_token = data['access_token']
        new_refresh_token = data['refresh_token']
        expires_at = data['expires_at']
        
        # Update DB
        set_system_param(conn, 'strava_access_token', new_access_token)
        set_system_param(conn, 'strava_refresh_token', new_refresh_token)
        set_system_param(conn, 'strava_token_expires_at', str(expires_at))
        
        return new_access_token
    except Exception as e:
        logger.error(f"Error refreshing Strava token: {e}")
        return None

def sync_strava_activities():
    conn = get_connection()
    
    # 1. Check if enabled
    enabled = get_system_param(conn, 'strava_enabled')
    if enabled != '1' and enabled != 'true':
        return {"status": "skipped", "message": "Strava integration disabled"}

    # 2. Get Credentials
    client_id = get_system_param(conn, 'strava_client_id')
    client_secret = get_system_param(conn, 'strava_client_secret')
    refresh_token = get_system_param(conn, 'strava_refresh_token')
    access_token = get_system_param(conn, 'strava_access_token')
    
    if not (client_id and client_secret and refresh_token):
        return {"status": "error", "message": "Missing Strava credentials"}

    # 3. Check Token Expiry and Refresh if needed
    expires_at = get_system_param(conn, 'strava_token_expires_at')
    if expires_at:
        try:
            if int(time.time()) > int(expires_at):
                logger.info("Strava token expired, refreshing...")
                access_token = refresh_access_token(conn, client_id, client_secret, refresh_token)
                if not access_token:
                    return {"status": "error", "message": "Failed to refresh Strava token"}
        except ValueError:
            pass # If expires_at is invalid, we'll try the request and handle 401

    headers = {'Authorization': f"Bearer {access_token}"}
    
    # Get last sync time to only fetch new activities
    last_sync = get_system_param(conn, 'strava_last_sync_timestamp')
    base_params = {'per_page': 200}
    if last_sync:
        base_params['after'] = last_sync

    # Paginate through all available activities
    activities = []
    page = 1
    try:
        while True:
            params = {**base_params, 'page': page}
            response = requests.get(f"{STRAVA_API_URL}/athlete/activities", headers=headers, params=params)

            # If unauthorized, refresh and retry once
            if response.status_code == 401:
                logger.info("Strava request unauthorized, refreshing token...")
                access_token = refresh_access_token(conn, client_id, client_secret, refresh_token)
                if not access_token:
                    return {"status": "error", "message": "Failed to refresh Strava token"}
                headers = {'Authorization': f"Bearer {access_token}"}
                response = requests.get(f"{STRAVA_API_URL}/athlete/activities", headers=headers, params=params)

            response.raise_for_status()
            page_activities = response.json()

            if not page_activities:
                break

            activities.extend(page_activities)

            # If fewer results than per_page, we've reached the last page
            if len(page_activities) < base_params['per_page']:
                break

            page += 1
    except Exception as e:
        logger.error(f"Strava API Error: {e}")
        return {"status": "error", "message": f"Strava API Error: {str(e)}"}

    if not activities:
        # Update last sync timestamp even if no activities, so we don't query old range again
        set_system_param(conn, 'strava_last_sync_timestamp', int(time.time()))
        return {"status": "success", "message": "No new activities found", "count": 0}

    # 4. Process Activities
    # Get activity-type → entry-type mapping
    mapping_json = get_system_param(conn, 'strava_activity_mapping')
    mapping = {}
    if mapping_json:
        try:
            if mapping_json.startswith('{') and "'" in mapping_json:
                mapping_json = mapping_json.replace("'", '"')
            mapping = json.loads(mapping_json)
        except Exception as e:
            logger.error(f"Error parsing Strava mapping: {e}")

    # Get field → CustomColumn mapping
    field_mapping_json = get_system_param(conn, 'strava_field_mapping')
    field_mapping = {}
    if field_mapping_json:
        try:
            field_mapping = json.loads(field_mapping_json)
        except Exception as e:
            logger.error(f"Error parsing Strava field mapping: {e}")

    count = 0
    backfilled = 0
    cursor = conn.cursor()

    for activity in activities:
        strava_id = str(activity['id'])
        strava_type = activity.get('sport_type') or activity.get('type', '')
        name = activity['name']
        start_date = activity['start_date_local']  # ISO format: 2018-02-16T06:52:54Z

        # Convert date to YYYY-MM-DD
        try:
            date_obj = datetime.strptime(start_date, "%Y-%m-%dT%H:%M:%SZ")
            date_str = date_obj.strftime("%Y-%m-%d")
        except ValueError:
            date_str = start_date.split('T')[0]

        # Determine Entry Type
        entry_type_id = mapping.get(strava_type) or mapping.get(activity.get('type', ''))
        if not entry_type_id:
            entry_type_id = mapping.get('default')

        if not entry_type_id:
            logger.info(f"Skipping Strava activity {strava_id} ({strava_type}): No mapping found")
            continue

        # Check for duplicate
        cursor.execute("SELECT id FROM Entry WHERE title = ? AND created_at LIKE ? AND entry_type_id = ?",
                       (name, f"{date_str}%", entry_type_id))
        existing_entry = cursor.fetchone()
        if existing_entry:
            logger.info(f"Skipping Strava activity {strava_id}: Duplicate found")

            # Keep mapped Strava custom fields in sync for existing matching entries.
            if field_mapping:
                field_values = _activity_to_field_dict(activity)
                _apply_field_mapping(existing_entry["id"], field_values, field_mapping, conn)
                backfilled += 1
            continue

        # Format Details
        distance_km = activity.get('distance', 0) / 1000
        moving_time_min = activity.get('moving_time', 0) / 60

        details = (f"Strava Activity: {strava_type}\n"
                   f"Distance: {distance_km:.2f} km\n"
                   f"Time: {moving_time_min:.0f} min\n"
                   f"Link: https://www.strava.com/activities/{strava_id}\n")

        # Insert Entry
        try:
            cursor.execute("""
                INSERT INTO Entry (title, description, created_at, entry_type_id, status)
                VALUES (?, ?, ?, ?, 'Completed')
            """, (name, details, date_str, entry_type_id))
            entry_id = cursor.lastrowid
            count += 1

            # Apply field mapping — write custom column values
            if field_mapping and entry_id:
                field_values = _activity_to_field_dict(activity)
                _apply_field_mapping(entry_id, field_values, field_mapping, conn)

        except Exception as e:
            logger.error(f"Error inserting entry for Strava activity {strava_id}: {e}")

    # Update last sync timestamp
    set_system_param(conn, 'strava_last_sync_timestamp', int(time.time()))
    conn.commit()
    
    return {
        "status": "success",
        "message": f"Synced {count} activities, backfilled custom fields for {backfilled} existing activities",
        "count": count,
        "backfilled": backfilled,
    }
