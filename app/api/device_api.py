# app/api/device_api.py

from flask import Blueprint, request, jsonify, g
import sqlite3
import requests
import socket
import threading
import ipaddress
import logging
from datetime import datetime, timedelta, timezone
import json
from ..db import get_connection
from ..utils.sensor_type_manager import auto_register_sensor_types, get_sensor_types_from_device_data

# Define a Blueprint for Device API
device_api_bp = Blueprint('device_api', __name__)

# Get a logger for this module
logger = logging.getLogger(__name__)

def get_db():
    """Get database connection"""
    if 'db' not in g:
        g.db = get_connection()
        g.db.row_factory = sqlite3.Row
    return g.db

def get_local_network_range():
    """Get the local network range for scanning (Docker-aware)"""
    try:
        # First check if network range is set via environment variable (for Docker bridge mode)
        import os
        env_network = os.getenv('NETWORK_RANGE')
        if env_network:
            logger.info(f"Using network range from environment: {env_network}")
            return env_network
        
        # First, try to get the default gateway (host network)
        # This is more reliable when running in Docker
        import subprocess
        import re
        
        # Try to get the default route to find the host network
        try:
            result = subprocess.run(['ip', 'route', 'show', 'default'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                # Extract the gateway IP from the default route
                match = re.search(r'via\s+(\d+\.\d+\.\d+\.\d+)', result.stdout)
                if match:
                    gateway_ip = match.group(1)
                    # Assume /24 subnet for the gateway
                    network = ipaddress.IPv4Network(f"{gateway_ip}/24", strict=False)
                    logger.info(f"Detected host network via gateway: {network}")
                    return str(network)
        except Exception as e:
            logger.debug(f"Could not detect network via gateway: {e}")
        
        # Fallback: Try to connect to a known external IP and see what interface is used
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        
        # Check if this is a Docker internal IP (172.x.x.x range)
        if local_ip.startswith('172.'):
            logger.info(f"Detected Docker internal IP {local_ip}, using common home network ranges")
            # Try common home network ranges when running in Docker
            common_ranges = ["192.168.1.0/24", "192.168.0.0/24", "192.168.68.0/24", "10.0.0.0/24"]
            # Return the first one that might contain devices
            # In practice, you might want to try all of them or make this configurable
            return "192.168.68.0/24"  # Your specific network
        
        # Convert to network range (assuming /24 subnet)
        network = ipaddress.IPv4Network(f"{local_ip}/24", strict=False)
        logger.info(f"Detected local network: {network}")
        return str(network)
        
    except Exception as e:
        logger.error(f"Error getting local network range: {e}")
        return "192.168.68.0/24"  # Default to your known network

def scan_for_esp32_device(ip):
    """Scan a single IP for ESP32 fermentation controller"""
    try:
        # Try to connect to the device's /api endpoint (your ESP32 uses /api, not /data)
        response = requests.get(f"http://{ip}/api", timeout=2)
        if response.status_code == 200:
            data = response.json()
            
            # Extract device identifiers
            device_name = data.get('device_name') or data.get('name', '')
            device_id = data.get('device_id') or data.get('id', '')
            
            # Check if this looks like our ESP32 device based on naming convention
            # Look for common ESP32/fermentation controller naming patterns
            name_patterns = [
                'esp32', 'fermentation', 'controller', 'sensor', 'temp', 'brewery', 'fermenter'
            ]
            
            # Check if device_name or device_id contains any of our patterns
            # OR if the device explicitly reports a type we know
            device_text = f"{device_name} {device_id} {data.get('type', '')}".lower()
            is_target_device = any(pattern in device_text for pattern in name_patterns)
            
            # Also check if it has the basic structure we expect (but don't require sensor to be working)
            has_basic_structure = (
                'device_id' in data or 'device_name' in data or 'id' in data or 'name' in data
            )
            
            if is_target_device and has_basic_structure:
                # Determine device type based on what fields are present
                device_type = 'unknown'
                capabilities = []
                
                if 'sensor' in data:
                    capabilities.append('temperature')
                if 'relay' in data:
                    capabilities.append('relay_control')
                    
                # More specific typing based on naming
                if any(word in device_text for word in ['fermentation', 'fermenter', 'brewery']):
                    device_type = 'esp32_fermentation'
                elif 'esp32' in device_text:
                    device_type = 'esp32_generic'
                else:
                    device_type = 'iot_device'
                
                # Use fallback names if not provided
                # Handle both 'device_name' (old) and 'name' (new firmware)
                final_device_name = device_name or data.get('name') or f'Device at {ip}'
                final_device_id = device_id or data.get('id') or f'device_{ip.replace(".", "_")}'
                
                logger.info(f"Found {device_type} device at {ip}: {final_device_name} (ID: {final_device_id})")
                
                return {
                    'ip': ip,
                    'device_id': final_device_id,
                    'device_name': final_device_name,
                    'last_seen': datetime.now().isoformat(),
                    'status': 'online',
                    'device_type': device_type,
                    'capabilities': capabilities,
                    'sample_data': data
                }
    except requests.exceptions.ConnectTimeout:
        # Silently skip timeout errors (expected for most IPs)
        pass
    except requests.exceptions.ConnectionError:
        # Silently skip connection errors (expected for most IPs)
        pass
    except requests.exceptions.RequestException as e:
        # Log other request errors for debugging
        logger.debug(f"Request error for {ip}: {e}")
    except Exception as e:
        # Log unexpected errors
        logger.debug(f"Unexpected error scanning {ip}: {e}")
    return None

@device_api_bp.route('/devices/scan', methods=['POST'])
def scan_network():
    """Scan the local network for ESP32 devices"""
    try:
        data = request.get_json() or {}
        network_range = data.get('network_range') or get_local_network_range()
        
        logger.info(f"Starting network scan on range: {network_range}")
        
        # Validate network range
        try:
            network = ipaddress.IPv4Network(network_range)
            if network.num_addresses > 512:  # Limit scan size
                return jsonify({'error': f'Network range too large ({network.num_addresses} addresses). Please use a smaller range.'}), 400
        except ValueError as e:
            return jsonify({'error': f'Invalid network range: {e}'}), 400
        
        discovered_devices = []
        threads = []
        
        def scan_ip_range():
            try:
                network = ipaddress.IPv4Network(network_range)
                logger.info(f"Scanning {network.num_addresses - 2} host addresses in {network_range}")
                
                # Use a thread-safe list for results
                import threading
                device_results = []
                result_lock = threading.Lock()
                
                def scan_and_store_ip(ip_str):
                    try:
                        result = scan_for_esp32_device(ip_str)
                        if result:
                            with result_lock:
                                device_results.append(result)
                    except Exception as e:
                        logger.debug(f"Error scanning {ip_str}: {e}")
                
                for ip in network.hosts():
                    ip_str = str(ip)
                    thread = threading.Thread(target=scan_and_store_ip, args=(ip_str,))
                    thread.start()
                    threads.append(thread)
                    
                    # Limit concurrent threads to avoid overwhelming the network
                    if len(threads) >= 20:
                        for t in threads:
                            t.join()
                        threads.clear()
                
                # Wait for remaining threads
                for t in threads:
                    t.join()
                
                # Copy results to main list
                discovered_devices.extend(device_results)
                
            except Exception as e:
                logger.error(f"Error in scan_ip_range: {e}", exc_info=True)
                raise
        
        # Run the scan
        scan_ip_range()
        
        # Auto-reconnect registered devices found with new IPs
        reconnected_count = 0
        try:
            conn = get_db()
            cursor = conn.cursor()
            
            for device in discovered_devices:
                device_id = device.get('device_id') or device.get('id')
                ip = device.get('ip')
                
                if device_id and ip:
                    # Check if this device is registered
                    cursor.execute('SELECT id, ip FROM RegisteredDevices WHERE device_id = ?', (device_id,))
                    registered = cursor.fetchone()
                    
                    if registered:
                        # If registered but IP is different, update it
                        if registered['ip'] != ip:
                            logger.info(f"Auto-reconnecting device {device_id}: IP changed from {registered['ip']} to {ip}")
                            timestamp = datetime.now(timezone.utc).isoformat()
                            cursor.execute('''
                                UPDATE RegisteredDevices 
                                SET ip = ?, status = 'online', last_seen = ? 
                                WHERE id = ?
                            ''', (ip, timestamp, registered['id']))
                            reconnected_count += 1
                            device['status'] = 'reconnected'
                        else:
                            # Just update status to online if IP matches
                            timestamp = datetime.now(timezone.utc).isoformat()
                            cursor.execute('''
                                UPDATE RegisteredDevices 
                                SET status = 'online', last_seen = ? 
                                WHERE id = ?
                            ''', (timestamp, registered['id']))
                            device['status'] = 'online'
            
            if reconnected_count > 0:
                conn.commit()
                logger.info(f"Auto-reconnected {reconnected_count} devices during scan")
                
        except Exception as e:
            logger.error(f"Error processing auto-reconnect during scan: {e}")

        logger.info(f"Network scan completed. Found {len(discovered_devices)} ESP32 devices")
        
        return jsonify({
            'discovered_devices': discovered_devices,
            'reconnected_count': reconnected_count,
            'scan_range': network_range,
            'scan_time': datetime.now().isoformat(),
            'total_scanned': len(list(ipaddress.IPv4Network(network_range).hosts()))
        })
        
    except ValueError as e:
        logger.error(f"Invalid network range in scan: {e}")
        return jsonify({'error': f'Invalid network range: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"Error scanning network: {e}", exc_info=True)
        return jsonify({'error': f'Network scan failed: {str(e)}'}), 500

@device_api_bp.route('/devices', methods=['GET'])
def get_devices():
    """Get all registered devices"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get devices with their linked entries
        cursor.execute('''
            SELECT d.*, 
                   GROUP_CONCAT(e.title) as entry_titles,
                   GROUP_CONCAT(e.id) as entry_ids
            FROM RegisteredDevices d
            LEFT JOIN DeviceEntryLinks del ON d.id = del.device_id
            LEFT JOIN Entry e ON del.entry_id = e.id
            GROUP BY d.id
            ORDER BY d.device_name
        ''')
        
        devices = []
        for row in cursor.fetchall():
            device = dict(row)
            if device['capabilities']:
                device['capabilities'] = json.loads(device['capabilities'])
            
            # Parse linked entries
            if device['entry_titles'] and device['entry_ids']:
                device['linked_entries'] = [
                    {'id': int(eid), 'title': title} 
                    for eid, title in zip(device['entry_ids'].split(','), device['entry_titles'].split(','))
                ]
                # For backward compatibility, set the first entry as the primary
                device['entry_title'] = device['entry_titles'].split(',')[0]
                device['entry_id'] = int(device['entry_ids'].split(',')[0])
            else:
                device['linked_entries'] = []
                device['entry_title'] = None
                device['entry_id'] = None
            
            devices.append(device)
        
        return jsonify(devices)
        
    except Exception as e:
        logger.error(f"Error fetching devices: {e}", exc_info=True)
        return jsonify({'error': 'Failed to fetch devices'}), 500

@device_api_bp.route('/devices', methods=['POST'])
def register_device():
    """Register a new device"""
    try:
        data = request.get_json()
        
        required_fields = ['device_id', 'device_name', 'ip', 'device_type']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if device already exists
        cursor.execute("SELECT id FROM RegisteredDevices WHERE device_id = ?", (data['device_id'],))
        if cursor.fetchone():
            return jsonify({'error': 'Device with this ID already registered'}), 409
        
        # We no longer auto-create sensor types during device registration
        # Users will configure data points manually, which will create the appropriate sensor types
        
        # Insert new device (without linked_entry_id)
        cursor.execute('''
            INSERT INTO RegisteredDevices 
            (device_id, device_name, ip, device_type, capabilities, 
             polling_enabled, polling_interval, last_seen, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['device_id'],
            data['device_name'],
            data['ip'],
            data['device_type'],
            json.dumps(data.get('capabilities', [])),
            data.get('polling_enabled', True),
            data.get('polling_interval', 60),  # Default 60 seconds
            datetime.now().isoformat(),
            'active'
        ))
        
        device_db_id = cursor.lastrowid
        
        # Handle linked entries
        linked_entry_ids = data.get('linked_entry_ids', [])
        if isinstance(linked_entry_ids, (int, str)):
            linked_entry_ids = [linked_entry_ids]
        
        for entry_id in linked_entry_ids:
            if entry_id:  # Skip empty values
                cursor.execute('''
                    INSERT OR IGNORE INTO DeviceEntryLinks (device_id, entry_id)
                    VALUES (?, ?)
                ''', (device_db_id, int(entry_id)))
        
        conn.commit()
        
        return jsonify({
            'message': 'Device registered successfully',
            'device_id': device_db_id
        }), 201
        
    except Exception as e:
        logger.error(f"Error registering device: {e}", exc_info=True)
        conn.rollback()
        return jsonify({'error': 'Failed to register device'}), 500

@device_api_bp.route('/devices/<int:device_id>', methods=['PATCH'])
def update_device(device_id):
    """Update device settings"""
    try:
        data = request.get_json()
        conn = get_db()
        cursor = conn.cursor()
        
        # Build update query dynamically
        update_fields = []
        values = []
        
        allowed_fields = ['device_name', 'ip', 'polling_enabled', 
                         'polling_interval', 'status', 'capabilities']
        
        for field in allowed_fields:
            if field in data:
                update_fields.append(f"{field} = ?")
                if field == 'capabilities':
                    values.append(json.dumps(data[field]))
                else:
                    values.append(data[field])
        
        # Handle linked entries separately
        if 'linked_entry_ids' in data:
            # Delete existing links
            cursor.execute("DELETE FROM DeviceEntryLinks WHERE device_id = ?", (device_id,))
            
            # Add new links
            linked_entry_ids = data['linked_entry_ids']
            if isinstance(linked_entry_ids, (int, str)):
                linked_entry_ids = [linked_entry_ids]
            
            for entry_id in linked_entry_ids:
                if entry_id:  # Skip empty values
                    cursor.execute('''
                        INSERT OR IGNORE INTO DeviceEntryLinks (device_id, entry_id)
                        VALUES (?, ?)
                    ''', (device_id, int(entry_id)))
        
        if update_fields:
            values.append(device_id)
            
            cursor.execute(f'''
                UPDATE RegisteredDevices 
                SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', values)
            
            if cursor.rowcount == 0:
                return jsonify({'error': 'Device not found'}), 404
        
        conn.commit()
        
        return jsonify({'message': 'Device updated successfully'})
        
    except Exception as e:
        logger.error(f"Error updating device {device_id}: {e}", exc_info=True)
        conn.rollback()
        return jsonify({'error': 'Failed to update device'}), 500

@device_api_bp.route('/devices/<int:device_id>', methods=['DELETE'])
def delete_device(device_id):
    """Delete a registered device"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM RegisteredDevices WHERE id = ?", (device_id,))
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'Device not found'}), 404
        
        conn.commit()
        
        return jsonify({'message': 'Device deleted successfully'})
        
    except Exception as e:
        logger.error(f"Error deleting device {device_id}: {e}", exc_info=True)
        conn.rollback()
        return jsonify({'error': 'Failed to delete device'}), 500

def extract_sensor_data_using_mappings(device_id, device_data, cursor):
    """
    Extract sensor data based on configured device sensor mappings
    
    Args:
        device_id: ID of the device
        device_data: Raw JSON data from device
        cursor: Database cursor
        
    Returns:
        List of sensor data points with mapped sensor types
    """
    # Get configured sensor mappings for this device
    cursor.execute('''
        SELECT sensor_name, entry_field, data_type, unit, enabled
        FROM DeviceSensorMapping 
        WHERE device_id = ? AND enabled = 1
    ''', (device_id,))
    
    mappings = cursor.fetchall()
    sensor_data_points = []
    timestamp = datetime.now(timezone.utc).isoformat()
    
    def get_nested_value(data, path):
        """Get value from nested dictionary using dot notation and array notation path"""
        import re
        # Split path by dots, but handle array notation like sensors[0]
        parts = []
        for part in path.split('.'):
            # Check if this part has array notation
            array_match = re.match(r'([^\[]+)\[(\d+)\]', part)
            if array_match:
                key_name = array_match.group(1)
                index = int(array_match.group(2))
                parts.append((key_name, 'dict'))
                parts.append((index, 'list'))
            else:
                parts.append((part, 'dict'))
        
        current = data
        for key, key_type in parts:
            if key_type == 'dict':
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    return None
            elif key_type == 'list':
                if isinstance(current, list) and 0 <= key < len(current):
                    current = current[key]
                else:
                    return None
        return current
    
    # Process each configured mapping
    for mapping in mappings:
        sensor_name = mapping['sensor_name']  # e.g., "sensor.temperature"
        entry_field = mapping['entry_field']   # e.g., "Temperature" 
        unit = mapping['unit'] or ''
        
        # Extract the value from device data
        value = get_nested_value(device_data, sensor_name)
        
        if value is not None:
            # Format the value with unit if specified
            if unit and isinstance(value, (int, float)):
                formatted_value = f"{value}{unit}"
            else:
                formatted_value = str(value)
            
            sensor_data_points.append({
                'sensor_type': entry_field,  # Use the configured sensor type name
                'value': formatted_value,
                'recorded_at': timestamp
            })
    
    return sensor_data_points

@device_api_bp.route('/devices/<int:device_id>/poll', methods=['POST'])
def poll_device_data(device_id):
    """Manually poll data from a specific device"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get device info with linked entries
        cursor.execute('''
            SELECT d.*, GROUP_CONCAT(del.entry_id) as linked_entry_ids
            FROM RegisteredDevices d
            LEFT JOIN DeviceEntryLinks del ON d.id = del.device_id
            WHERE d.id = ?
            GROUP BY d.id
        ''', (device_id,))
        device = cursor.fetchone()
        
        if not device:
            return jsonify({'error': 'Device not found'}), 404
        
        # Get linked entry IDs
        linked_entry_ids = []
        if device['linked_entry_ids']:
            linked_entry_ids = [int(eid) for eid in device['linked_entry_ids'].split(',')]
        
        if not linked_entry_ids:
            return jsonify({'error': 'Device not linked to any entries'}), 400
        
        # Poll the device
        try:
            response = requests.get(f"http://{device['ip']}/api", timeout=10)
            response.raise_for_status()
            device_data = response.json()
            
            # Extract sensor data using configured mappings
            sensor_data_points = extract_sensor_data_using_mappings(device_id, device_data, cursor)
            
            if not sensor_data_points:
                return jsonify({'warning': 'No sensor mappings configured for this device. Please configure data points first.'}), 200
            
            # Store sensor data to all linked entries and trigger notification checks
            stored_count = 0
            for entry_id in linked_entry_ids:
                for sensor_point in sensor_data_points:
                    cursor.execute('''
                        INSERT INTO SensorData (entry_id, sensor_type, value, recorded_at)
                        VALUES (?, ?, ?, ?)
                    ''', (
                        entry_id,
                        sensor_point['sensor_type'],
                        sensor_point['value'],
                        sensor_point['recorded_at']
                    ))
                    stored_count += 1
                    
                    # Check sensor notification rules for each data point
                    try:
                        from ..api.notifications_api import check_sensor_rules
                        check_sensor_rules(entry_id, sensor_point['sensor_type'], 
                                         sensor_point['value'], sensor_point['recorded_at'])
                    except Exception as e:
                        logger.warning(f"Error checking sensor rules for entry {entry_id}: {e}")
                        # Don't fail the data collection if notification checking fails
            
            # Update device last_seen
            timestamp = datetime.now(timezone.utc).isoformat()
            cursor.execute('''
                UPDATE RegisteredDevices 
                SET last_seen = ?, status = 'online', last_poll_success = ?
                WHERE id = ?
            ''', (timestamp, timestamp, device_id))
            
            conn.commit()
            
            return jsonify({
                'message': f'Successfully polled device and stored {stored_count} sensor readings to {len(linked_entry_ids)} entries',
                'device_data': device_data,
                'stored_sensors': stored_count,
                'linked_entries': len(linked_entry_ids)
            })
            
        except requests.RequestException as e:
            # Update device status to offline
            cursor.execute('''
                UPDATE RegisteredDevices 
                SET status = 'offline', last_poll_error = ?
                WHERE id = ?
            ''', (str(e), device_id))
            conn.commit()
            
            return jsonify({'error': f'Failed to connect to device: {str(e)}'}), 503
        
    except Exception as e:
        logger.error(f"Error polling device {device_id}: {e}", exc_info=True)
        return jsonify({'error': 'Failed to poll device'}), 500

@device_api_bp.route('/devices/poll-all', methods=['POST'])
def poll_all_devices():
    """Poll data from all enabled devices"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get all devices with polling enabled that have linked entries
        cursor.execute('''
            SELECT d.*, GROUP_CONCAT(del.entry_id) as linked_entry_ids
            FROM RegisteredDevices d
            INNER JOIN DeviceEntryLinks del ON d.id = del.device_id
            WHERE d.polling_enabled = 1 AND d.status != 'disabled'
            GROUP BY d.id
        ''')
        
        devices = cursor.fetchall()
        results = []
        
        for device in devices:
            try:
                # Check if it's time to poll this device
                if device['last_poll_success']:
                    last_poll = datetime.fromisoformat(device['last_poll_success'])
                    if datetime.now() - last_poll < timedelta(seconds=device['polling_interval']):
                        continue  # Skip if not time yet
                
                # Get linked entry IDs
                linked_entry_ids = [int(eid) for eid in device['linked_entry_ids'].split(',')]
                
                # Poll the device (reuse logic from poll_device_data)
                response = requests.get(f"http://{device['ip']}/api", timeout=5)
                response.raise_for_status()
                device_data = response.json()
                
                # Extract sensor data using configured mappings
                sensor_data_points = extract_sensor_data_using_mappings(device['id'], device_data, cursor)
                
                if not sensor_data_points:
                    # No configured mappings - skip this device
                    continue
                
                # Store sensor data to all linked entries and trigger notification checks
                stored_count = 0
                for entry_id in linked_entry_ids:
                    for sensor_point in sensor_data_points:
                        cursor.execute('''
                            INSERT INTO SensorData (entry_id, sensor_type, value, recorded_at)
                            VALUES (?, ?, ?, ?)
                        ''', (
                            entry_id,
                            sensor_point['sensor_type'],
                            sensor_point['value'],
                            sensor_point['recorded_at']
                        ))
                        stored_count += 1
                        
                        # Check sensor notification rules for each data point
                        try:
                            from ..api.notifications_api import check_sensor_rules
                            check_sensor_rules(entry_id, sensor_point['sensor_type'], 
                                             sensor_point['value'], sensor_point['recorded_at'])
                        except Exception as e:
                            logger.warning(f"Error checking sensor rules for entry {entry_id}: {e}")
                            # Don't fail the data collection if notification checking fails
                
                timestamp = datetime.now(timezone.utc).isoformat()
                cursor.execute('''
                    UPDATE RegisteredDevices 
                    SET last_seen = ?, status = 'online', last_poll_success = ?
                    WHERE id = ?
                ''', (timestamp, timestamp, device['id']))
                
                results.append({
                    'device_id': device['id'],
                    'device_name': device['device_name'],
                    'status': 'success',
                    'sensors_stored': stored_count,
                    'linked_entries': len(linked_entry_ids)
                })
                
            except Exception as e:
                cursor.execute('''
                    UPDATE RegisteredDevices 
                    SET status = 'offline', last_poll_error = ?
                    WHERE id = ?
                ''', (str(e), device['id']))
                
                results.append({
                    'device_id': device['id'],
                    'device_name': device['device_name'],
                    'status': 'error',
                    'error': str(e)
                })
        
        conn.commit()
        
        return jsonify({
            'message': f'Polled {len(results)} devices',
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error polling all devices: {e}", exc_info=True)
        return jsonify({'error': 'Failed to poll devices'}), 500

@device_api_bp.route('/devices/test-connection', methods=['POST'])
def test_device_connection():
    """Test connection to a device without registering it"""
    try:
        data = request.get_json()
        ip = data.get('ip')
        
        if not ip:
            return jsonify({'error': 'IP address required'}), 400
        
        # Try to connect to the device (use /api endpoint for your ESP32)
        response = requests.get(f"http://{ip}/api", timeout=10)
        response.raise_for_status()
        device_data = response.json()
        
        # Analyze the response to determine device type using naming convention
        device_info = {
            'ip': ip,
            'status': 'online',
            'response_data': device_data
        }
        
        # Extract device identifiers
        device_name = device_data.get('device_name', '')
        device_id = device_data.get('device_id', '')
        
        # Check if this looks like our target device based on naming convention
        name_patterns = [
            'esp32', 'fermentation', 'controller', 'sensor', 'temp', 'brewery', 'fermenter'
        ]
        
        device_text = f"{device_name} {device_id}".lower()
        is_target_device = any(pattern in device_text for pattern in name_patterns)
        
        if is_target_device or ('sensor' in device_data and 'relay' in device_data and 'device_id' in device_data):
            # Determine capabilities based on what's present in the data
            capabilities = []
            if 'sensor' in device_data:
                capabilities.append('temperature')
            if 'relay' in device_data:
                capabilities.append('relay_control')
            
            # Determine device type based on naming
            device_type = 'unknown'
            if any(word in device_text for word in ['fermentation', 'fermenter', 'brewery']):
                device_type = 'esp32_fermentation'
            elif 'esp32' in device_text:
                device_type = 'esp32_generic'
            elif capabilities:  # Has sensor/relay but no clear naming
                device_type = 'iot_device'
            
            # Extract additional info if available
            temperature = None
            heating_status = None
            wifi_signal = None
            
            if 'sensor' in device_data:
                sensor_data = device_data['sensor']
                temperature = sensor_data.get('temperature')
                # Mark as error if temperature is invalid
                if temperature == -999 or not sensor_data.get('valid', True):
                    temperature = f"{temperature} (SENSOR ERROR)"
            
            if 'relay' in device_data:
                heating_status = device_data['relay'].get('state')
            
            if 'network' in device_data:
                wifi_signal = device_data['network'].get('rssi')
            
            device_info.update({
                'device_type': device_type,
                'device_name': device_name or f'Device at {ip}',
                'device_id': device_id or f'device_{ip.replace(".", "_")}',
                'capabilities': capabilities,
                'temperature': temperature,
                'heating_status': heating_status,
                'wifi_signal': wifi_signal
            })
        else:
            device_info.update({
                'device_type': 'unknown',
                'device_name': f'Unknown Device ({ip})',
                'capabilities': []
            })
        
        return jsonify(device_info)
        
    except requests.RequestException as e:
        return jsonify({
            'ip': data.get('ip'),
            'status': 'offline',
            'error': f'Connection failed: {str(e)}'
        }), 503
    except Exception as e:
        logger.error(f"Error testing device connection: {e}", exc_info=True)
        return jsonify({'error': 'Connection test failed'}), 500

@device_api_bp.route('/devices/status', methods=['GET'])
def get_api_status():
    """Get API status and configuration for debugging"""
    try:
        local_network = get_local_network_range()
        
        return jsonify({
            'status': 'active',
            'local_network_range': local_network,
            'timestamp': datetime.now().isoformat(),
            'available_endpoints': [
                '/devices/scan - Full network scan with threading',
                '/devices/test-connection - Test single IP',
                '/devices/status - This endpoint',
                '/devices - CRUD operations',
                '/devices/{id}/sensor-mappings - Configure data points'
            ]
        })
        
    except Exception as e:
        logger.error(f"Error getting API status: {e}", exc_info=True)
        return jsonify({'error': f'Status check failed: {str(e)}'}), 500


# Sensor Mapping API Endpoints

def _extract_aliases_from_script(script_content):
    """
    Extract aliases from a sensor script to improve data labeling
    """
    aliases = {}
    try:
        if not script_content:
            return aliases
            
        # Handle case where script_content might be a dict already or a string
        if isinstance(script_content, str):
            script = json.loads(script_content)
        else:
            script = script_content
            
        actions = script.get('actions', [])
        
        def recurse_actions(action_list):
            for action in action_list:
                if isinstance(action, dict):
                    if 'alias' in action and action['alias']:
                        alias = action['alias']
                        action_type = action.get('type', '')
                        pin = action.get('pin')
                        
                        info = {
                            'alias': alias, 
                            'type': action_type,
                            'pin': pin
                        }
                        
                        # Add metadata based on type
                        if action_type == 'read_temperature':
                            info['unit'] = '°C'
                            info['data_type'] = 'numeric'
                            info['category'] = 'sensor'
                        elif action_type == 'gpio_write':
                            info['unit'] = ''
                            info['data_type'] = 'text'
                            info['category'] = 'control'
                        elif action_type == 'gpio_read':
                            info['unit'] = ''
                            info['data_type'] = 'numeric'
                            info['category'] = 'sensor'
                        elif action_type == 'read_battery':
                            info['unit'] = 'V'
                            info['data_type'] = 'numeric'
                            info['category'] = 'sensor'
                            # Also add the percentage alias
                            aliases[alias + '_pct'] = {
                                'alias': alias + '_pct',
                                'type': 'read_battery_pct',
                                'pin': pin,
                                'unit': '%',
                                'data_type': 'numeric',
                                'category': 'sensor'
                            }
                            
                        aliases[alias] = info
                    
                    # Recurse into nested blocks
                    if 'then' in action and isinstance(action['then'], list):
                        recurse_actions(action['then'])
                    if 'else' in action and isinstance(action['else'], list):
                        recurse_actions(action['else'])
                    
        recurse_actions(actions)
    except Exception as e:
        logger.error(f"Error extracting aliases from script: {e}")
        
    return aliases

@device_api_bp.route('/devices/<int:device_id>/sensor-mappings', methods=['GET'])
def get_sensor_mappings(device_id):
    """Get sensor mappings for a device"""
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Check if device exists
        cursor.execute('SELECT * FROM RegisteredDevices WHERE id = ?', (device_id,))
        device = cursor.fetchone()
        if not device:
            return jsonify({'error': 'Device not found'}), 404
        
        # Get existing sensor mappings
        cursor.execute('''
            SELECT sensor_name, entry_field, data_type, unit, enabled 
            FROM DeviceSensorMapping 
            WHERE device_id = ?
        ''', (device_id,))
        sensor_mappings = [dict(row) for row in cursor.fetchall()]
        
        # Try to get script aliases to improve labeling (do this first so it's available for fallback)
        script_aliases = {}
        try:
            # Find the sensor_id (string) for this device
            sensor_id = device['device_id']
            logger.info(f"DEBUG: Looking for script for sensor_id: {sensor_id}")
            
            # Get the active script for this sensor
            cursor.execute('''
                SELECT s.script_content 
                FROM SensorRegistration r
                JOIN SensorScripts s ON r.current_script_id = s.id
                WHERE r.sensor_id = ?
            ''', (sensor_id,))
            
            script_row = cursor.fetchone()
            if script_row:
                logger.info(f"DEBUG: Found script content for {sensor_id}")
                if script_row['script_content']:
                    script_aliases = _extract_aliases_from_script(script_row['script_content'])
                    logger.info(f"DEBUG: Extracted aliases: {list(script_aliases.keys())}")
                else:
                    logger.info("DEBUG: Script content is empty")
            else:
                logger.info(f"DEBUG: No active script found in DB for {sensor_id}")

        except Exception as e:
            logger.warning(f"Could not get script aliases: {e}")

        # Get available sensors by actually polling the device
        available_sensors = []
        try:
            # Poll device for current data
            logger.info(f"Polling device {device_id} at IP: {device['ip']}")
            endpoint = f"http://{device['ip']}/api"
            response = requests.get(endpoint, timeout=5)
            
            if response.status_code == 200:
                device_data = response.json()
                
                # Analyze the data structure to find available sensors
                data_paths = _analyze_data_structure(device_data)
                
                # Convert to available sensors format, grouping by category
                for path, info in data_paths.items():
                    # Skip non-useful data points
                    if path in ['device_id', 'device_name', 'timestamp', 'id', 'name', 'type', 'mac_address', 'ip_address']:
                        continue
                    
                    display_name = info.get('display_name', path.replace('_', ' ').title())
                    
                    # Apply script aliases if available
                    if script_aliases:
                        # Heuristic: Map 'temperature' to the first read_temperature alias
                        if path == 'temperature':
                            for alias, meta in script_aliases.items():
                                if meta['type'] == 'read_temperature':
                                    display_name = f"{alias} (Temperature)"
                                    break
                        # Heuristic: Map 'relay_state' to the first gpio_write alias on pin 25
                        elif path == 'relay_state':
                            for alias, meta in script_aliases.items():
                                if meta['type'] == 'gpio_write' and meta.get('pin') == 25:
                                    display_name = f"{alias} (Relay)"
                                    break
                        # Direct match (if firmware is updated to send alias keys)
                        elif path in script_aliases:
                            display_name = script_aliases[path]['alias']

                    available_sensors.append({
                        'name': path,
                        'display_name': display_name,
                        'unit': info.get('unit', ''),
                        'data_type': info.get('data_type', 'text'),
                        'category': info.get('category', 'unknown'),
                        'sample_value': info.get('value', '')
                    })
                
                # If we filtered out everything (e.g. only metadata was returned), 
                # or if we want to ensure standard sensors are present for this device type
                # we should inject them based on the script or device type.
                
                # Check if we have the core sensors
                has_temp = any(s['name'] == 'temperature' for s in available_sensors)
                has_relay = any(s['name'] == 'relay_state' for s in available_sensors)
                
                if not has_temp or not has_relay:
                    # Inject from script aliases if possible
                    if script_aliases:
                        for alias, meta in script_aliases.items():
                            if meta['type'] == 'read_temperature' and not any(s['name'] == 'temperature' for s in available_sensors):
                                available_sensors.append({
                                    'name': 'temperature',
                                    'display_name': f"{alias} (Temperature)",
                                    'unit': '°C',
                                    'data_type': 'numeric',
                                    'category': 'sensor',
                                    'sample_value': 20.0
                                })
                            elif meta['type'] == 'gpio_write' and meta.get('pin') == 25 and not any(s['name'] == 'relay_state' for s in available_sensors):
                                available_sensors.append({
                                    'name': 'relay_state',
                                    'display_name': f"{alias} (Relay)",
                                    'unit': '',
                                    'data_type': 'text',
                                    'category': 'control',
                                    'sample_value': 'OFF'
                                })
                    
                    # Fallback to standard sensors for this device type if still missing
                    if device['device_type'] == 'esp32_fermentation':
                        if not any(s['name'] == 'temperature' for s in available_sensors):
                            available_sensors.append({
                                'name': 'temperature', 
                                'display_name': 'Temperature', 
                                'unit': '°C', 
                                'data_type': 'numeric', 
                                'category': 'sensor',
                                'sample_value': 20.0
                            })
                        if not any(s['name'] == 'relay_state' for s in available_sensors):
                            available_sensors.append({
                                'name': 'relay_state', 
                                'display_name': 'Relay State', 
                                'unit': '', 
                                'data_type': 'text', 
                                'category': 'control',
                                'sample_value': 'OFF'
                            })

                # Sort sensors by category and then by name
                available_sensors.sort(key=lambda x: (x['category'], x['name']))
            else:
                logger.warning(f"Failed to poll device {device_id} for sensor data: {response.status_code}")
                # Fallback to predefined sensors
                available_sensors = [
                    {'name': 'sensor.temperature', 'display_name': 'Temperature', 'unit': '°C', 'data_type': 'numeric', 'category': 'sensor'},
                    {'name': 'network.rssi', 'display_name': 'WiFi Signal Strength', 'unit': 'dBm', 'data_type': 'numeric', 'category': 'network'},
                    {'name': 'system.free_heap', 'display_name': 'Free Memory', 'unit': 'bytes', 'data_type': 'numeric', 'category': 'system'},
                    {'name': 'system.uptime_formatted', 'display_name': 'Uptime', 'unit': '', 'data_type': 'text', 'category': 'system'},
                    {'name': 'relay.state', 'display_name': 'Relay State', 'unit': '', 'data_type': 'text', 'category': 'relay'}
                ]
                
        except Exception as e:
            logger.error(f"Error polling device for sensor data: {e}")
            # Fallback to predefined sensors
            available_sensors = [
                {'name': 'sensor.temperature', 'display_name': 'Temperature', 'unit': '°C', 'data_type': 'numeric', 'category': 'sensor'},
                {'name': 'network.rssi', 'display_name': 'WiFi Signal Strength', 'unit': 'dBm', 'data_type': 'numeric', 'category': 'network'},
                {'name': 'system.free_heap', 'display_name': 'Free Memory', 'unit': 'bytes', 'data_type': 'numeric', 'category': 'system'}
            ]
        
        # Generic injection for any alias found in the script but not in the device data
        # This ensures new sensors (like battery) appear in the UI even if the device 
        # hasn't been updated/flashed to report them yet, or if the device is offline.
        existing_names = {s['name'] for s in available_sensors}
        if script_aliases:
            for alias, meta in script_aliases.items():
                if alias not in existing_names:
                    logger.info(f"Injecting missing sensor from script: {alias}")
                    available_sensors.append({
                        'name': alias,
                        'display_name': meta.get('alias', alias).replace('_', ' ').title(),
                        'unit': meta.get('unit', ''),
                        'data_type': meta.get('data_type', 'text'),
                        'category': meta.get('category', 'unknown'),
                        'sample_value': 'N/A'
                    })
        
        return jsonify({
            'sensor_mappings': sensor_mappings,
            'available_sensors': available_sensors,
            'device_name': device['device_name'] if 'device_name' in device.keys() else 'Unknown',
            'device_type': device['device_type'] if 'device_type' in device.keys() else 'Unknown'
        })
        
    except Exception as e:
        logger.error(f"Error getting sensor mappings: {e}", exc_info=True)
        return jsonify({'error': f'Failed to get sensor mappings: {str(e)}'}), 500


@device_api_bp.route('/devices/<int:device_id>/sensor-mappings', methods=['POST'])
def save_sensor_mappings(device_id):
    """Save sensor mappings for a device"""
    try:
        data = request.get_json()
        mappings = data.get('mappings', [])
        
        db = get_db()
        cursor = db.cursor()
        
        # Check if device exists
        cursor.execute('SELECT * FROM RegisteredDevices WHERE id = ?', (device_id,))
        device = cursor.fetchone()
        if not device:
            return jsonify({'error': 'Device not found'}), 404
        
        # Auto-register sensor types for enabled mappings
        # This is where sensor types should be created - when users configure data points
        enabled_sensor_types = []
        for mapping in mappings:
            if mapping.get('enabled', True) and mapping.get('entry_field'):
                enabled_sensor_types.append({
                    'sensor_type': mapping.get('entry_field')
                })
        
        new_sensor_types = []
        if enabled_sensor_types:
            from ..utils.sensor_type_manager import auto_register_sensor_types
            new_sensor_types = auto_register_sensor_types(
                enabled_sensor_types, 
                device['device_name'] if device['device_name'] else f'Device {device_id}'
            )
        
        # Delete existing mappings
        cursor.execute('DELETE FROM DeviceSensorMapping WHERE device_id = ?', (device_id,))
        
        # Insert new mappings
        for mapping in mappings:
            cursor.execute('''
                INSERT INTO DeviceSensorMapping 
                (device_id, sensor_name, entry_field, data_type, unit, enabled)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                device_id,
                mapping.get('sensor_name'),
                mapping.get('entry_field'),
                mapping.get('data_type', 'text'),
                mapping.get('unit', ''),
                mapping.get('enabled', True)
            ))
        
        db.commit()
        
        logger.info(f"Saved {len(mappings)} sensor mappings for device {device_id}")
        
        response_data = {
            'message': f'Saved {len(mappings)} sensor mappings',
            'mappings_count': len(mappings)
        }
        
        if new_sensor_types:
            response_data['new_sensor_types'] = new_sensor_types
            response_data['message'] += f' and created {len(new_sensor_types)} new sensor types'
            logger.info(f"Auto-created sensor types during data point configuration: {new_sensor_types}")
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error saving sensor mappings: {e}", exc_info=True)
        return jsonify({'error': f'Failed to save sensor mappings: {str(e)}'}), 500


@device_api_bp.route('/devices/<int:device_id>/debug-data', methods=['GET'])
def debug_device_data(device_id):
    """Debug endpoint to see raw device data structure"""
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Get device info
        cursor.execute('SELECT * FROM RegisteredDevices WHERE id = ?', (device_id,))
        device = cursor.fetchone()
        if not device:
            return jsonify({'error': 'Device not found'}), 404
        
        # Try to fetch data from device
        device_url = f"http://{device['ip']}"
        if device['device_type'] == 'esp32_fermentation':
            device_url += "/api"
        
        try:
            response = requests.get(device_url, timeout=5)
            response.raise_for_status()
            raw_data = response.json()
        except Exception as e:
            return jsonify({
                'error': f'Could not fetch data from device: {str(e)}',
                'device_ip': device['ip'],
                'endpoint': device_url
            }), 400
        
        # Analyze data structure
        data_paths = _analyze_data_structure(raw_data)
        
        # Get discovered sensor types
        discovered_sensor_types = get_sensor_types_from_device_data(raw_data)
        
        return jsonify({
            'device_name': device['device_name'],
            'device_type': device['device_type'],
            'endpoint': device_url,
            'raw_data': raw_data,
            'data_structure': data_paths,
            'discovered_sensor_types': discovered_sensor_types
        })
        
    except Exception as e:
        logger.error(f"Error debugging device data: {e}", exc_info=True)
        return jsonify({'error': f'Failed to debug device data: {str(e)}'}), 500


def _analyze_data_structure(data, prefix="", max_array_items=5):
    """
    Recursively analyze data structure to find all available paths
    
    Args:
        data: The data structure to analyze
        prefix: Current path prefix
        max_array_items: Maximum number of array items to analyze (default 5)
    
    Returns:
        Dictionary of paths with their metadata
    """
    paths = {}
    
    if isinstance(data, dict):
        for key, value in data.items():
            current_path = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, (dict, list)):
                # Check for complex value object pattern (e.g. {value: 25, alias: "Temp"})
                if isinstance(value, dict) and ('value' in value or 'val' in value):
                    actual_value = value.get('value', value.get('val'))
                    # Don't recurse if it looks like a leaf node with metadata
                    if not isinstance(actual_value, (dict, list)):
                        alias = value.get('alias', value.get('label', value.get('name', value.get('friendly_name'))))
                        unit = value.get('unit', "")
                        
                        # Use the alias as display name if available
                        display_name = alias if alias else key.replace("_", " ").title()
                        category = prefix.split('.')[0] if prefix else "root"
                        
                        # Infer data type
                        data_type = "numeric" if isinstance(actual_value, (int, float)) else "text"
                        
                        paths[current_path] = {
                            'type': type(actual_value).__name__,
                            'value': actual_value,
                            'sample': str(actual_value)[:50] + ('...' if len(str(actual_value)) > 50 else ''),
                            'data_type': data_type,
                            'unit': unit,
                            'display_name': display_name,
                            'category': category
                        }
                        continue

                paths.update(_analyze_data_structure(value, current_path, max_array_items))
            else:
                # Enhanced analysis for ESP32 fermentation controller data
                data_type = "numeric" if isinstance(value, (int, float)) else "text"
                unit = ""
                display_name = key.replace("_", " ").title()
                category = prefix.split('.')[0] if prefix else "root"
                
                # Enhanced unit inference based on key names and ESP32 context
                if "temp" in key.lower():
                    unit = "°C"
                    display_name = "Temperature"
                    if "target" in key.lower():
                        display_name = "Target Temperature"
                    elif "beer" in key.lower():
                        display_name = "Beer Temperature"
                    elif "fridge" in key.lower() or "chamber" in key.lower():
                        display_name = "Chamber Temperature"
                elif "rssi" in key.lower():
                    unit = "dBm"
                    display_name = "WiFi Signal Strength"
                elif "heap" in key.lower():
                    unit = "bytes"
                    display_name = "Free Memory"
                elif key.lower() == "uptime_ms":
                    unit = "ms"
                    display_name = "Uptime (milliseconds)"
                elif key.lower() == "uptime_formatted":
                    display_name = "Uptime"
                elif "buffer_count" in key.lower():
                    display_name = "Buffer Count"
                elif "buffer_max" in key.lower():
                    display_name = "Buffer Max Size"
                elif "target_temp" in key.lower():
                    unit = "°C"
                    display_name = "Target Temperature"
                elif "ip_address" in key.lower():
                    display_name = "IP Address"
                elif "mac_address" in key.lower():
                    display_name = "MAC Address"
                elif "wifi_ssid" in key.lower():
                    display_name = "WiFi Network"
                elif "sensor_interval" in key.lower():
                    if "ms" in key.lower():
                        unit = "ms"
                    elif "seconds" in key.lower():
                        unit = "s"
                    display_name = f"Sensor {key.replace('sensor_interval_', '').replace('_', ' ').title()}"
                elif "ds18b20_devices" in key.lower():
                    display_name = "Connected Temperature Sensors"
                elif "pin" in key.lower():
                    display_name = "Control Pin"
                elif "state" in key.lower():
                    display_name = "Relay State"
                    if "relay" in prefix.lower():
                         display_name = "Relay State"
                    elif "door" in prefix.lower():
                         display_name = "Door State"
                elif "status" in key.lower():
                    display_name = f"{prefix.split('.')[-1].title() if prefix else 'Device'} Status"
                elif "valid" in key.lower():
                    display_name = "Sensor Valid"
                elif "battery_monitoring" in key.lower():
                    display_name = "Battery Monitoring"
                elif "buffer_full" in key.lower():
                    display_name = "Buffer Full"
                elif "heating_pad" in key.lower():
                    display_name = "Heating Pad"
                elif "timestamp" in key.lower():
                    if "formatted" in key.lower():
                        display_name = "Last Update Time"
                    else:
                        display_name = "Timestamp"
                elif "device_id" in key.lower():
                    display_name = "Device ID"
                elif "device_name" in key.lower():
                    display_name = "Device Name"
                elif "sensor_type" in key.lower():
                    display_name = "Sensor Type"
                elif "percent" in key.lower() or key.lower().endswith("%"):
                    unit = "%"
                elif "volt" in key.lower():
                    unit = "V"
                elif "amp" in key.lower():
                    unit = "A"
                elif "humidity" in key.lower():
                    unit = "%"
                    display_name = "Humidity"
                elif "pressure" in key.lower():
                    unit = "hPa"
                    display_name = "Pressure"
                elif "gravity" in key.lower():
                    unit = "SG"
                    display_name = "Specific Gravity"
                elif "abv" in key.lower():
                    unit = "%"
                    display_name = "Alcohol by Volume"
                elif "ph" in key.lower():
                    unit = "pH"
                    display_name = "pH Level"
                elif "co2" in key.lower():
                    unit = "ppm"
                    display_name = "CO2 Level"
                
                paths[current_path] = {
                    'type': type(value).__name__,
                    'value': value,
                    'sample': str(value)[:50] + ('...' if len(str(value)) > 50 else ''),
                    'data_type': data_type,
                    'unit': unit,
                    'display_name': display_name,
                    'category': category
                }
    
    elif isinstance(data, list) and data:
        # Analyze multiple items in list (up to max_array_items)
        items_to_analyze = min(len(data), max_array_items)
        for i in range(items_to_analyze):
            paths.update(_analyze_data_structure(data[i], f"{prefix}[{i}]", max_array_items))
    
    return paths


@device_api_bp.route('/devices/<int:device_id>/link-entry', methods=['POST'])
def link_device_to_entry(device_id):
    """Link a device to automatically record data to a specific entry"""
    try:
        data = request.get_json()
        entry_id = data.get('entry_id')
        
        if not entry_id:
            return jsonify({'error': 'Entry ID is required'}), 400
        
        db = get_db()
        cursor = db.cursor()
        
        # Check if device exists
        cursor.execute('SELECT * FROM RegisteredDevices WHERE id = ?', (device_id,))
        device = cursor.fetchone()
        if not device:
            return jsonify({'error': 'Device not found'}), 404
        
        # Check if entry exists (assuming you have an Entry table)
        cursor.execute('SELECT * FROM Entry WHERE id = ?', (entry_id,))
        entry = cursor.fetchone()
        if not entry:
            return jsonify({'error': 'Entry not found'}), 404
        
        # Check if link already exists
        cursor.execute('SELECT * FROM DeviceEntryLinks WHERE device_id = ? AND entry_id = ?', 
                      (device_id, entry_id))
        existing_link = cursor.fetchone()
        
        if existing_link:
            return jsonify({'error': 'Device is already linked to this entry'}), 400
        
        # Create the link
        cursor.execute('''
            INSERT INTO DeviceEntryLinks (device_id, entry_id, auto_record, created_at)
            VALUES (?, ?, ?, datetime('now'))
        ''', (device_id, entry_id, True))
        
        db.commit()
        
        return jsonify({
            'message': 'Device linked to entry successfully',
            'device_id': device_id,
            'entry_id': entry_id
        })
        
    except Exception as e:
        logger.error(f"Error linking device to entry: {e}", exc_info=True)
        return jsonify({'error': f'Failed to link device to entry: {str(e)}'}), 500


@device_api_bp.route('/devices/<int:device_id>/unlink-entry', methods=['POST'])
def unlink_device_from_entry(device_id):
    """Unlink a device from an entry"""
    try:
        data = request.get_json()
        entry_id = data.get('entry_id')
        
        if not entry_id:
            return jsonify({'error': 'Entry ID is required'}), 400
        
        db = get_db()
        cursor = db.cursor()
        
        # Remove the link
        cursor.execute('DELETE FROM DeviceEntryLinks WHERE device_id = ? AND entry_id = ?', 
                      (device_id, entry_id))
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'Device link not found'}), 404
        
        db.commit()
        
        return jsonify({
            'message': 'Device unlinked from entry successfully',
            'device_id': device_id,
            'entry_id': entry_id
        })
        
    except Exception as e:
        logger.error(f"Error unlinking device from entry: {e}", exc_info=True)
        return jsonify({'error': f'Failed to unlink device from entry: {str(e)}'}), 500


@device_api_bp.route('/entries/<int:entry_id>/linked-devices', methods=['GET'])
def get_linked_devices(entry_id):
    """Get all devices linked to a specific entry"""
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Get linked devices
        cursor.execute('''
            SELECT rd.*, del.auto_record, del.created_at as link_created_at
            FROM RegisteredDevices rd
            JOIN DeviceEntryLinks del ON rd.id = del.device_id
            WHERE del.entry_id = ?
            ORDER BY rd.device_name
        ''', (entry_id,))
        
        devices = [dict(row) for row in cursor.fetchall()]
        
        return jsonify({
            'entry_id': entry_id,
            'linked_devices': devices,
            'count': len(devices)
        })
        
    except Exception as e:
        logger.error(f"Error getting linked devices: {e}", exc_info=True)
        return jsonify({'error': f'Failed to get linked devices: {str(e)}'}), 500
