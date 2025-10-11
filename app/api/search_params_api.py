# template_app/app/api/search_params_api.py
from flask import Blueprint, request, jsonify, g, current_app
import sqlite3
import logging
from ..db import get_system_parameters

# Define a Blueprint for Search Parameters API
search_params_api_bp = Blueprint('search_params_api', __name__)

# Get a logger for this module
logger = logging.getLogger(__name__)

def get_db():
    if 'db' not in g:
        db_path = current_app.config['DATABASE_PATH']
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
    return g.db

@search_params_api_bp.route('/search_defaults', methods=['GET'])
def get_search_defaults():
    """Get the current default search parameters"""
    try:
        params = get_system_parameters()
        
        search_defaults = {
            'search_term': params.get('default_search_term', ''),
            'type_filter': params.get('default_type_filter', ''),
            'status_filter': params.get('default_status_filter', ''),
            'specific_states': params.get('default_specific_states', ''),
            'date_range': params.get('default_date_range', ''),
            'sort_by': params.get('default_sort_by', 'created_desc'),
            'content_display': params.get('default_content_display', ''),
            'result_limit': params.get('default_result_limit', '50')
        }
        
        return jsonify(search_defaults), 200
        
    except Exception as e:
        logger.error(f"Error getting search defaults: {e}", exc_info=True)
        return jsonify({'error': 'Failed to get search defaults'}), 500

@search_params_api_bp.route('/search_defaults', methods=['POST'])
def save_search_defaults():
    """Save new default search parameters"""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        updated_count = 0
        
        # Map frontend parameter names to database parameter names
        param_mapping = {
            'search_term': 'default_search_term',
            'type_filter': 'default_type_filter', 
            'status_filter': 'default_status_filter',
            'specific_states': 'default_specific_states',
            'date_range': 'default_date_range',
            'sort_by': 'default_sort_by',
            'content_display': 'default_content_display',
            'result_limit': 'default_result_limit'
        }
        
        for frontend_name, db_name in param_mapping.items():
            if frontend_name in data:
                param_value = data[frontend_name]
                
                cursor.execute(
                    "UPDATE SystemParameters SET parameter_value = ? WHERE parameter_name = ?",
                    (param_value, db_name)
                )
                
                if cursor.rowcount > 0:
                    updated_count += 1
                else:
                    # If parameter doesn't exist, insert it
                    cursor.execute(
                        "INSERT INTO SystemParameters (parameter_name, parameter_value) VALUES (?, ?)",
                        (db_name, param_value)
                    )
                    updated_count += 1
        
        conn.commit()
        
        logger.info(f"Updated {updated_count} search default parameters")
        return jsonify({
            'message': f'Search defaults saved successfully!',
            'updated_count': updated_count
        }), 200
        
    except Exception as e:
        logger.error(f"Error saving search defaults: {e}", exc_info=True)
        return jsonify({'error': 'Failed to save search defaults'}), 500
