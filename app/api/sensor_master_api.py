# app/api/sensor_master_api.py
"""
Sensor Master Control API
==========================

This API provides endpoints for the Sensor Master Control system, which allows
sensors (like ESP32s) to "phone home" and receive configuration instructions.

Simplified architecture: Sensors connect directly to this instance (no master instances).

Endpoints:
----------
1. POST /api/sensor-master/register - Sensor registration (phone-home)
2. GET /api/sensor-master/config/<sensor_id> - Get sensor configuration
3. POST /api/sensor-master/heartbeat - Sensor heartbeat/status update
4. GET/PATCH /api/sensor-master/sensors - Manage registered sensors
5. GET/POST/PATCH/DELETE /api/sensor-master/configs - Manage configuration templates
6. POST /api/sensor-master/command - Queue commands for sensors
"""

from flask import Blueprint, request, jsonify, g
import sqlite3
import json
import hashlib
import logging
from datetime import datetime, timedelta, timezone
from ..db import get_connection

# Define a Blueprint for Sensor Master Control API
sensor_master_api_bp = Blueprint('sensor_master_api', __name__)

# Get a logger for this module
logger = logging.getLogger(__name__)

def get_db():
    """Get database connection"""
    if 'db' not in g:
        g.db = get_connection()
        g.db.row_factory = sqlite3.Row
    return g.db


def generate_config_hash(config_data):
    """Generate a hash for configuration data to detect changes"""
    config_str = json.dumps(config_data, sort_keys=True)
    return hashlib.sha256(config_str.encode()).hexdigest()


@sensor_master_api_bp.route('/sensor-master/register', methods=['POST'])
def register_sensor():
    """
    Sensor registration endpoint (phone-home)
    
    Expected payload:
    {
        "sensor_id": "esp32_unique_id",
        "sensor_name": "Fermentation Chamber 1",
        "sensor_type": "esp32_fermentation",
        "hardware_info": "ESP32-WROOM-32",
        "firmware_version": "1.0.0",
        "ip_address": "192.168.1.100",
        "mac_address": "AA:BB:CC:DD:EE:FF",
        "capabilities": ["temperature", "relay_control"]
    }
    
    Returns:
    {
        "status": "registered",
        "has_config": true,
        "message": "Sensor registered successfully"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'sensor_id' not in data:
            return jsonify({'error': 'sensor_id is required'}), 400
        
        sensor_id = data['sensor_id']
        sensor_type = data.get('sensor_type', 'unknown')
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if sensor is already registered
        cursor.execute('''
            SELECT id, status 
            FROM SensorRegistration 
            WHERE sensor_id = ?
        ''', (sensor_id,))
        
        existing = cursor.fetchone()
        timestamp = datetime.now(timezone.utc).isoformat()
        
        if existing:
            # Update existing registration
            cursor.execute('''
                UPDATE SensorRegistration
                SET sensor_name = ?,
                    sensor_type = ?,
                    hardware_info = ?,
                    firmware_version = ?,
                    ip_address = ?,
                    mac_address = ?,
                    capabilities = ?,
                    last_check_in = ?,
                    status = ?,
                    updated_at = ?
                WHERE sensor_id = ?
            ''', (
                data.get('sensor_name', 'Unnamed Sensor'),
                sensor_type,
                data.get('hardware_info', ''),
                data.get('firmware_version', ''),
                data.get('ip_address', ''),
                data.get('mac_address', ''),
                json.dumps(data.get('capabilities', [])),
                timestamp,
                'online',
                timestamp,
                sensor_id
            ))
            
            logger.info(f"Updated sensor registration: {sensor_id}")
        else:
            # Create new registration
            cursor.execute('''
                INSERT INTO SensorRegistration
                (sensor_id, sensor_name, sensor_type, hardware_info, firmware_version,
                 ip_address, mac_address, capabilities,
                 last_check_in, status, registration_source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                sensor_id,
                data.get('sensor_name', 'Unnamed Sensor'),
                sensor_type,
                data.get('hardware_info', ''),
                data.get('firmware_version', ''),
                data.get('ip_address', ''),
                data.get('mac_address', ''),
                json.dumps(data.get('capabilities', [])),
                timestamp,
                'online',
                'auto'
            ))
            
            logger.info(f"Registered new sensor: {sensor_id}")
        
        # Check if there's a configuration available
        # SensorMasterConfig table has been removed, so we check if a script is assigned
        # or if we have a new way to store config. For now, we'll assume no config
        # unless we implement a new config storage.
        
        # Check if a script is assigned (this might be what we want to check now)
        cursor.execute('SELECT current_script_id FROM SensorRegistration WHERE sensor_id = ?', (sensor_id,))
        row = cursor.fetchone()
        has_script = row and row['current_script_id'] is not None
        
        # For now, we'll set has_config to False to prevent 500 errors until
        # the new configuration system is fully implemented.
        # If we want to trigger OTA, we might use a different flag.
        has_config = False 
        
        conn.commit()
        
        return jsonify({
            'status': 'registered',
            'has_config': has_config,
            'message': 'Sensor registered successfully',
            'check_in_interval': 60,  # Check back every 1 minute
            'config_endpoint': f'/api/sensor-master/config/{sensor_id}'
        }), 200
        
    except Exception as e:
        logger.error(f"Error registering sensor: {e}", exc_info=True)
        return jsonify({'error': 'Failed to register sensor'}), 500


@sensor_master_api_bp.route('/sensor-master/config/<sensor_id>', methods=['GET'])
def get_sensor_config(sensor_id):
    """
    Get configuration for a specific sensor
    
    Returns:
    {
        "config_available": true,
        "config_hash": "abc123...",
        "config": {
            "polling_interval": 60,
            "data_endpoint": "http://192.168.1.50:5000/api/devices/data",
            "sensor_mappings": [...],
            "linked_entries": [...],
            ...
        },
        "commands": [...]
    }
    """
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get sensor registration
        cursor.execute('''
            SELECT * FROM SensorRegistration
            WHERE sensor_id = ?
        ''', (sensor_id,))
        
        sensor = cursor.fetchone()
        
        if not sensor:
            return jsonify({
                'error': 'Sensor not registered',
                'fallback_mode': True
            }), 404
        
        # Get configuration (sensor-specific first, then type-specific)
        # SensorMasterConfig table has been removed.
        # We return no config for now.
        config_row = None
        
        if not config_row:
            return jsonify({
                'config_available': False,
                'message': 'No configuration defined for this sensor',
                'fallback_mode': True
            }), 200
        
        # Parse configuration
        config_data = json.loads(config_row['config_data'])
        config_hash = generate_config_hash(config_data)
        
        # Check if configuration has changed
        config_changed = sensor['config_hash'] != config_hash
        
        if config_changed:
            # Update sensor's config hash
            cursor.execute('''
                UPDATE SensorRegistration
                SET config_hash = ?, last_config_update = ?
                WHERE sensor_id = ?
            ''', (config_hash, datetime.now(timezone.utc).isoformat(), sensor_id))
        
        # Get any pending commands for this sensor
        cursor.execute('''
            SELECT id, command_type, command_data, priority, created_at
            FROM SensorCommandQueue
            WHERE sensor_id = ? 
            AND status = 'pending'
            AND (expires_at IS NULL OR expires_at > datetime('now'))
            ORDER BY priority ASC, created_at ASC
            LIMIT 10
        ''', (sensor_id,))
        
        commands = [dict(row) for row in cursor.fetchall()]
        
        # Mark commands as delivered
        if commands:
            command_ids = [cmd['id'] for cmd in commands]
            cursor.execute(f'''
                UPDATE SensorCommandQueue
                SET status = 'delivered', attempts = attempts + 1
                WHERE id IN ({','.join('?' * len(command_ids))})
            ''', command_ids)
        
        conn.commit()
        
        response = {
            'config_available': True,
            'config_changed': config_changed,
            'config_hash': config_hash,
            'config_name': config_row['config_name'],
            'config_version': config_row['config_version'],
            'config': config_data,
            'commands': commands,
            'check_in_interval': 60
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error getting sensor config: {e}", exc_info=True)
        return jsonify({'error': 'Failed to get configuration'}), 500


@sensor_master_api_bp.route('/sensor-master/heartbeat', methods=['POST'])
def sensor_heartbeat():
    """
    Sensor heartbeat endpoint
    
    Expected payload:
    {
        "sensor_id": "esp32_unique_id",
        "status": "online",
        "metrics": {
            "uptime": 3600,
            "free_memory": 80000,
            "wifi_rssi": -45
        },
        "command_results": [
            {"command_id": 1, "result": "success", "message": "Command executed"}
        ]
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'sensor_id' not in data:
            return jsonify({'error': 'sensor_id is required'}), 400
        
        sensor_id = data['sensor_id']
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Update sensor last check-in
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Build update query dynamically to include script version if provided
        update_fields = {
            'last_check_in': timestamp,
            'status': data.get('status', 'online'),
            'ip_address': data.get('ip_address', ''),
            'updated_at': timestamp
        }
        
        # If sensor reports current script version, update it
        if 'current_script_version' in data:
            update_fields['current_script_version'] = data['current_script_version']
        
        if 'current_script_id' in data:
            update_fields['current_script_id'] = data['current_script_id']
        
        set_clause = ', '.join([f"{k} = ?" for k in update_fields.keys()])
        values = list(update_fields.values()) + [sensor_id]
        
        cursor.execute(f'''
            UPDATE SensorRegistration
            SET {set_clause}
            WHERE sensor_id = ?
        ''', values)
        
        if cursor.rowcount == 0:
            return jsonify({
                'error': 'Sensor not registered',
                'action': 'register'
            }), 404
            
        # Store telemetry data if metrics are provided
        if 'metrics' in data:
            try:
                cursor.execute('''
                    INSERT INTO SensorTelemetry (sensor_id, data, timestamp)
                    VALUES (?, ?, ?)
                ''', (sensor_id, json.dumps(data['metrics']), timestamp))
            except sqlite3.OperationalError:
                # Table might not exist if migration wasn't run
                logger.warning("SensorTelemetry table not found. Skipping telemetry storage.")

        
        # Process command results if provided
        if 'command_results' in data:
            for result in data['command_results']:
                command_id = result.get('command_id')
                if command_id:
                    cursor.execute('''
                        UPDATE SensorCommandQueue
                        SET status = ?,
                            result = ?,
                            executed_at = ?
                        WHERE id = ? AND sensor_id = ?
                    ''', (
                        result.get('status', 'completed'),
                        json.dumps(result),
                        timestamp,
                        command_id,
                        sensor_id
                    ))
        
        conn.commit()
        
        # Check if there are new commands
        cursor.execute('''
            SELECT COUNT(*) FROM SensorCommandQueue
            WHERE sensor_id = ? AND status = 'pending'
        ''', (sensor_id,))
        
        pending_commands = cursor.fetchone()[0]
        
        return jsonify({
            'status': 'acknowledged',
            'pending_commands': pending_commands,
            'timestamp': timestamp
        }), 200
        
    except Exception as e:
        logger.error(f"Error processing heartbeat: {e}", exc_info=True)
        return jsonify({'error': 'Failed to process heartbeat'}), 500


def calculate_sensor_status(last_check_in, timeout_minutes=10):
    """
    Calculate sensor online/offline status based on last heartbeat
    
    Args:
        last_check_in: ISO timestamp string or None
        timeout_minutes: Number of minutes before considering sensor offline (default: 10)
    
    Returns:
        'online', 'offline', or 'pending'
    """
    if not last_check_in:
        return 'pending'
    
    try:
        # Try to parse ISO format timestamp
        try:
            last_check = datetime.fromisoformat(last_check_in.replace('Z', '+00:00'))
        except ValueError:
            # Try parsing without timezone info
            last_check = datetime.strptime(last_check_in, '%Y-%m-%d %H:%M:%S')
            last_check = last_check.replace(tzinfo=timezone.utc)
        
        now = datetime.now(timezone.utc)
        
        # Make last_check timezone-aware if it isn't
        if last_check.tzinfo is None:
            last_check = last_check.replace(tzinfo=timezone.utc)
        
        time_since_last = (now - last_check).total_seconds() / 60  # minutes
        
        if time_since_last <= timeout_minutes:
            return 'online'
        else:
            return 'offline'
    except Exception as e:
        logger.error(f"Error calculating sensor status: {e}")
        return 'offline'


@sensor_master_api_bp.route('/sensor-master/sensors', methods=['GET'])
def get_registered_sensors():
    """Get all registered sensors with real-time heartbeat status"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Optional filters
        status_filter = request.args.get('status')
        
        query = '''
            SELECT * FROM SensorRegistration
            WHERE 1=1
        '''
        params = []
        
        if status_filter:
            query += ' AND status = ?'
            params.append(status_filter)
        
        query += ' ORDER BY last_check_in DESC'
        
        cursor.execute(query, params)
        sensors = []
        
        for row in cursor.fetchall():
            sensor = dict(row)
            if sensor['capabilities']:
                sensor['capabilities'] = json.loads(sensor['capabilities'])
            
            # Calculate real-time status based on heartbeat
            sensor['status'] = calculate_sensor_status(sensor.get('last_check_in'))
            
            # Get active script for this sensor (what SHOULD be running)
            cursor.execute('''
                SELECT id, description, script_version, script_type, created_at, last_executed
                FROM SensorScripts
                WHERE sensor_id = ? AND is_active = 1
                ORDER BY created_at DESC
                LIMIT 1
            ''', (sensor['sensor_id'],))
            
            script_row = cursor.fetchone()
            if script_row:
                assigned_version = script_row[2]
                running_version = sensor.get('current_script_version')
                
                # Determine script status
                script_status = 'unknown'
                if running_version:
                    if running_version == assigned_version:
                        script_status = 'running'  # Sensor is running the correct version
                    else:
                        script_status = 'outdated'  # Sensor is running old version
                else:
                    script_status = 'pending'  # Sensor hasn't reported version yet
                
                sensor['assigned_script'] = {
                    'id': script_row[0],
                    'name': script_row[1] or 'Unnamed Script',
                    'version': assigned_version,
                    'language': script_row[3],
                    'uploaded_at': script_row[4],
                    'last_executed': script_row[5],
                    'status': script_status
                }
            else:
                sensor['assigned_script'] = None
            
            # Add running script info (what sensor reports it's actually running)
            sensor['running_script_version'] = sensor.get('current_script_version')
            
            sensors.append(sensor)
        
        return jsonify(sensors), 200
        
    except Exception as e:
        logger.error(f"Error fetching sensors: {e}", exc_info=True)
        return jsonify({'error': 'Failed to fetch sensors'}), 500


@sensor_master_api_bp.route('/sensor-master/check-heartbeats', methods=['POST'])
def check_heartbeats():
    """
    Check all sensors and update their status based on heartbeat timeout
    This endpoint can be called periodically to maintain accurate status
    """
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get all sensors
        cursor.execute('SELECT sensor_id, last_check_in, status FROM SensorRegistration')
        sensors = cursor.fetchall()
        
        updated_count = 0
        timestamp = datetime.now(timezone.utc).isoformat();
        
        for sensor in sensors:
            sensor_id = sensor['sensor_id']
            last_check_in = sensor['last_check_in']
            current_status = sensor['status']
            
            # Calculate new status
            new_status = calculate_sensor_status(last_check_in)
            
            # Update if status changed
            if new_status != current_status:
                cursor.execute('''
                    UPDATE SensorRegistration
                    SET status = ?, updated_at = ?
                    WHERE sensor_id = ?
                ''', (new_status, timestamp, sensor_id))
                updated_count += 1
                logger.info(f"Sensor {sensor_id} status changed: {current_status} -> {new_status}")
        
        conn.commit()
        
        return jsonify({
            'message': 'Heartbeat check completed',
            'sensors_checked': len(sensors),
            'sensors_updated': updated_count
        }), 200
        
    except Exception as e:
        logger.error(f"Error checking heartbeats: {e}", exc_info=True)
        return jsonify({'error': 'Failed to check heartbeats'}), 500


@sensor_master_api_bp.route('/sensor-master/sensors/<sensor_id>', methods=['PATCH'])
def update_sensor(sensor_id):
    """Update a registered sensor"""
    try:
        data = request.get_json()
        
        conn = get_db()
        cursor = conn.cursor()
        
        update_fields = []
        values = []
        
        allowed_fields = ['sensor_name', 'assigned_master_id', 'status']
        
        for field in allowed_fields:
            if field in data:
                update_fields.append(f"{field} = ?")
                values.append(data[field])
        
        if not update_fields:
            return jsonify({'error': 'No fields to update'}), 400
        
        values.append(datetime.now(timezone.utc).isoformat())
        values.append(sensor_id)
        
        cursor.execute(f'''
            UPDATE SensorRegistration
            SET {', '.join(update_fields)}, updated_at = ?
            WHERE sensor_id = ?
        ''', values)
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'Sensor not found'}), 404
        
        conn.commit()
        
        return jsonify({'message': 'Sensor updated successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error updating sensor: {e}", exc_info=True)
        return jsonify({'error': 'Failed to update sensor'}), 500


@sensor_master_api_bp.route('/sensor-master/sensors/<sensor_id>', methods=['DELETE'])
def delete_sensor(sensor_id):
    """Delete a registered sensor"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM SensorRegistration WHERE sensor_id = ?', (sensor_id,))
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'Sensor not found'}), 404
        
        conn.commit()
        
        return jsonify({'message': 'Sensor deleted successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error deleting sensor: {e}", exc_info=True)
        return jsonify({'error': 'Failed to delete sensor'}), 500


@sensor_master_api_bp.route('/sensor-master/configs', methods=['GET'])
def get_sensor_configs():
    """Get all sensor configurations"""
    try:
        # SensorMasterConfig table has been removed
        return jsonify([]), 200
        
    except Exception as e:
        logger.error(f"Error fetching configs: {e}", exc_info=True)
        return jsonify({'error': 'Failed to fetch configs'}), 500


@sensor_master_api_bp.route('/sensor-master/configs', methods=['POST'])
def create_sensor_config():
    """Create a new sensor configuration"""
    try:
        data = request.get_json()
        
        required = ['config_name', 'config_data']
        for field in required:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Must specify either sensor_id or sensor_type
        if not data.get('sensor_id') and not data.get('sensor_type'):
            return jsonify({'error': 'Must specify either sensor_id or sensor_type'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # SensorMasterConfig table has been removed
        return jsonify({'error': 'Configuration management is deprecated. Please use Script Library.'}), 410
        
    except Exception as e:
        logger.error(f"Error creating config: {e}", exc_info=True)
        return jsonify({'error': 'Failed to create configuration'}), 500


@sensor_master_api_bp.route('/sensor-master/configs/<int:config_id>', methods=['PATCH'])
def update_sensor_config(config_id):
    """Update a sensor configuration"""
    try:
        # SensorMasterConfig table has been removed
        return jsonify({'error': 'Configuration management is deprecated. Please use Script Library.'}), 410
        
    except Exception as e:
        logger.error(f"Error updating config: {e}", exc_info=True)
        return jsonify({'error': 'Failed to update configuration'}), 500


@sensor_master_api_bp.route('/sensor-master/configs/<int:config_id>', methods=['DELETE'])
def delete_sensor_config(config_id):
    """Delete a sensor configuration"""
    try:
        # SensorMasterConfig table has been removed
        return jsonify({'error': 'Configuration management is deprecated. Please use Script Library.'}), 410
        
    except Exception as e:
        logger.error(f"Error deleting config: {e}", exc_info=True)
        return jsonify({'error': 'Failed to delete configuration'}), 500


@sensor_master_api_bp.route('/sensor-master/command', methods=['POST'])
def queue_sensor_command():
    """Queue a command for a sensor"""
    try:
        data = request.get_json()
        
        required = ['sensor_id', 'command_type']
        for field in required:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if sensor exists
        cursor.execute('SELECT id FROM SensorRegistration WHERE sensor_id = ?', 
                      (data['sensor_id'],))
        if not cursor.fetchone():
            return jsonify({'error': 'Sensor not registered'}), 404
        
        cursor.execute('''
            INSERT INTO SensorCommandQueue
            (sensor_id, command_type, command_data, priority, max_attempts, expires_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            data['sensor_id'],
            data['command_type'],
            json.dumps(data.get('command_data', {})),
            data.get('priority', 100),
            data.get('max_attempts', 3),
            data.get('expires_at')
        ))
        
        command_id = cursor.lastrowid
        conn.commit()
        
        return jsonify({
            'message': 'Command queued successfully',
            'command_id': command_id
        }), 201
        
    except Exception as e:
        logger.error(f"Error queuing command: {e}", exc_info=True)
        return jsonify({'error': 'Failed to queue command'}), 500


@sensor_master_api_bp.route('/sensor-master/commands', methods=['GET'])
def get_sensor_commands():
    """Get command queue for sensors"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        sensor_filter = request.args.get('sensor_id')
        status_filter = request.args.get('status', 'pending')
        
        query = '''
            SELECT scq.*,
                   sr.sensor_name,
                   sr.sensor_type
            FROM SensorCommandQueue scq
            JOIN SensorRegistration sr ON scq.sensor_id = sr.sensor_id
            WHERE 1=1
        '''
        params = []
        
        if sensor_filter:
            query += ' AND scq.sensor_id = ?'
            params.append(sensor_filter)
        
        if status_filter:
            query += ' AND scq.status = ?'
            params.append(status_filter)
        
        query += ' ORDER BY scq.priority ASC, scq.created_at ASC'
        
        cursor.execute(query, params)
        commands = []
        
        for row in cursor.fetchall():
            command = dict(row)
            if command['command_data']:
                command['command_data'] = json.loads(command['command_data'])
            if command['result']:
                command['result'] = json.loads(command['result']);
            commands.append(command)
        
        return jsonify(commands), 200
        
    except Exception as e:
        logger.error(f"Error fetching commands: {e}", exc_info=True)
        return jsonify({'error': 'Failed to fetch commands'}), 500


@sensor_master_api_bp.route('/sensor-master/script/<sensor_id>', methods=['GET'])
def get_sensor_script(sensor_id):
    """
    Get the current script/instructions for a sensor
    
    This endpoint is polled by the ESP32 to check for script updates
    """
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get sensor info and check if it has a script
        cursor.execute('''
            SELECT *
            FROM SensorRegistration
            WHERE sensor_id = ?
        ''', (sensor_id,))
        
        sensor = cursor.fetchone()
        
        if not sensor:
            return jsonify({'error': 'Sensor not found'}), 404
        
        # Check for sensor-specific script
        cursor.execute('''
            SELECT script_content, script_version, script_type, updated_at
            FROM SensorScripts
            WHERE sensor_id = ? AND is_active = 1
            ORDER BY updated_at DESC
            LIMIT 1
        ''', (sensor_id,))
        
        script_row = cursor.fetchone()
        
        if script_row:
            return jsonify({
                'script_available': True,
                'script': script_row['script_content'],
                'version': script_row['script_version'],
                'type': script_row['script_type'],
                'updated_at': script_row['updated_at']
            }), 200
        
        return jsonify({
            'script_available': False,
            'message': 'No script configured for this sensor'
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching sensor script: {e}", exc_info=True)
        return jsonify({'error': 'Failed to fetch script'}), 500


@sensor_master_api_bp.route('/sensor-master/scripts/assign', methods=['POST'])
def assign_script_to_sensor():
    """
    Assign (copy) a script from one sensor to another
    
    Expected payload:
    {
        "source_script_id": 123,
        "target_sensor_id": "esp32_002"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'source_script_id' not in data or 'target_sensor_id' not in data:
            return jsonify({'error': 'source_script_id and target_sensor_id are required'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Verify target sensor exists
        cursor.execute('SELECT id FROM SensorRegistration WHERE sensor_id = ?',
                      (data['target_sensor_id'],))
        if not cursor.fetchone():
            return jsonify({'error': 'Target sensor not registered'}), 404
        
        # Get source script
        cursor.execute('SELECT * FROM SensorScripts WHERE id = ?', (data['source_script_id'],))
        source_script = cursor.fetchone()
        if not source_script:
            return jsonify({'error': 'Source script not found'}), 404
        
        # Deactivate previous scripts for target sensor
        cursor.execute('''
            UPDATE SensorScripts
            SET is_active = 0
            WHERE sensor_id = ?
        ''', (data['target_sensor_id'],))
        
        # Copy script to target sensor
        cursor.execute('''
            INSERT INTO SensorScripts
            (sensor_id, script_content, script_version, script_type, description, is_active)
            VALUES (?, ?, ?, ?, ?, 1)
        ''', (
            data['target_sensor_id'],
            source_script['script_content'],
            source_script['script_version'],
            source_script['script_type'],
            source_script['description']
        ))
        
        new_script_id = cursor.lastrowid
        conn.commit()
        
        logger.info(f"Script {data['source_script_id']} assigned to sensor {data['target_sensor_id']} as script {new_script_id}")
        
        return jsonify({
            'message': 'Script assigned successfully',
            'new_script_id': new_script_id,
            'target_sensor_id': data['target_sensor_id']
        }), 201
        
    except Exception as e:
        logger.error(f"Error assigning script: {e}", exc_info=True)
        return jsonify({'error': 'Failed to assign script'}), 500


@sensor_master_api_bp.route('/sensor-master/script', methods=['POST'])
def upload_sensor_script():
    """
    Upload or update a script for a sensor
    
    Expected payload:
    {
        "sensor_id": "esp32_001",
        "script_content": "// Arduino code here",
        "script_version": "1.0.0",
        "script_type": "arduino",
        "description": "LED control script"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'sensor_id' not in data or 'script_content' not in data:
            return jsonify({'error': 'sensor_id and script_content are required'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Verify sensor exists
        cursor.execute('SELECT id FROM SensorRegistration WHERE sensor_id = ?',
                      (data['sensor_id'],))
        if not cursor.fetchone():
            return jsonify({'error': 'Sensor not registered'}), 404
        
        # Deactivate previous scripts for this sensor
        cursor.execute('''
            UPDATE SensorScripts
            SET is_active = 0
            WHERE sensor_id = ?
        ''', (data['sensor_id'],))
        
        # Insert new script
        cursor.execute('''
            INSERT INTO SensorScripts
            (sensor_id, script_content, script_version, script_type, description, is_active)
            VALUES (?, ?, ?, ?, ?, 1)
        ''', (
            data['sensor_id'],
            data['script_content'],
            data.get('script_version', '1.0.0'),
            data.get('script_type', 'arduino'),
            data.get('description', '')
        ))
        
        script_id = cursor.lastrowid
        conn.commit()
        
        logger.info(f"Script uploaded for sensor {data['sensor_id']}, version {data.get('script_version')}")
        
        return jsonify({
            'message': 'Script uploaded successfully',
            'script_id': script_id,
            'sensor_id': data['sensor_id']
        }), 201
        
    except Exception as e:
        logger.error(f"Error uploading script: {e}", exc_info=True)
        return jsonify({'error': 'Failed to upload script'}), 500


@sensor_master_api_bp.route('/sensor-master/library-script', methods=['POST'])
def create_library_script():
    """
    Create a new script in the library
    
    Expected payload:
    {
        "name": "Standard Blink",
        "script_content": "// Arduino code here",
        "script_version": "1.0.0",
        "script_type": "arduino",
        "description": "Standard LED blink pattern",
        "target_sensor_type": "esp32_fermentation" (optional)
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'name' not in data or 'script_content' not in data:
            return jsonify({'error': 'name and script_content are required'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO ScriptLibrary
            (name, script_content, script_version, script_type, description, target_sensor_type)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            data['name'],
            data['script_content'],
            data.get('script_version', '1.0.0'),
            data.get('script_type', 'arduino'),
            data.get('description', ''),
            data.get('target_sensor_type', '')
        ))
        
        script_id = cursor.lastrowid
        conn.commit()
        
        logger.info(f"Library script created: {data['name']}")
        
        return jsonify({
            'message': 'Script added to library successfully',
            'id': script_id
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating library script: {e}", exc_info=True)
        return jsonify({'error': 'Failed to create library script'}), 500


@sensor_master_api_bp.route('/sensor-master/library-scripts', methods=['GET'])
def list_library_scripts():
    """List all scripts in the library"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM ScriptLibrary
            ORDER BY created_at DESC
        ''')
        
        scripts = [dict(row) for row in cursor.fetchall()]
        
        return jsonify(scripts), 200
        
    except Exception as e:
        logger.error(f"Error listing library scripts: {e}", exc_info=True)
        return jsonify({'error': 'Failed to list library scripts'}), 500


@sensor_master_api_bp.route('/sensor-master/assign-library-script', methods=['POST'])
def assign_library_script():
    """
    Assign a library script to a sensor (copies it to SensorScripts)
    
    Expected payload:
    {
        "library_script_id": 1,
        "sensor_id": "esp32_001"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'library_script_id' not in data or 'sensor_id' not in data:
            return jsonify({'error': 'library_script_id and sensor_id are required'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Get library script
        cursor.execute('SELECT * FROM ScriptLibrary WHERE id = ?', (data['library_script_id'],))
        lib_script = cursor.fetchone()
        
        if not lib_script:
            return jsonify({'error': 'Library script not found'}), 404
            
        # Verify sensor exists
        cursor.execute('SELECT id FROM SensorRegistration WHERE sensor_id = ?', (data['sensor_id'],))
        if not cursor.fetchone():
            return jsonify({'error': 'Sensor not registered'}), 404
            
        # Deactivate previous scripts for this sensor
        cursor.execute('''
            UPDATE SensorScripts
            SET is_active = 0
            WHERE sensor_id = ?
        ''', (data['sensor_id'],))
        
        # Insert new script from library
        cursor.execute('''
            INSERT INTO SensorScripts
            (sensor_id, script_content, script_version, script_type, description, is_active)
            VALUES (?, ?, ?, ?, ?, 1)
        ''', (
            data['sensor_id'],
            lib_script['script_content'],
            lib_script['script_version'],
            lib_script['script_type'],
            lib_script['description']
        ))
        
        new_script_id = cursor.lastrowid
        conn.commit()
        
        logger.info(f"Assigned library script {data['library_script_id']} to sensor {data['sensor_id']}")
        
        return jsonify({
            'message': 'Script assigned successfully',
            'script_id': new_script_id,
            'sensor_id': data['sensor_id']
        }), 201
        
    except Exception as e:
        logger.error(f"Error assigning library script: {e}", exc_info=True)
        return jsonify({'error': 'Failed to assign script'}), 500


@sensor_master_api_bp.route('/sensor-master/scripts', methods=['GET'])
def list_sensor_scripts():
    """Get all scripts for sensors"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        sensor_id = request.args.get('sensor_id')
        
        query = '''
            SELECT ss.*, sr.sensor_name, sr.sensor_type
            FROM SensorScripts ss
            JOIN SensorRegistration sr ON ss.sensor_id = sr.sensor_id
            WHERE 1=1
        '''
        params = []
        
        if sensor_id:
            query += ' AND ss.sensor_id = ?'
            params.append(sensor_id)
        
        query += ' ORDER BY ss.updated_at DESC'
        
        cursor.execute(query, params)
        scripts = []
        
        for row in cursor.fetchall():
            script = dict(row)
            scripts.append(script)
        
        return jsonify(scripts), 200
        
    except Exception as e:
        logger.error(f"Error listing scripts: {e}", exc_info=True)
        return jsonify({'error': 'Failed to list scripts'}), 500


@sensor_master_api_bp.route('/sensor-master/scripts/<int:script_id>', methods=['DELETE'])
def delete_script(script_id):
    """
    Delete a sensor script
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Check if script exists
        cursor.execute('SELECT id FROM SensorScripts WHERE id = ?', (script_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Script not found'}), 404
        
        # Delete the script
        cursor.execute('DELETE FROM SensorScripts WHERE id = ?', (script_id,))
        conn.commit()
        
        logger.info(f"Deleted script {script_id}")
        return jsonify({'message': 'Script deleted successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error deleting script: {e}", exc_info=True)
        return jsonify({'error': 'Failed to delete script'}), 500


@sensor_master_api_bp.route('/sensor-master/scripts/<int:script_id>', methods=['PATCH'])
def update_script_status(script_id):
    """
    Update a sensor script (mainly for activating/deactivating)
    
    Expected payload:
    {
        "is_active": true/false
    }
    """
    try:
        data = request.get_json()
        
        if 'is_active' not in data:
            return jsonify({'error': 'is_active field is required'}), 400
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Check if script exists
        cursor.execute('SELECT sensor_id FROM SensorScripts WHERE id = ?', (script_id,))
        result = cursor.fetchone()
        if not result:
            return jsonify({'error': 'Script not found'}), 404
        
        sensor_id = result['sensor_id']
        is_active = data['is_active']
        
        # If activating, deactivate other scripts for this sensor
        if is_active:
            cursor.execute(
                'UPDATE SensorScripts SET is_active = 0 WHERE sensor_id = ? AND id != ?',
                (sensor_id, script_id)
            )
        
        # Update the script
        cursor.execute(
            'UPDATE SensorScripts SET is_active = ?, updated_at = ? WHERE id = ?',
            (1 if is_active else 0, datetime.now(timezone.utc).isoformat(), script_id)
        )
        conn.commit()
        
        logger.info(f"Updated script {script_id} active status to {is_active}")
        return jsonify({'message': 'Script updated successfully', 'is_active': is_active}), 200
        
    except Exception as e:
        logger.error(f"Error updating script: {e}", exc_info=True)
        return jsonify({'error': 'Failed to update script'}), 500


@sensor_master_api_bp.route('/sensor-master/export-code', methods=['POST'])
def export_esp32_code():
    """
    Export ESP32 firmware code for a sensor
    
    Expected payload:
    {
        "sensor_id": "esp32_001" (optional - if not provided, generates template),
        "sensor_type": "esp32_fermentation" (optional),
        "language": "arduino" or "micropython",
        "wifi_ssid": "MyWiFi",
        "wifi_password": "MyPassword",
        "custom_config": {} (optional)
    }
    
    Returns:
    {
        "success": true,
        "code": "... generated code ...",
        "language": "arduino",
        "sensor_id": "esp32_001",
        "filename": "esp32_001.ino"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        language = data.get('language', 'arduino').lower()
        if language not in ['arduino', 'micropython']:
            return jsonify({'error': 'Language must be "arduino" or "micropython"'}), 400
        
        sensor_id = data.get('sensor_id')
        sensor_type = data.get('sensor_type')
        wifi_ssid = data.get('wifi_ssid', '')
        wifi_password = data.get('wifi_password', '')
        custom_config = data.get('custom_config')
        
        # Import the code generator service
        from ..services.esp32_code_generator import ESP32CodeGenerator
        
        conn = get_db()
        generator = ESP32CodeGenerator(conn)
        
        result = generator.generate_code(
            sensor_id=sensor_id,
            sensor_type=sensor_type,
            language=language,
            wifi_ssid=wifi_ssid,
            wifi_password=wifi_password,
            custom_config=custom_config
        )
        
        if result.get('success'):
            # Determine filename
            sensor_id_str = result.get('sensor_id', 'esp32_sensor')
            if language == 'arduino':
                filename = f"{sensor_id_str}.ino"
            else:
                filename = f"{sensor_id_str}.py"
            
            result['filename'] = filename
            return jsonify(result), 200
        else:
            return jsonify(result), 400
        
    except Exception as e:
        logger.error(f"Error exporting code: {e}", exc_info=True)
        return jsonify({'error': 'Failed to export code', 'details': str(e)}), 500


@sensor_master_api_bp.route('/sensor-master/script-executed', methods=['POST'])
def report_script_execution():
    """
    ESP32 reports that it executed a script
    
    Expected payload:
    {
        "sensor_id": "esp32_fermentation_001",
        "script_id": 123
    }
    """
    try:
        data = request.get_json()
        sensor_id = data.get('sensor_id')
        script_id = data.get('script_id')
        
        if not sensor_id:
            return jsonify({'error': 'sensor_id is required'}), 400
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # If script_id provided, update specific script
        if script_id:
            cursor.execute('''
                SELECT id FROM SensorScripts 
                WHERE id = ? AND sensor_id = ?
            ''', (script_id, sensor_id))
            
            if not cursor.fetchone():
                return jsonify({'error': 'Script not found for this sensor'}), 404
            
            cursor.execute('''
                UPDATE SensorScripts 
                SET last_executed = ? 
                WHERE id = ? AND sensor_id = ?
            ''', (datetime.now(timezone.utc).isoformat(), script_id, sensor_id))
            
            logger.info(f"Script {script_id} executed on {sensor_id}")
        else:
            # Update the active script for this sensor
            cursor.execute('''
                UPDATE SensorScripts 
                SET last_executed = ? 
                WHERE sensor_id = ? AND is_active = 1
            ''', (datetime.now(timezone.utc).isoformat(), sensor_id))
            
            logger.info(f"Active script executed on {sensor_id}")
        
        conn.commit()
        return jsonify({'message': 'Execution reported'}), 200
        
    except Exception as e:
        logger.error(f"Error reporting script execution: {e}", exc_info=True)
        return jsonify({'error': 'Failed to report execution'}), 500


@sensor_master_api_bp.route('/sensor-master/report-version', methods=['POST'])
def report_script_version():
    """
    ESP32 reports which script version is currently running
    
    Expected payload:
    {
        "sensor_id": "esp32_fermentation_001",
        "script_version": "1.0.0",
        "script_id": 123 (optional)
    }
    """
    try:
        data = request.get_json()
        sensor_id = data.get('sensor_id')
        script_version = data.get('script_version')
        script_id = data.get('script_id')
        
        if not sensor_id or not script_version:
            return jsonify({'error': 'sensor_id and script_version are required'}), 400
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Update sensor's current running version
        cursor.execute('''
            UPDATE SensorRegistration 
            SET current_script_version = ?,
                current_script_id = ?,
                last_check_in = ?
            WHERE sensor_id = ?
        ''', (script_version, script_id, datetime.now(timezone.utc).isoformat(), sensor_id))
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'Sensor not found'}), 404
        
        conn.commit()
        logger.info(f"Sensor {sensor_id} reported running version {script_version}")
        return jsonify({'message': 'Version reported', 'version': script_version}), 200
        
    except Exception as e:
        logger.error(f"Error reporting version: {e}", exc_info=True)
        return jsonify({'error': 'Failed to report version'}), 500


@sensor_master_api_bp.route('/sensor-master/telemetry/<sensor_id>', methods=['GET'])
def get_sensor_telemetry(sensor_id):
    """
    Get telemetry data for a sensor
    
    Query params:
    - limit: Number of records to return (default: 100)
    """
    try:
        limit = request.args.get('limit', 100, type=int)
        
        conn = get_db()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT data, timestamp 
                FROM SensorTelemetry
                WHERE sensor_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (sensor_id, limit))
            
            rows = cursor.fetchall()
            
            telemetry = []
            for row in rows:
                telemetry.append({
                    'timestamp': row['timestamp'],
                    'data': json.loads(row['data'])
                })
                
            return jsonify({
                'sensor_id': sensor_id,
                'telemetry': telemetry
            }), 200
            
        except sqlite3.OperationalError:
            return jsonify({'error': 'Telemetry data not available'}), 404
            
    except Exception as e:
        logger.error(f"Error getting telemetry: {e}", exc_info=True)
        return jsonify({'error': 'Failed to get telemetry'}), 500


@sensor_master_api_bp.route('/sensor-master/library-scripts/<int:script_id>', methods=['DELETE'])
def delete_library_script(script_id):
    """Delete a script from the library"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if script exists
        cursor.execute('SELECT id FROM ScriptLibrary WHERE id = ?', (script_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Script not found'}), 404
            
        cursor.execute('DELETE FROM ScriptLibrary WHERE id = ?', (script_id,))
        conn.commit()
        
        logger.info(f"Library script deleted: {script_id}")
        
        return jsonify({'message': 'Script deleted successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error deleting library script: {e}", exc_info=True)
        return jsonify({'error': 'Failed to delete library script'}), 500


@sensor_master_api_bp.route('/sensor-master/logs', methods=['POST'])
def report_sensor_log():
    """
    Report a log message from a sensor
    
    Expected payload:
    {
        "sensor_id": "esp32_001",
        "message": "Log message content",
        "level": "info" (optional)
    }
    """
    try:
        data = request.get_json()
        logger.info(f"Received log request from sensor: {data}")
        
        if not data or 'sensor_id' not in data or 'message' not in data:
            return jsonify({'error': 'sensor_id and message are required'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO SensorLogs (sensor_id, message, log_level, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (
            data['sensor_id'],
            data['message'],
            data.get('level', 'info'),
            datetime.now(timezone.utc).isoformat()
        ))
        
        conn.commit()
        
        return jsonify({'message': 'Log saved'}), 201
        
    except Exception as e:
        logger.error(f"Error saving sensor log: {e}", exc_info=True)
        return jsonify({'error': f'Failed to save log: {str(e)}'}), 500


@sensor_master_api_bp.route('/sensor-master/logs/<sensor_id>', methods=['GET'])
def get_sensor_logs(sensor_id):
    """
    Get logs for a sensor
    
    Query params:
    - limit: Number of records to return (default: 100)
    """
    try:
        limit = request.args.get('limit', 100, type=int)
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT message, log_level, created_at
            FROM SensorLogs
            WHERE sensor_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (sensor_id, limit))
        
        logs = [dict(row) for row in cursor.fetchall()]
        
        return jsonify({
            'sensor_id': sensor_id,
            'logs': logs
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching sensor logs: {e}", exc_info=True)
        return jsonify({'error': 'Failed to fetch logs'}), 500


