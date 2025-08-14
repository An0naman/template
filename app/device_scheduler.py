# app/device_scheduler.py

import threading
import time
import requests
import sqlite3
import logging
from datetime import datetime, timedelta
from .db import get_connection

logger = logging.getLogger(__name__)

class DevicePollingScheduler:
    """Background scheduler for polling ESP32 devices"""
    
    def __init__(self):
        self.running = False
        self.thread = None
        self.poll_interval = 30  # Check every 30 seconds for devices to poll
        self.app = None  # Will store the Flask app instance
        
    def init_app(self, app):
        """Initialize with Flask app instance"""
        self.app = app
        
    def start(self):
        """Start the polling scheduler"""
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._polling_loop, daemon=True)
        self.thread.start()
        logger.info("Device polling scheduler started")
        
    def stop(self):
        """Stop the polling scheduler"""
        self.running = False
        if self.thread:
            self.thread.join()
        logger.info("Device polling scheduler stopped")
        
    def _polling_loop(self):
        """Main polling loop"""
        while self.running:
            try:
                if self.app:
                    with self.app.app_context():
                        self._poll_devices()
                else:
                    logger.error("No app context available for device polling")
            except Exception as e:
                logger.error(f"Error in polling loop: {e}", exc_info=True)
            
            # Sleep for the poll interval
            time.sleep(self.poll_interval)
    
    def _poll_devices(self):
        """Poll all enabled devices that are due for polling"""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Get devices that need polling
            now = datetime.now()
            
            # Find devices that:
            # 1. Have polling enabled
            # 2. Are linked to at least one entry (via DeviceEntryLinks table)
            # 3. Are not disabled
            # 4. Haven't been polled recently (based on their polling_interval)
            cursor.execute('''
                SELECT DISTINCT rd.* 
                FROM RegisteredDevices rd
                INNER JOIN DeviceEntryLinks del ON rd.id = del.device_id
                WHERE rd.polling_enabled = 1 
                AND rd.status != 'disabled'
                AND (
                    rd.last_poll_success IS NULL 
                    OR datetime(rd.last_poll_success, '+' || rd.polling_interval || ' seconds') <= datetime('now')
                )
            ''')
            
            devices_to_poll = cursor.fetchall()
            logger.debug(f"Found {len(devices_to_poll)} devices due for polling")
            
            for device in devices_to_poll:
                try:
                    self._poll_device(device, cursor)
                except Exception as e:
                    logger.error(f"Error polling device {device['device_name']}: {e}")
                    # Update device with error status
                    cursor.execute('''
                        UPDATE RegisteredDevices 
                        SET status = 'offline', last_poll_error = ?
                        WHERE id = ?
                    ''', (str(e), device['id']))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error in _poll_devices: {e}", exc_info=True)
    
    def _poll_device(self, device, cursor):
        """Poll a single device and store the data"""
        try:
            logger.debug(f"Polling device {device['device_name']}")
            
            # Use appropriate endpoint based on device type
            endpoint = "/api" if device['device_type'] == 'esp32_fermentation' else "/data"
            response = requests.get(f"http://{device['ip']}{endpoint}", timeout=10)
            response.raise_for_status()
            device_data = response.json()

            timestamp = datetime.now().isoformat()
            stored_count = 0
            
            # Extract and store sensor data based on device type
            if device['device_type'] == 'esp32_fermentation':
                stored_count = self._store_esp32_fermentation_data(
                    device, device_data, timestamp, cursor
                )
            
            # Update device status
            cursor.execute('''
                UPDATE RegisteredDevices 
                SET last_seen = ?, status = 'online', last_poll_success = ?, last_poll_error = NULL
                WHERE id = ?
            ''', (timestamp, timestamp, device['id']))
            
            logger.debug(f"Successfully polled {device['device_name']}, stored {stored_count} sensors")
            
        except requests.RequestException as e:
            # Network/HTTP error
            cursor.execute('''
                UPDATE RegisteredDevices 
                SET status = 'offline', last_poll_error = ?
                WHERE id = ?
            ''', (f"Connection error: {str(e)}", device['id']))
            raise
        
        except Exception as e:
            # Other errors
            cursor.execute('''
                UPDATE RegisteredDevices 
                SET last_poll_error = ?
                WHERE id = ?
            ''', (f"Data processing error: {str(e)}", device['id']))
            raise
    
    def _store_esp32_fermentation_data(self, device, device_data, timestamp, cursor):
        """Store data from ESP32 fermentation controller for all linked entries"""
        stored_count = 0
        
        try:
            # Get all linked entry IDs for this device
            cursor.execute('''
                SELECT entry_id FROM DeviceEntryLinks WHERE device_id = ?
            ''', (device['id'],))
            linked_entries = cursor.fetchall()
            
            if not linked_entries:
                logger.warning(f"Device {device['device_name']} has no linked entries")
                return stored_count
            
            # Get enabled sensor mappings for this device
            cursor.execute('''
                SELECT sensor_name, entry_field, data_type, unit, enabled 
                FROM DeviceSensorMapping 
                WHERE device_id = ? AND enabled = 1
            ''', (device['id'],))
            sensor_mappings = cursor.fetchall()
            
            # If no specific mappings exist, use default behavior for backward compatibility
            if not sensor_mappings:
                return self._store_default_esp32_data(device, device_data, timestamp, cursor, linked_entries)
            
            entry_ids = [row['entry_id'] for row in linked_entries]
            logger.debug(f"Storing data for device {device['device_name']} to entries: {entry_ids} using {len(sensor_mappings)} sensor mappings")
            
            # Store data for each linked entry using sensor mappings
            for entry_id in entry_ids:
                for mapping in sensor_mappings:
                    sensor_name = mapping['sensor_name']
                    sensor_type = mapping['entry_field']
                    unit = mapping['unit'] or ''
                    
                    # Extract value based on sensor name from device data
                    value = self._extract_sensor_value(device_data, sensor_name, unit)
                    
                    if value is not None:
                        cursor.execute('''
                            INSERT INTO SensorData (entry_id, sensor_type, value, recorded_at)
                            VALUES (?, ?, ?, ?)
                        ''', (entry_id, sensor_type, value, timestamp))
                        stored_count += 1
                        
                        # Check sensor notification rules for each data point
                        try:
                            from .api.notifications_api import check_sensor_rules_with_connection
                            check_sensor_rules_with_connection(cursor, entry_id, sensor_type, value, timestamp)
                        except Exception as e:
                            logger.warning(f"Error checking sensor rules for entry {entry_id}: {e}")
                            # Don't fail the data collection if notification checking fails
            
            return stored_count
            
        except Exception as e:
            logger.error(f"Error storing ESP32 data: {e}", exc_info=True)
            return stored_count
    
    def _store_default_esp32_data(self, device, device_data, timestamp, cursor, linked_entries):
        """Store default ESP32 data when no sensor mappings are configured"""
        stored_count = 0
        entry_ids = [row['entry_id'] for row in linked_entries]
        
        try:
            # Store data for each linked entry
            for entry_id in entry_ids:
                # Temperature data
                if ('sensor' in device_data and 
                    device_data['sensor'].get('valid') and
                    'temperature' in device_data['sensor']):
                    
                    temp_value = device_data['sensor']['temperature']
                    temp_formatted = f"{temp_value}°C"
                    cursor.execute('''
                        INSERT INTO SensorData (entry_id, sensor_type, value, recorded_at)
                        VALUES (?, ?, ?, ?)
                    ''', (
                        entry_id,
                        'Temperature',
                        temp_formatted,
                        timestamp
                    ))
                    stored_count += 1
                    
                    # Check sensor notification rules
                    try:
                        from .api.notifications_api import check_sensor_rules_with_connection
                        check_sensor_rules_with_connection(cursor, entry_id, 'Temperature', temp_formatted, timestamp)
                    except Exception as e:
                        logger.warning(f"Error checking sensor rules for Temperature: {e}")
                
                # Target temperature (if different from current)
                if ('sensor' in device_data and 
                    'target' in device_data['sensor']):
                    
                    target_temp = device_data['sensor']['target']
                    target_formatted = f"{target_temp}°C"
                    cursor.execute('''
                        INSERT INTO SensorData (entry_id, sensor_type, value, recorded_at)
                        VALUES (?, ?, ?, ?)
                    ''', (
                        entry_id,
                        'Target Temperature',
                        target_formatted,
                        timestamp
                    ))
                    stored_count += 1
                    
                    # Check sensor notification rules
                    try:
                        from .api.notifications_api import check_sensor_rules_with_connection
                        check_sensor_rules_with_connection(cursor, entry_id, 'Target Temperature', target_formatted, timestamp)
                    except Exception as e:
                        logger.warning(f"Error checking sensor rules for Target Temperature: {e}")
                
                # Relay/Heating status
                if 'relay' in device_data and 'state' in device_data['relay']:
                    relay_state = device_data['relay']['state']
                    cursor.execute('''
                        INSERT INTO SensorData (entry_id, sensor_type, value, recorded_at)
                        VALUES (?, ?, ?, ?)
                    ''', (
                        entry_id,
                        'Heating Status',
                        relay_state,
                        timestamp
                    ))
                    stored_count += 1
                    
                    # Check sensor notification rules
                    try:
                        from .api.notifications_api import check_sensor_rules_with_connection
                        check_sensor_rules_with_connection(cursor, entry_id, 'Heating Status', relay_state, timestamp)
                    except Exception as e:
                        logger.warning(f"Error checking sensor rules for Heating Status: {e}")
                
                # System information (less frequent - only store every 10th poll)
                if 'system' in device_data:
                    system_data = device_data['system']
                    
                    # WiFi signal strength
                    if 'wifi_rssi' in system_data:
                        wifi_rssi = system_data['wifi_rssi']
                        wifi_formatted = f"{wifi_rssi} dBm"
                        cursor.execute('''
                            INSERT INTO SensorData (entry_id, sensor_type, value, recorded_at)
                            VALUES (?, ?, ?, ?)
                        ''', (
                            entry_id,
                            'WiFi Signal',
                            wifi_formatted,
                            timestamp
                        ))
                        stored_count += 1
                        
                        # Check sensor notification rules
                        try:
                            from .api.notifications_api import check_sensor_rules_with_connection
                            check_sensor_rules_with_connection(cursor, entry_id, 'WiFi Signal', wifi_formatted, timestamp)
                        except Exception as e:
                            logger.warning(f"Error checking sensor rules for WiFi Signal: {e}")
                        
                        # Free heap (memory)
                        if 'free_heap' in system_data:
                            free_heap = system_data['free_heap']
                            heap_formatted = f"{free_heap} bytes"
                            cursor.execute('''
                                INSERT INTO SensorData (entry_id, sensor_type, value, recorded_at)
                                VALUES (?, ?, ?, ?)
                            ''', (
                                entry_id,
                                'Free Memory',
                                heap_formatted,
                                timestamp
                            ))
                            stored_count += 1
                            
                            # Check sensor notification rules
                            try:
                                from .api.notifications_api import check_sensor_rules_with_connection
                                check_sensor_rules_with_connection(cursor, entry_id, 'Free Memory', heap_formatted, timestamp)
                            except Exception as e:
                                logger.warning(f"Error checking sensor rules for Free Memory: {e}")
                    
                    # Store device status
                    device_status = device_data.get('device_status', 'unknown')
                    cursor.execute('''
                        INSERT INTO SensorData (entry_id, sensor_type, value, recorded_at)
                        VALUES (?, ?, ?, ?)
                    ''', (
                        entry_id,
                        'Device Status',
                        device_status,
                        timestamp
                    ))
                    stored_count += 1
                    
                    # Check sensor notification rules
                    try:
                        from .api.notifications_api import check_sensor_rules_with_connection
                        check_sensor_rules_with_connection(cursor, entry_id, 'Device Status', device_status, timestamp)
                    except Exception as e:
                        logger.warning(f"Error checking sensor rules for Device Status: {e}")
            
            logger.info(f"Stored {stored_count} sensor readings for device {device['device_name']} across {len(entry_ids)} entries")
            return stored_count
            
        except Exception as e:
            logger.error(f"Error storing ESP32 data for device {device['device_name']}: {e}")
            raise
    
    def _extract_sensor_value(self, device_data, sensor_name, unit):
        """Extract sensor value from device data based on sensor name using dot notation paths"""
        try:
            logger.debug(f"Extracting sensor value for '{sensor_name}' from device data keys: {list(device_data.keys()) if isinstance(device_data, dict) else type(device_data)}")
            
            # Handle direct sensor mapping using dot notation paths
            value = device_data
            
            # Split the sensor name by dots to navigate nested structure
            path_parts = sensor_name.split('.')
            logger.debug(f"Following path: {path_parts}")
            
            for i, key in enumerate(path_parts):
                if isinstance(value, dict) and key in value:
                    old_value = value
                    value = value[key]
                    logger.debug(f"Step {i+1}: Found key '{key}' -> {value} (type: {type(value)})")
                else:
                    logger.warning(f"Step {i+1}: Key '{key}' not found in {type(value)}")
                    if isinstance(value, dict):
                        logger.debug(f"Available keys at this level: {list(value.keys())}")
                    else:
                        logger.debug(f"Current value is not a dict: {value}")
                    return None
            
            logger.debug(f"Final extracted value: {value}")
            
            # Format value with unit if provided
            if value is not None and unit:
                if 'temp' in sensor_name.lower() and unit == '°C':
                    formatted_value = f"{value}°C"
                elif 'rssi' in sensor_name.lower() and unit == 'dBm':
                    formatted_value = f"{value} dBm"
                elif 'heap' in sensor_name.lower() and unit == 'bytes':
                    formatted_value = f"{value} bytes"
                elif unit:
                    formatted_value = f"{value} {unit}"
                else:
                    formatted_value = str(value)
            else:
                formatted_value = str(value) if value is not None else None
            
            logger.debug(f"Formatted value: {formatted_value}")
            return formatted_value
            
        except Exception as e:
            logger.error(f"Error extracting sensor value for {sensor_name}: {e}", exc_info=True)
            return None

# Global scheduler instance
device_scheduler = DevicePollingScheduler()

def start_device_polling(app=None):
    """Start the device polling scheduler"""
    if app:
        device_scheduler.init_app(app)
    device_scheduler.start()

def stop_device_polling():
    """Stop the device polling scheduler"""
    device_scheduler.stop()
