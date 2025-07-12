# template_app/app/api/system_params_api.py
from flask import Blueprint, request, jsonify, g, current_app
import sqlite3
import logging
from ..db import get_system_parameters # Import the helper function

# Define a Blueprint for System Parameters API
system_params_api_bp = Blueprint('system_params_api', __name__)

# Get a logger for this module
logger = logging.getLogger(__name__)

def get_db():
    if 'db' not in g:
        db_path = current_app.config['DATABASE_PATH']
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
    return g.db

@system_params_api_bp.route('/system_parameters', methods=['GET'])
def api_get_system_parameters():
    return jsonify(get_system_parameters())

@system_params_api_bp.route('/system_parameters', methods=['PATCH'])
def api_update_system_parameters():
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    updated_count = 0
    try:
        for param_name, param_value in data.items():
            if param_name in ['project_name', 'entry_singular_label', 'entry_plural_label']:
                cursor.execute(
                    "UPDATE SystemParameters SET parameter_value = ? WHERE parameter_name = ?",
                    (param_value, param_name)
                )
                if cursor.rowcount > 0:
                    updated_count += 1
                else:
                    # If parameter doesn't exist, insert it (should ideally be handled by init_db/get_system_parameters)
                    # but kept for robustness.
                    cursor.execute(
                        "INSERT INTO SystemParameters (parameter_name, parameter_value) VALUES (?, ?)",
                        (param_name, param_value)
                    )
                    updated_count += 1
        conn.commit()
        return jsonify({'message': f'{updated_count} parameters updated successfully!'}), 200
    except Exception as e:
        logger.error(f"Error updating system parameters: {e}", exc_info=True)
        conn.rollback()
        return jsonify({'error': 'An internal error occurred.'}), 500