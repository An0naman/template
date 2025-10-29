# app/api/health_api.py
from flask import Blueprint, jsonify
import os
import sqlite3
from datetime import datetime

health_api_bp = Blueprint('health_api', __name__)

@health_api_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for container orchestration and monitoring.
    Returns 200 if app is healthy, 503 if not.
    """
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'checks': {}
    }
    
    overall_healthy = True
    
    # Check 1: Database connectivity
    try:
        from app.config import DATABASE_PATH
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        health_status['checks']['database'] = 'ok'
    except Exception as e:
        health_status['checks']['database'] = f'error: {str(e)}'
        overall_healthy = False
    
    # Check 2: Data directory writable
    try:
        from app.config import DATABASE_PATH
        data_dir = os.path.dirname(DATABASE_PATH)
        test_file = os.path.join(data_dir, '.health_check')
        with open(test_file, 'w') as f:
            f.write('ok')
        os.remove(test_file)
        health_status['checks']['data_directory'] = 'ok'
    except Exception as e:
        health_status['checks']['data_directory'] = f'error: {str(e)}'
        overall_healthy = False
    
    # Check 3: Upload directory writable
    try:
        from app.config import UPLOAD_FOLDER
        test_file = os.path.join(UPLOAD_FOLDER, '.health_check')
        with open(test_file, 'w') as f:
            f.write('ok')
        os.remove(test_file)
        health_status['checks']['upload_directory'] = 'ok'
    except Exception as e:
        health_status['checks']['upload_directory'] = f'error: {str(e)}'
        overall_healthy = False
    
    # Add version information
    try:
        version_file = '/app/VERSION'
        if os.path.exists(version_file):
            with open(version_file, 'r') as f:
                health_status['version'] = f.read().strip()
    except:
        pass
    
    try:
        revision_file = '/app/REVISION'
        if os.path.exists(revision_file):
            with open(revision_file, 'r') as f:
                health_status['revision'] = f.read().strip()
    except:
        pass
    
    # Set overall status
    if not overall_healthy:
        health_status['status'] = 'unhealthy'
        return jsonify(health_status), 503
    
    return jsonify(health_status), 200

@health_api_bp.route('/version', methods=['GET'])
def version_info():
    """
    Returns version information about the running framework.
    """
    version_data = {
        'framework': 'Template CMS',
        'version': 'unknown',
        'revision': 'unknown',
        'build_date': 'unknown'
    }
    
    # Read version files created during Docker build
    version_files = {
        'version': '/app/VERSION',
        'revision': '/app/REVISION',
        'build_date': '/app/BUILD_DATE'
    }
    
    for key, filepath in version_files.items():
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    version_data[key] = f.read().strip()
        except:
            pass
    
    return jsonify(version_data), 200
