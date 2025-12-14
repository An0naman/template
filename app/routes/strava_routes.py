from flask import Blueprint, request, redirect, url_for, current_app, flash, jsonify
import requests
import time
import logging
import json
from ..db import get_connection
from ..services.strava_service import sync_strava_activities

strava_routes_bp = Blueprint('strava_routes', __name__)
logger = logging.getLogger(__name__)

def get_system_param(conn, param_name):
    cursor = conn.cursor()
    cursor.execute("SELECT parameter_value FROM SystemParameters WHERE parameter_name = ?", (param_name,))
    row = cursor.fetchone()
    return row['parameter_value'] if row else None

def set_system_param(conn, param_name, param_value):
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO SystemParameters (parameter_name, parameter_value) VALUES (?, ?)", (param_name, param_value))
    conn.commit()

@strava_routes_bp.route('/strava/login')
def strava_login():
    conn = get_connection()
    client_id = get_system_param(conn, 'strava_client_id')
    
    if not client_id:
        flash('Strava Client ID is missing. Please configure it in settings.', 'error')
        return redirect(url_for('main.settings'))
    
    redirect_uri = url_for('strava_routes.strava_callback', _external=True)
    logger.info(f"Generated Strava Redirect URI: {redirect_uri}")
    scope = 'read,activity:read_all'
    
    strava_auth_url = (
        f"https://www.strava.com/oauth/authorize?"
        f"client_id={client_id}&"
        f"response_type=code&"
        f"redirect_uri={redirect_uri}&"
        f"approval_prompt=force&"
        f"scope={scope}"
    )
    
    return redirect(strava_auth_url)

@strava_routes_bp.route('/strava/callback')
def strava_callback():
    code = request.args.get('code')
    error = request.args.get('error')
    
    if error:
        flash(f'Strava authorization failed: {error}', 'error')
        return redirect(url_for('main.settings'))
    
    if not code:
        flash('No code received from Strava.', 'error')
        return redirect(url_for('main.settings'))
        
    conn = get_connection()
    client_id = get_system_param(conn, 'strava_client_id')
    client_secret = get_system_param(conn, 'strava_client_secret')
    
    if not client_id or not client_secret:
        flash('Strava Client ID or Secret is missing.', 'error')
        return redirect(url_for('main.settings'))
        
    # Exchange code for tokens
    token_url = 'https://www.strava.com/oauth/token'
    payload = {
        'client_id': client_id,
        'client_secret': client_secret,
        'code': code,
        'grant_type': 'authorization_code'
    }
    
    try:
        response = requests.post(token_url, data=payload)
        response.raise_for_status()
        data = response.json()
        
        access_token = data.get('access_token')
        refresh_token = data.get('refresh_token')
        expires_at = data.get('expires_at')
        athlete = data.get('athlete', {})
        athlete_id = athlete.get('id')
        athlete_firstname = athlete.get('firstname')
        athlete_lastname = athlete.get('lastname')
        
        # Save to DB
        set_system_param(conn, 'strava_access_token', access_token)
        set_system_param(conn, 'strava_refresh_token', refresh_token)
        set_system_param(conn, 'strava_token_expires_at', str(expires_at))
        set_system_param(conn, 'strava_athlete_id', str(athlete_id))
        set_system_param(conn, 'strava_athlete_name', f"{athlete_firstname} {athlete_lastname}")
        
        flash('Successfully connected to Strava!', 'success')
        
    except requests.exceptions.RequestException as e:
        flash(f'Failed to exchange token: {str(e)}', 'error')
        
    return redirect(url_for('main.settings'))

@strava_routes_bp.route('/strava/disconnect', methods=['POST'])
def strava_disconnect():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Clear Strava tokens
    params_to_clear = [
        'strava_access_token', 
        'strava_refresh_token', 
        'strava_token_expires_at', 
        'strava_athlete_id', 
        'strava_athlete_name',
        'strava_last_sync_time'
    ]
    
    for param in params_to_clear:
        cursor.execute("DELETE FROM SystemParameters WHERE parameter_name = ?", (param,))
        
    conn.commit()
    flash('Disconnected from Strava.', 'success')
    return redirect(url_for('main.settings'))

def refresh_strava_token(conn):
    client_id = get_system_param(conn, 'strava_client_id')
    client_secret = get_system_param(conn, 'strava_client_secret')
    refresh_token = get_system_param(conn, 'strava_refresh_token')
    
    if not all([client_id, client_secret, refresh_token]):
        return None
        
    token_url = 'https://www.strava.com/oauth/token'
    payload = {
        'client_id': client_id,
        'client_secret': client_secret,
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token'
    }
    
    try:
        response = requests.post(token_url, data=payload)
        response.raise_for_status()
        data = response.json()
        
        access_token = data.get('access_token')
        new_refresh_token = data.get('refresh_token')
        expires_at = data.get('expires_at')
        
        set_system_param(conn, 'strava_access_token', access_token)
        set_system_param(conn, 'strava_refresh_token', new_refresh_token)
        set_system_param(conn, 'strava_token_expires_at', str(expires_at))
        
        return access_token
    except Exception as e:
        logger.error(f"Failed to refresh Strava token: {e}")
        return None

def get_valid_access_token(conn):
    expires_at = get_system_param(conn, 'strava_token_expires_at')
    if not expires_at:
        return None
        
    # Check if expired (add a 5-minute buffer)
    if int(expires_at) < time.time() + 300:
        logger.info("Strava token expired or expiring soon, refreshing...")
        return refresh_strava_token(conn)
        
    return get_system_param(conn, 'strava_access_token')

@strava_routes_bp.route('/strava/sync', methods=['POST'])
def strava_sync():
    try:
        result = sync_strava_activities()
        if result['status'] == 'success':
            flash(result['message'], 'success')
        elif result['status'] == 'skipped':
            flash(result['message'], 'warning')
        else:
            flash(result['message'], 'error')
            
        return jsonify(result)
    except Exception as e:
        logger.error(f"Sync route error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
