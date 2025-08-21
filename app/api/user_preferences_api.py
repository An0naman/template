# template_app/app/api/user_preferences_api.py
from flask import Blueprint, request, jsonify, g, current_app
import sqlite3
import json
import logging
from datetime import datetime
from ..db import get_user_preference, set_user_preference, get_all_user_preferences

# Define a Blueprint for User Preferences API
user_preferences_api_bp = Blueprint('user_preferences_api', __name__)

# Get a logger for this module
logger = logging.getLogger(__name__)

def get_db():
    if 'db' not in g:
        db_path = current_app.config['DATABASE_PATH']
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
    return g.db

@user_preferences_api_bp.route('/user_preferences', methods=['GET'])
def api_get_all_user_preferences():
    """Get all user preferences"""
    try:
        preferences = get_all_user_preferences()
        return jsonify({
            'success': True,
            'preferences': preferences
        })
    except Exception as e:
        logger.error(f"Error getting all user preferences: {e}")
        return jsonify({
            'success': False,
            'message': f'Error getting preferences: {str(e)}'
        }), 500

@user_preferences_api_bp.route('/user_preferences/<preference_name>', methods=['GET'])
def api_get_user_preference(preference_name):
    """Get a specific user preference"""
    try:
        default_value = request.args.get('default')
        preference_value = get_user_preference(preference_name, default_value)
        
        return jsonify({
            'success': True,
            'preference_name': preference_name,
            'preference_value': preference_value
        })
    except Exception as e:
        logger.error(f"Error getting user preference {preference_name}: {e}")
        return jsonify({
            'success': False,
            'message': f'Error getting preference: {str(e)}'
        }), 500

@user_preferences_api_bp.route('/user_preferences/<preference_name>', methods=['POST', 'PUT'])
def api_set_user_preference(preference_name):
    """Set a specific user preference"""
    try:
        data = request.json
        if not data or 'value' not in data:
            return jsonify({
                'success': False,
                'message': 'Missing "value" in request body'
            }), 400
        
        preference_value = data['value']
        
        # If the value is a dict or list, convert to JSON string
        if isinstance(preference_value, (dict, list)):
            preference_value = json.dumps(preference_value)
        
        success = set_user_preference(preference_name, preference_value)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Preference {preference_name} saved successfully',
                'preference_name': preference_name,
                'preference_value': preference_value
            })
        else:
            return jsonify({
                'success': False,
                'message': f'Failed to save preference {preference_name}'
            }), 500
            
    except Exception as e:
        logger.error(f"Error setting user preference {preference_name}: {e}")
        return jsonify({
            'success': False,
            'message': f'Error setting preference: {str(e)}'
        }), 500

@user_preferences_api_bp.route('/user_preferences/chart/<entry_id>', methods=['GET'])
def api_get_chart_preferences(entry_id):
    """Get chart preferences for a specific entry"""
    try:
        preference_name = f'chart_preferences_entry_{entry_id}'
        preference_value = get_user_preference(preference_name)
        
        if preference_value:
            try:
                # Try to parse as JSON
                preferences = json.loads(preference_value)
            except json.JSONDecodeError:
                preferences = {}
        else:
            # Return default preferences
            preferences = {
                'chartType': 'line',
                'sensorType': 'all',
                'timeRange': 'all',
                'dataLimit': 'all'
            }
        
        return jsonify({
            'success': True,
            'preferences': preferences
        })
        
    except Exception as e:
        logger.error(f"Error getting chart preferences for entry {entry_id}: {e}")
        return jsonify({
            'success': False,
            'message': f'Error getting chart preferences: {str(e)}'
        }), 500

@user_preferences_api_bp.route('/user_preferences/chart/<entry_id>', methods=['POST', 'PUT'])
def api_set_chart_preferences(entry_id):
    """Set chart preferences for a specific entry"""
    try:
        data = request.json
        if not data:
            return jsonify({
                'success': False,
                'message': 'Missing preferences in request body'
            }), 400
        
        preference_name = f'chart_preferences_entry_{entry_id}'
        
        # Add timestamp
        preferences = dict(data)
        preferences['savedAt'] = datetime.utcnow().isoformat() + 'Z'
        
        preference_value = json.dumps(preferences)
        success = set_user_preference(preference_name, preference_value)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Chart preferences for entry {entry_id} saved successfully',
                'preferences': preferences
            })
        else:
            return jsonify({
                'success': False,
                'message': f'Failed to save chart preferences for entry {entry_id}'
            }), 500
            
    except Exception as e:
        logger.error(f"Error setting chart preferences for entry {entry_id}: {e}")
        return jsonify({
            'success': False,
            'message': f'Error setting chart preferences: {str(e)}'
        }), 500

@user_preferences_api_bp.route('/user_preferences/chart/<entry_id>', methods=['DELETE'])
def api_delete_chart_preferences(entry_id):
    """Delete chart preferences for a specific entry"""
    try:
        preference_name = f'chart_preferences_entry_{entry_id}'
        
        # We'll set it to an empty string to effectively delete it
        success = set_user_preference(preference_name, '')
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Chart preferences for entry {entry_id} deleted successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': f'Failed to delete chart preferences for entry {entry_id}'
            }), 500
            
    except Exception as e:
        logger.error(f"Error deleting chart preferences for entry {entry_id}: {e}")
        return jsonify({
            'success': False,
            'message': f'Error deleting chart preferences: {str(e)}'
        }), 500
