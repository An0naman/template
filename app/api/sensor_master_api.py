# app/api/sensor_master_api.py
"""
Sensor Master Control API
==========================

This API provides endpoints for the Sensor Master Control system, which allows
sensors (like ESP32s) to "phone home" and receive configuration instructions from
a designated master control instance.

Endpoints:
----------
1. POST /api/sensor-master/register - Sensor registration (phone-home)
2. GET /api/sensor-master/config/<sensor_id> - Get sensor configuration
3. POST /api/sensor-master/heartbeat - Sensor heartbeat/status update
4. GET/POST/PATCH/DELETE /api/sensor-master/instances - Manage master instances
5. GET/PATCH /api/sensor-master/sensors - Manage registered sensors
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


def get_active_master():
    """Get the currently active master control instance"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM SensorMasterControl
        WHERE is_enabled = 1
        ORDER BY priority ASC, id ASC
        LIMIT 1
    ''')
    
    return cursor.fetchone()


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
        "assigned_master": "Local Master",
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
        
        # Check if master control is enabled
        master = get_active_master()
        
        if not master:
            return jsonify({
                'status': 'no_master',
                'message': 'No active master control instance available',
                'fallback_mode': True
            }), 200
        
        # Check if sensor is already registered
        cursor.execute('''
            SELECT id, assigned_master_id, status 
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
                 ip_address, mac_address, capabilities, assigned_master_id,
                 last_check_in, status, registration_source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                sensor_id,
                data.get('sensor_name', 'Unnamed Sensor'),
                sensor_type,
                data.get('hardware_info', ''),
                data.get('firmware_version', ''),
                data.get('ip_address', ''),
                data.get('mac_address', ''),
                json.dumps(data.get('capabilities', [])),
                master['id'],
                timestamp,
                'online',
                'auto'
            ))
            
            logger.info(f"Registered new sensor: {sensor_id}")
        
        # Check if there's a configuration available
        cursor.execute('''
            SELECT COUNT(*) FROM SensorMasterConfig
            WHERE master_id = ? 
            AND (sensor_id = ? OR sensor_type = ?)
            AND is_active = 1
        ''', (master['id'], sensor_id, sensor_type))
        
        has_config = cursor.fetchone()[0] > 0
        
        conn.commit()
        
        return jsonify({
            'status': 'registered',
            'assigned_master': master['instance_name'],
            'master_id': master['id'],
            'has_config': has_config,
            'message': 'Sensor registered successfully',
            'check_in_interval': 300,  # Check back every 5 minutes
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
            SELECT sr.*, smc.instance_name as master_name
            FROM SensorRegistration sr
            LEFT JOIN SensorMasterControl smc ON sr.assigned_master_id = smc.id
            WHERE sr.sensor_id = ?
        ''', (sensor_id,))
        
        sensor = cursor.fetchone()
        
        if not sensor:
            return jsonify({
                'error': 'Sensor not registered',
                'fallback_mode': True
            }), 404
        
        # Get master control instance
        master = get_active_master()
        
        if not master or not master['is_enabled']:
            return jsonify({
                'config_available': False,
                'fallback_mode': True,
                'message': 'Master control not active'
            }), 200
        
        # Get configuration (sensor-specific first, then type-specific, then default)
        cursor.execute('''
            SELECT config_data, config_version, config_name
            FROM SensorMasterConfig
            WHERE master_id = ? 
            AND (sensor_id = ? OR (sensor_id IS NULL AND sensor_type = ?))
            AND is_active = 1
            ORDER BY 
                CASE WHEN sensor_id IS NOT NULL THEN 1 ELSE 2 END,
                priority ASC
            LIMIT 1
        ''', (master['id'], sensor_id, sensor['sensor_type']))
        
        config_row = cursor.fetchone()
        
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
            'master': {
                'name': master['instance_name'],
                'id': master['id']
            },
            'check_in_interval': 300
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
        
        cursor.execute('''
            UPDATE SensorRegistration
            SET last_check_in = ?,
                status = ?,
                ip_address = ?,
                updated_at = ?
            WHERE sensor_id = ?
        ''', (
            timestamp,
            data.get('status', 'online'),
            data.get('ip_address', ''),
            timestamp,
            sensor_id
        ))
        
        if cursor.rowcount == 0:
            return jsonify({
                'error': 'Sensor not registered',
                'action': 'register'
            }), 404
        
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


@sensor_master_api_bp.route('/sensor-master/instances', methods=['GET'])
def get_master_instances():
    """Get all master control instances"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT smc.*,
                   COUNT(DISTINCT sr.id) as registered_sensors
            FROM SensorMasterControl smc
            LEFT JOIN SensorRegistration sr ON smc.id = sr.assigned_master_id
            GROUP BY smc.id
            ORDER BY smc.priority ASC, smc.instance_name ASC
        ''')
        
        instances = [dict(row) for row in cursor.fetchall()]
        
        return jsonify(instances), 200
        
    except Exception as e:
        logger.error(f"Error fetching master instances: {e}", exc_info=True)
        return jsonify({'error': 'Failed to fetch instances'}), 500


@sensor_master_api_bp.route('/sensor-master/instances', methods=['POST'])
def create_master_instance():
    """Create a new master control instance"""
    try:
        data = request.get_json()
        
        if not data or 'instance_name' not in data:
            return jsonify({'error': 'instance_name is required'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO SensorMasterControl
            (instance_name, description, api_endpoint, api_key, is_enabled,
             priority, status, max_sensors, allowed_sensor_types)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['instance_name'],
            data.get('description', ''),
            data.get('api_endpoint', ''),
            data.get('api_key', ''),
            data.get('is_enabled', False),
            data.get('priority', 100),
            'inactive',
            data.get('max_sensors', 0),
            data.get('allowed_sensor_types', '')
        ))
        
        instance_id = cursor.lastrowid
        conn.commit()
        
        return jsonify({
            'message': 'Master instance created successfully',
            'instance_id': instance_id
        }), 201
        
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Instance name already exists'}), 409
    except Exception as e:
        logger.error(f"Error creating master instance: {e}", exc_info=True)
        return jsonify({'error': 'Failed to create instance'}), 500


@sensor_master_api_bp.route('/sensor-master/instances/<int:instance_id>', methods=['PATCH'])
def update_master_instance(instance_id):
    """Update a master control instance"""
    try:
        data = request.get_json()
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Build update query dynamically
        update_fields = []
        values = []
        
        allowed_fields = ['instance_name', 'description', 'api_endpoint', 'api_key',
                         'is_enabled', 'priority', 'status', 'max_sensors', 
                         'allowed_sensor_types']
        
        for field in allowed_fields:
            if field in data:
                update_fields.append(f"{field} = ?")
                values.append(data[field])
        
        if not update_fields:
            return jsonify({'error': 'No fields to update'}), 400
        
        values.append(datetime.now(timezone.utc).isoformat())
        values.append(instance_id)
        
        cursor.execute(f'''
            UPDATE SensorMasterControl
            SET {', '.join(update_fields)}, updated_at = ?
            WHERE id = ?
        ''', values)
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'Instance not found'}), 404
        
        # Update heartbeat if enabling
        if data.get('is_enabled'):
            cursor.execute('''
                UPDATE SensorMasterControl
                SET last_heartbeat = ?, status = 'active'
                WHERE id = ?
            ''', (datetime.now(timezone.utc).isoformat(), instance_id))
        
        conn.commit()
        
        return jsonify({'message': 'Instance updated successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error updating master instance: {e}", exc_info=True)
        return jsonify({'error': 'Failed to update instance'}), 500


@sensor_master_api_bp.route('/sensor-master/instances/<int:instance_id>', methods=['DELETE'])
def delete_master_instance(instance_id):
    """Delete a master control instance"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM SensorMasterControl WHERE id = ?', (instance_id,))
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'Instance not found'}), 404
        
        conn.commit()
        
        return jsonify({'message': 'Instance deleted successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error deleting master instance: {e}", exc_info=True)
        return jsonify({'error': 'Failed to delete instance'}), 500


@sensor_master_api_bp.route('/sensor-master/sensors', methods=['GET'])
def get_registered_sensors():
    """Get all registered sensors"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Optional filters
        status_filter = request.args.get('status')
        master_filter = request.args.get('master_id')
        
        query = '''
            SELECT sr.*,
                   smc.instance_name as master_name,
                   smc.status as master_status
            FROM SensorRegistration sr
            LEFT JOIN SensorMasterControl smc ON sr.assigned_master_id = smc.id
            WHERE 1=1
        '''
        params = []
        
        if status_filter:
            query += ' AND sr.status = ?'
            params.append(status_filter)
        
        if master_filter:
            query += ' AND sr.assigned_master_id = ?'
            params.append(int(master_filter))
        
        query += ' ORDER BY sr.last_check_in DESC'
        
        cursor.execute(query, params)
        sensors = []
        
        for row in cursor.fetchall():
            sensor = dict(row)
            if sensor['capabilities']:
                sensor['capabilities'] = json.loads(sensor['capabilities'])
            sensors.append(sensor)
        
        return jsonify(sensors), 200
        
    except Exception as e:
        logger.error(f"Error fetching sensors: {e}", exc_info=True)
        return jsonify({'error': 'Failed to fetch sensors'}), 500


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
        conn = get_db()
        cursor = conn.cursor()
        
        master_filter = request.args.get('master_id')
        
        query = '''
            SELECT smc.*,
                   m.instance_name as master_name
            FROM SensorMasterConfig smc
            JOIN SensorMasterControl m ON smc.master_id = m.id
            WHERE 1=1
        '''
        params = []
        
        if master_filter:
            query += ' AND smc.master_id = ?'
            params.append(int(master_filter))
        
        query += ' ORDER BY smc.priority ASC, smc.created_at DESC'
        
        cursor.execute(query, params)
        configs = []
        
        for row in cursor.fetchall():
            config = dict(row)
            config['config_data'] = json.loads(config['config_data'])
            configs.append(config)
        
        return jsonify(configs), 200
        
    except Exception as e:
        logger.error(f"Error fetching configs: {e}", exc_info=True)
        return jsonify({'error': 'Failed to fetch configs'}), 500


@sensor_master_api_bp.route('/sensor-master/configs', methods=['POST'])
def create_sensor_config():
    """Create a new sensor configuration"""
    try:
        data = request.get_json()
        
        required = ['master_id', 'config_name', 'config_data']
        for field in required:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        config_data_str = json.dumps(data['config_data'])
        
        cursor.execute('''
            INSERT INTO SensorMasterConfig
            (master_id, sensor_id, sensor_type, config_name, config_data,
             config_version, is_active, priority, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['master_id'],
            data.get('sensor_id'),
            data.get('sensor_type'),
            data['config_name'],
            config_data_str,
            data.get('config_version', 1),
            data.get('is_active', True),
            data.get('priority', 100),
            data.get('description', '')
        ))
        
        config_id = cursor.lastrowid
        conn.commit()
        
        return jsonify({
            'message': 'Configuration created successfully',
            'config_id': config_id
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating config: {e}", exc_info=True)
        return jsonify({'error': 'Failed to create configuration'}), 500


@sensor_master_api_bp.route('/sensor-master/configs/<int:config_id>', methods=['PATCH'])
def update_sensor_config(config_id):
    """Update a sensor configuration"""
    try:
        data = request.get_json()
        
        conn = get_db()
        cursor = conn.cursor()
        
        update_fields = []
        values = []
        
        allowed_fields = ['config_name', 'config_data', 'config_version',
                         'is_active', 'priority', 'description', 'sensor_id', 'sensor_type']
        
        for field in allowed_fields:
            if field in data:
                if field == 'config_data':
                    update_fields.append(f"{field} = ?")
                    values.append(json.dumps(data[field]))
                else:
                    update_fields.append(f"{field} = ?")
                    values.append(data[field])
        
        if not update_fields:
            return jsonify({'error': 'No fields to update'}), 400
        
        values.append(datetime.now(timezone.utc).isoformat())
        values.append(config_id)
        
        cursor.execute(f'''
            UPDATE SensorMasterConfig
            SET {', '.join(update_fields)}, updated_at = ?
            WHERE id = ?
        ''', values)
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'Configuration not found'}), 404
        
        conn.commit()
        
        return jsonify({'message': 'Configuration updated successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error updating config: {e}", exc_info=True)
        return jsonify({'error': 'Failed to update configuration'}), 500


@sensor_master_api_bp.route('/sensor-master/configs/<int:config_id>', methods=['DELETE'])
def delete_sensor_config(config_id):
    """Delete a sensor configuration"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM SensorMasterConfig WHERE id = ?', (config_id,))
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'Configuration not found'}), 404
        
        conn.commit()
        
        return jsonify({'message': 'Configuration deleted successfully'}), 200
        
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
                command['result'] = json.loads(command['result'])
            commands.append(command)
        
        return jsonify(commands), 200
        
    except Exception as e:
        logger.error(f"Error fetching commands: {e}", exc_info=True)
        return jsonify({'error': 'Failed to fetch commands'}), 500


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

