# template_app/app/api/system_params_api.py
from flask import Blueprint, request, jsonify, g, current_app
import sqlite3
import logging
from ..db import get_system_parameters # Import the helper function
from ..utils.sensor_type_manager import get_sensor_types_from_device_data

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

@system_params_api_bp.route('/system_params', methods=['GET'])
def api_get_system_params():
    return jsonify(get_system_parameters())

@system_params_api_bp.route('/system_params/<param_name>', methods=['GET'])
def api_get_single_param(param_name):
    """Get a single system parameter by name"""
    try:
        params = get_system_parameters()
        if param_name in params:
            return jsonify({'value': params[param_name]}), 200
        else:
            # Return empty structure for custom_note_types if it doesn't exist yet
            if param_name == 'custom_note_types':
                return jsonify({'value': '{"custom_types":[],"default_prompts":{}}'}), 200
            return jsonify({'error': 'Parameter not found'}), 404
    except Exception as e:
        logger.error(f"Error fetching parameter {param_name}: {e}", exc_info=True)
        return jsonify({'error': 'An internal error occurred.'}), 500

@system_params_api_bp.route('/system_params', methods=['POST', 'PATCH'])
def api_update_system_params():
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    updated_count = 0
    ai_params_updated = False
    
    try:
        # Allowed parameter prefixes/names
        allowed_params = [
            # Core UI/system params
            'project_name', 'entry_singular_label', 'entry_plural_label', 'project_subtitle', 'enable_sensors', 'enable_sensor_master_control', 'enable_kanban', 'sensor_types', 
            # Git integration settings
            'git_integration_enabled', 'git_provider', 'git_token', 'gitlab_url',
            # Strava integration settings
            'strava_enabled', 'strava_client_id', 'strava_client_secret', 'strava_refresh_token', 'strava_activity_mapping',
            'project_logo_path', 'label_font_size', 'label_include_qr_code', 'label_include_logo',
            'label_qr_code_prefix', 'allowed_file_types', 'max_file_size', 'custom_note_types',
            'gemini_api_key', 'groq_api_key', 'huggingface_api_key',
            'gemini_model_name', 'groq_model_name', 'huggingface_model', 'huggingface_image_size',
            'gemini_base_prompt',
            'prompt_description', 'prompt_note', 'prompt_sql', 'prompt_theme', 'prompt_chat', 'prompt_diagram', 'prompt_diagram_rules', 'prompt_summary',
            'default_search_term', 'default_type_filter', 'default_status_filter', 
            'default_date_range', 'default_sort_by', 'default_content_display', 'default_result_limit'
        ]
        
        for param_name, param_value in data.items():
            # Track if AI-related parameters are being updated
            if param_name in ['gemini_api_key', 'groq_api_key', 'huggingface_api_key',
                             'gemini_model_name', 'groq_model_name', 'huggingface_model', 'huggingface_image_size',
                             'gemini_base_prompt', 
                             'prompt_description', 'prompt_note', 'prompt_sql', 'prompt_theme', 'prompt_chat', 'prompt_diagram', 'prompt_diagram_rules', 'prompt_summary']:
                ai_params_updated = True
            
            # Allow any parameter in the whitelist OR any parameter starting with 'label_'
            if param_name in allowed_params or param_name.startswith('label_'):
                cursor.execute(
                    "UPDATE SystemParameters SET parameter_value = ? WHERE parameter_name = ?",
                    (param_value, param_name)
                )
                if cursor.rowcount > 0:
                    updated_count += 1
                else:
                    # If parameter doesn't exist, insert it
                    cursor.execute(
                        "INSERT INTO SystemParameters (parameter_name, parameter_value) VALUES (?, ?)",
                        (param_name, param_value)
                    )
                    updated_count += 1
        conn.commit()
        
        # If AI parameters were updated, reconfigure the AI services
        if ai_params_updated:
            try:
                from app.services.ai_service import get_ai_service
                ai_service = get_ai_service()
                ai_service.reconfigure()
                logger.info("AI service reconfigured after parameter update")
            except Exception as e:
                logger.warning(f"Could not reconfigure AI service: {e}")
            
            # Also reconfigure image service if Hugging Face params were updated
            try:
                from app.services.image_service import get_image_service
                image_service = get_image_service()
                image_service.reconfigure()
                logger.info("Image service reconfigured after parameter update")
            except Exception as e:
                logger.warning(f"Could not reconfigure image service: {e}")
        
        return jsonify({'message': f'{updated_count} parameters updated successfully!'}), 200
    except Exception as e:
        logger.error(f"Error updating system parameters: {e}", exc_info=True)
        conn.rollback()
        return jsonify({'error': 'An internal error occurred.'}), 500

@system_params_api_bp.route('/system_params/preview_device_sensors', methods=['POST'])
def preview_device_sensors():
    """Preview what sensor types would be discovered from device data"""
    try:
        data = request.json
        device_data = data.get('device_data', {})
        
        if not device_data:
            return jsonify({'error': 'device_data is required'}), 400
        
        discovered_types = get_sensor_types_from_device_data(device_data)
        
        return jsonify({
            'discovered_sensor_types': discovered_types,
            'count': len(discovered_types)
        })
        
    except Exception as e:
        logger.error(f"Error previewing device sensors: {e}", exc_info=True)
        return jsonify({'error': 'Failed to preview device sensors'}), 500