# ntfy_api.py - API endpoints for ntfy configuration and testing
from flask import Blueprint, request, jsonify, g, current_app
import sqlite3
import logging
from ..services.ntfy_service import NtfyService, send_app_notification_via_ntfy

# Define a Blueprint for ntfy API
ntfy_api_bp = Blueprint('ntfy_api', __name__)

# Get a logger for this module
logger = logging.getLogger(__name__)

def get_db():
    if 'db' not in g:
        db_path = current_app.config['DATABASE_PATH']
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
    return g.db

@ntfy_api_bp.route('/ntfy/test', methods=['POST'])
def test_ntfy_notification():
    """Test ntfy notification sending"""
    data = request.json
    
    # Get ntfy configuration from database
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT parameter_name, parameter_value FROM SystemParameters WHERE parameter_name IN ('ntfy_server_url', 'ntfy_topic', 'ntfy_auth_token')")
    params = dict(cursor.fetchall())
    
    server_url = data.get('server_url') or params.get('ntfy_server_url', 'https://ntfy.sh')
    topic = data.get('topic') or params.get('ntfy_topic')
    auth_token = data.get('auth_token') or params.get('ntfy_auth_token')
    
    if not topic:
        return jsonify({'error': 'ntfy topic is required'}), 400
    
    # Create test notification
    title = data.get('title', 'Test Notification')
    message = data.get('message', 'This is a test notification from your app!')
    priority = data.get('priority', 3)
    
    try:
        ntfy_service = NtfyService(
            server_url=server_url,
            topic=topic,
            auth_token=auth_token
        )
        
        success, response_text = ntfy_service.send_notification(
            title=title,
            message=message,
            priority=priority,
            tags=['📱', 'test']
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Test notification sent successfully!',
                'response': response_text
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': response_text
            }), 400
            
    except Exception as e:
        logger.error(f"Error testing ntfy notification: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Failed to send test notification: {str(e)}'
        }), 500

@ntfy_api_bp.route('/ntfy/config', methods=['GET'])
def get_ntfy_config():
    """Get current ntfy configuration (without sensitive data)"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Get ntfy configuration from database
    cursor.execute("SELECT parameter_name, parameter_value FROM SystemParameters WHERE parameter_name IN ('ntfy_server_url', 'ntfy_topic', 'ntfy_auth_token')")
    params = dict(cursor.fetchall())
    
    config = {
        'server_url': params.get('ntfy_server_url', 'https://ntfy.sh'),
        'topic': params.get('ntfy_topic'),
        'has_auth_token': bool(params.get('ntfy_auth_token')),
        'enabled': bool(params.get('ntfy_topic'))
    }
    logger.info(f"ntfy config requested: {config}")
    return jsonify(config), 200

@ntfy_api_bp.route('/ntfy/config', methods=['POST'])
def update_ntfy_config():
    """Update ntfy configuration"""
    data = request.json
    
    # Validate required fields
    topic = data.get('topic', '').strip()
    if not topic:
        return jsonify({'error': 'Topic is required'}), 400
    
    server_url = data.get('server_url', 'https://ntfy.sh').strip()
    auth_token = data.get('auth_token', '').strip()
    
    # Save to database for persistence
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Update or insert ntfy parameters
        params = [
            ('ntfy_server_url', server_url),
            ('ntfy_topic', topic),
            ('ntfy_auth_token', auth_token if auth_token else '')
        ]
        
        for param_name, param_value in params:
            cursor.execute(
                "UPDATE SystemParameters SET parameter_value = ? WHERE parameter_name = ?",
                (param_value, param_name)
            )
            if cursor.rowcount == 0:
                # Parameter doesn't exist, insert it
                cursor.execute(
                    "INSERT INTO SystemParameters (parameter_name, parameter_value) VALUES (?, ?)",
                    (param_name, param_value)
                )
        
        conn.commit()
        logger.info(f"ntfy configuration saved to database: topic={topic}, server_url={server_url}")
        
        return jsonify({
            'message': 'ntfy configuration updated successfully!',
            'config': {
                'server_url': server_url,
                'topic': topic,
                'has_auth_token': bool(auth_token)
            }
        }), 200
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error saving ntfy configuration: {e}")
        return jsonify({'error': 'Failed to save configuration'}), 500

@ntfy_api_bp.route('/ntfy/send', methods=['POST'])
def send_custom_notification():
    """Send a custom notification via ntfy"""
    data = request.json
    
    # Validate required fields
    title = data.get('title', '').strip()
    message = data.get('message', '').strip()
    
    if not title or not message:
        return jsonify({'error': 'Title and message are required'}), 400
    
    # Optional parameters
    priority_map = {
        'low': 2,
        'medium': 3,
        'high': 4,
        'critical': 5
    }
    priority = priority_map.get(data.get('priority', 'medium'), 3)
    tags = data.get('tags', ['📱'])
    
    try:
        # Get app base URL for click actions
        app_base_url = request.host_url.rstrip('/')
        
        ntfy_service = NtfyService.from_database()
        success, response_text = ntfy_service.send_notification(
            title=title,
            message=message,
            priority=priority,
            tags=tags,
            click_url=app_base_url
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Notification sent successfully!',
                'response': response_text
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': response_text
            }), 400
            
    except Exception as e:
        logger.error(f"Error sending custom ntfy notification: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Failed to send notification: {str(e)}'
        }), 500
