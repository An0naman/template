# template_app/app/api/cron_api.py
from flask import Blueprint, request, jsonify, g, current_app
import subprocess
import os
import logging
import sqlite3
from tempfile import NamedTemporaryFile

# Define a Blueprint for Cron Management API
cron_api_bp = Blueprint('cron_api', __name__)

# Get a logger for this module
logger = logging.getLogger(__name__)

def get_db():
    if 'db' not in g:
        db_path = current_app.config['DATABASE_PATH']
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
    return g.db

def get_project_root():
    """Get the absolute path to the project root directory"""
    # Check if we're running in Docker (common indicators)
    if os.path.exists('/.dockerenv') or os.environ.get('DOCKER_ENV') or os.getcwd() == '/app':
        # In Docker, the working directory is /app and that's our project root
        return '/app'
    
    # Try to use Flask's current_app to get the root path
    try:
        if current_app:
            # Get the path from DATABASE_PATH configuration which is already calculated correctly
            db_path = current_app.config.get('DATABASE_PATH', '')
            if db_path:
                # DATABASE_PATH is project_root/template.db, so get the directory
                return os.path.dirname(db_path)
    except:
        pass
    
    # Fallback: calculate from file path (app/api/cron_api.py -> project root)
    # This file is in app/api/, so go up two levels to get to project root
    calculated_root = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    
    # Final fallback to hardcoded path if calculated path doesn't contain expected files
    if not os.path.exists(os.path.join(calculated_root, 'run.py')):
        return '/home/an0naman/Documents/GitHub/template'
    
    return calculated_root

def get_current_crontab():
    """Get the current user's crontab entries"""
    try:
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip().split('\n') if result.stdout.strip() else []
        elif result.returncode == 1 and 'no crontab' in result.stderr:
            # No crontab exists yet - this is normal
            return []
        else:
            # Other error
            logger.error(f"Unexpected crontab error: {result.stderr}")
            return []
    except FileNotFoundError:
        logger.error("crontab command not found")
        return []
    except Exception as e:
        logger.error(f"Error reading crontab: {e}")
        return []

def update_crontab(entries):
    """Update the user's crontab with the given entries"""
    try:
        # Create a temporary file with the crontab entries
        with NamedTemporaryFile(mode='w', delete=False, suffix='.cron') as temp_file:
            for entry in entries:
                if entry.strip():  # Skip empty lines
                    temp_file.write(entry + '\n')
            temp_file_path = temp_file.name
        
        # Install the new crontab
        result = subprocess.run(['crontab', temp_file_path], capture_output=True, text=True)
        
        # Clean up the temporary file
        os.unlink(temp_file_path)
        
        if result.returncode == 0:
            return True, "Crontab updated successfully"
        else:
            return False, f"Failed to update crontab: {result.stderr}"
            
    except FileNotFoundError:
        return False, "crontab command not found. Please install cron/crontab or manually set up the cron job."
    except Exception as e:
        logger.error(f"Error updating crontab: {e}")
        return False, f"Error updating crontab: {str(e)}"

@cron_api_bp.route('/cron/overdue', methods=['POST'])
def manage_overdue_cron():
    """Manage the overdue check scheduled job (using internal scheduler for Docker compatibility)"""
    try:
        data = request.json
        enabled = data.get('enabled', False)
        schedule = data.get('schedule', '0 9 * * *')
        
        # For Docker environments, we use an internal scheduler instead of system cron
        # Update the system parameters to control the internal scheduler
        db = get_db()
        cursor = db.cursor()
        
        # Update the settings
        cursor.execute("""
            INSERT OR REPLACE INTO SystemParameters (parameter_name, parameter_value) 
            VALUES ('overdue_check_enabled', ?)
        """, (str(enabled).lower(),))
        
        cursor.execute("""
            INSERT OR REPLACE INTO SystemParameters (parameter_name, parameter_value) 
            VALUES ('overdue_check_schedule', ?)
        """, (schedule,))
        
        db.commit()
        
        status = "enabled" if enabled else "disabled"
        
        # The internal scheduler will automatically pick up these changes
        response_data = {
            'success': True,
            'message': f'Overdue check scheduled job {status} successfully',
            'enabled': enabled,
            'schedule': schedule if enabled else None,
            'method': 'internal_scheduler',
            'note': 'Using internal Flask scheduler (Docker-compatible)'
        }
        
        logger.info(f"Overdue check scheduled job {status} via internal scheduler")
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Error managing overdue cron job: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Failed to manage scheduled job: {str(e)}'
        }), 500

@cron_api_bp.route('/cron/overdue/status', methods=['GET'])
def get_overdue_cron_status():
    """Get the current status of the overdue check scheduled job (internal scheduler)"""
    try:
        # Get settings from database for internal scheduler
        db = get_db()
        cursor = db.cursor()
        
        # Get enabled status
        cursor.execute("SELECT parameter_value FROM SystemParameters WHERE parameter_name = 'overdue_check_enabled'")
        enabled_row = cursor.fetchone()
        enabled = enabled_row and enabled_row['parameter_value'].lower() == 'true'
        
        # Get schedule
        cursor.execute("SELECT parameter_value FROM SystemParameters WHERE parameter_name = 'overdue_check_schedule'")
        schedule_row = cursor.fetchone()
        schedule = schedule_row['parameter_value'] if schedule_row else '0 9 * * *'
        
        return jsonify({
            'enabled': enabled,
            'schedule': schedule if enabled else None,
            'method': 'internal_scheduler',
            'note': 'Using internal Flask scheduler (Docker-compatible)'
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting scheduled job status: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Failed to get scheduled job status: {str(e)}'
        }), 500
