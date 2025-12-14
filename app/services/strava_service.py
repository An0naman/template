import requests
import time
import json
import logging
from datetime import datetime
from ..db import get_connection

logger = logging.getLogger(__name__)

STRAVA_AUTH_URL = "https://www.strava.com/oauth/token"
STRAVA_API_URL = "https://www.strava.com/api/v3"

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
    params = {'per_page': 30}
    if last_sync:
        params['after'] = last_sync

    try:
        response = requests.get(f"{STRAVA_API_URL}/athlete/activities", headers=headers, params=params)
        
        # If unauthorized, refresh and retry (in case expires_at check failed or wasn't present)
        if response.status_code == 401:
            logger.info("Strava request unauthorized, refreshing token...")
            access_token = refresh_access_token(conn, client_id, client_secret, refresh_token)
            if not access_token:
                return {"status": "error", "message": "Failed to refresh Strava token"}
            headers = {'Authorization': f"Bearer {access_token}"}
            response = requests.get(f"{STRAVA_API_URL}/athlete/activities", headers=headers, params=params)

        response.raise_for_status()
        activities = response.json()
    except Exception as e:
        logger.error(f"Strava API Error: {e}")
        return {"status": "error", "message": f"Strava API Error: {str(e)}"}
    
    if not activities:
        # Update last sync timestamp even if no activities, so we don't query old range again
        set_system_param(conn, 'strava_last_sync_timestamp', int(time.time()))
        return {"status": "success", "message": "No new activities found", "count": 0}

    # 4. Process Activities
    # Get Mappings
    mapping_json = get_system_param(conn, 'strava_activity_mapping')
    mapping = {}
    if mapping_json:
        try:
            # Handle potential single quotes from Python dict string representation
            if mapping_json.startswith('{') and "'" in mapping_json:
                 mapping_json = mapping_json.replace("'", '"')
            mapping = json.loads(mapping_json)
        except Exception as e:
            logger.error(f"Error parsing Strava mapping: {e}")
            pass
            
    count = 0
    cursor = conn.cursor()
    
    for activity in activities:
        strava_id = str(activity['id'])
        strava_type = activity['type']
        name = activity['name']
        start_date = activity['start_date_local'] # ISO format: 2018-02-16T06:52:54Z
        distance_meters = activity.get('distance', 0)
        moving_time_seconds = activity.get('moving_time', 0)
        
        # Convert date to YYYY-MM-DD
        try:
            date_obj = datetime.strptime(start_date, "%Y-%m-%dT%H:%M:%SZ")
            date_str = date_obj.strftime("%Y-%m-%d")
        except ValueError:
             # Fallback if format is different
             date_str = start_date.split('T')[0]
        
        # Determine Entry Type
        entry_type_id = mapping.get(strava_type)
        if not entry_type_id:
            entry_type_id = mapping.get('default') # Check for lowercase 'default'
            
        if not entry_type_id:
            logger.info(f"Skipping Strava activity {strava_id} ({strava_type}): No mapping found")
            continue

        # Check for duplicate
        # We'll check if an entry with this title and date exists.
        # Ideally we should have an external_id column.
        # For now, let's check title + date + entry_type
        cursor.execute("SELECT 1 FROM Entry WHERE title = ? AND created_at LIKE ? AND entry_type_id = ?", (name, f"{date_str}%", entry_type_id))
        if cursor.fetchone():
            logger.info(f"Skipping Strava activity {strava_id}: Duplicate found")
            continue

        # Format Details
        distance_km = distance_meters / 1000
        moving_time_min = moving_time_seconds / 60
        
        details = f"""Strava Activity: {strava_type}
Distance: {distance_km:.2f} km
Time: {moving_time_min:.0f} min
Link: https://www.strava.com/activities/{strava_id}
"""
        
        # Insert Entry
        try:
            cursor.execute("""
                INSERT INTO Entry (title, description, created_at, entry_type_id, status)
                VALUES (?, ?, ?, ?, 'Completed')
            """, (name, details, date_str, entry_type_id))
            count += 1
        except Exception as e:
            logger.error(f"Error inserting entry for Strava activity {strava_id}: {e}")

    # Update last sync timestamp
    set_system_param(conn, 'strava_last_sync_timestamp', int(time.time()))
    conn.commit()
    
    return {"status": "success", "message": f"Synced {count} activities", "count": count}
