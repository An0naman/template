# app/services/sensor_master_service.py
"""
Sensor Master Control Service
==============================

This service provides business logic for the Sensor Master Control system,
including configuration management, sensor registration, and command queueing.

Simplified architecture: No master instances - sensors connect directly to this instance.
"""

import json
import hashlib
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class SensorMasterService:
    """Service for managing sensor master control operations"""
    
    def __init__(self, db_connection):
        """
        Initialize the service with a database connection
        
        Args:
            db_connection: SQLite database connection
        """
        self.conn = db_connection
        self.cursor = self.conn.cursor()
    
    def get_sensor_configuration(self, sensor_id: str) -> Optional[Dict]:
        """
        Get the complete configuration for a sensor.
        
        Priority order:
        1. Sensor-specific configuration
        2. Sensor-type configuration
        3. Local/default configuration (fallback)
        
        Args:
            sensor_id: Unique identifier for the sensor
            
        Returns:
            Dictionary with configuration data or None if not found
        """
        try:
            # Get sensor registration info
            self.cursor.execute('''
                SELECT * FROM SensorRegistration
                WHERE sensor_id = ?
            ''', (sensor_id,))
            
            sensor = self.cursor.fetchone()
            
            if not sensor:
                logger.warning(f"Sensor {sensor_id} not registered")
                return None
            
            # Try to get sensor-specific configuration
            config = self._get_config(sensor_id=sensor_id)
            
            if config:
                return config
            
            # Try to get sensor-type configuration
            config = self._get_config(sensor_type=sensor['sensor_type'])
            
            if config:
                return config
            
            # Fall back to local configuration
            return self._get_fallback_config(sensor_id, sensor['sensor_type'])
            
        except Exception as e:
            logger.error(f"Error getting sensor configuration: {e}", exc_info=True)
            return None
    
    def _get_config(self, sensor_id: str = None, sensor_type: str = None) -> Optional[Dict]:
        """
        Get configuration from database
        
        Args:
            sensor_id: Specific sensor ID (optional)
            sensor_type: Sensor type (optional)
            
        Returns:
            Configuration dictionary or None
        """
        # SensorMasterConfig table has been removed
        return None
    
    def _get_fallback_config(self, sensor_id: str, sensor_type: str) -> Dict:
        """
        Get fallback/local configuration for a sensor
        
        This would typically come from RegisteredDevices or default settings
        
        Args:
            sensor_id: Sensor identifier
            sensor_type: Type of sensor
            
        Returns:
            Default configuration dictionary
        """
        # Check if sensor is registered as a device
        self.cursor.execute('''
            SELECT rd.*, del.entry_id
            FROM RegisteredDevices rd
            LEFT JOIN DeviceEntryLinks del ON rd.id = del.device_id
            WHERE rd.device_id = ?
            LIMIT 1
        ''', (sensor_id,))
        
        device = self.cursor.fetchone()
        
        if device:
            # Build config from registered device settings
            config = {
                'mode': 'local',
                'polling_interval': device['polling_interval'] or 60,
                'device_id': device['id'],
                'entry_id': device['entry_id'] if device['entry_id'] else None,
                'sensor_mappings': self._get_device_sensor_mappings(device['id']),
                '_meta': {
                    'source': 'local_device',
                    'device_name': device['device_name']
                }
            }
            return config
        
        # Return absolute fallback configuration
        return {
            'mode': 'standalone',
            'polling_interval': 60,
            'data_endpoint': None,
            'sensor_mappings': [],
            '_meta': {
                'source': 'fallback',
                'message': 'No configuration available, using defaults'
            }
        }
    
    def _get_device_sensor_mappings(self, device_id: int) -> List[Dict]:
        """Get sensor mappings for a device"""
        self.cursor.execute('''
            SELECT sensor_name, entry_field, data_type, unit, enabled
            FROM DeviceSensorMapping
            WHERE device_id = ? AND enabled = 1
        ''', (device_id,))
        
        return [dict(row) for row in self.cursor.fetchall()]
    
    def create_configuration_template(self, template_name: str,
                                     sensor_type: str = None, sensor_id: str = None,
                                     config_data: Dict = None, priority: int = 100) -> int:
        """
        Create a configuration template for sensors
        
        Args:
            template_name: Name of the configuration template
            sensor_type: Apply to all sensors of this type (optional)
            sensor_id: Apply to specific sensor (optional)
            config_data: Configuration data dictionary
            priority: Priority (lower = higher priority, default 100)
            
        Returns:
            Configuration ID
        """
        # SensorMasterConfig table has been removed
        logger.warning("create_configuration_template called but SensorMasterConfig table is removed")
        return -1
    
    def _get_default_config_template(self, sensor_type: str) -> Dict:
        """Get default configuration template based on sensor type"""
        
        base_config = {
            'polling_interval': 60,
            'data_endpoint': 'http://localhost:5000/api/sensor-data',
            'retry_attempts': 3,
            'retry_delay': 5,
            'sensor_mappings': []
        }
        
        # Customize based on sensor type
        if sensor_type == 'esp32_fermentation':
            base_config['sensor_mappings'] = [
                {
                    'sensor_name': 'sensor.temperature',
                    'entry_field': 'Temperature',
                    'unit': '°C',
                    'data_type': 'float'
                },
                {
                    'sensor_name': 'sensor.target',
                    'entry_field': 'Target Temperature',
                    'unit': '°C',
                    'data_type': 'float'
                },
                {
                    'sensor_name': 'relay.state',
                    'entry_field': 'Relay State',
                    'unit': '',
                    'data_type': 'text'
                }
            ]
        
        return base_config
    
    def get_sensor_status_summary(self) -> Dict:
        """
        Get summary of sensor status
        
        Returns:
            Dictionary with status summary
        """
        query = '''
            SELECT 
                COUNT(*) as total_sensors,
                SUM(CASE WHEN status = 'online' THEN 1 ELSE 0 END) as online,
                SUM(CASE WHEN status = 'offline' THEN 1 ELSE 0 END) as offline,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN datetime(last_check_in) > datetime('now', '-5 minutes') 
                    THEN 1 ELSE 0 END) as active_recently
            FROM SensorRegistration
        '''
        
        self.cursor.execute(query)
        result = self.cursor.fetchone()
        
        return dict(result) if result else {}
    
    def cleanup_stale_sensors(self, hours: int = 24) -> int:
        """
        Mark sensors as offline if they haven't checked in recently
        
        Args:
            hours: Number of hours without check-in to consider stale
            
        Returns:
            Number of sensors marked as offline
        """
        self.cursor.execute('''
            UPDATE SensorRegistration
            SET status = 'offline'
            WHERE status = 'online'
            AND datetime(last_check_in) < datetime('now', '-' || ? || ' hours')
        ''', (hours,))
        
        return self.cursor.rowcount
    
    def generate_config_hash(self, config_data: Dict) -> str:
        """Generate a hash for configuration data"""
        config_str = json.dumps(config_data, sort_keys=True)
        return hashlib.sha256(config_str.encode()).hexdigest()
    
    def has_config_changed(self, sensor_id: str, new_config: Dict) -> bool:
        """Check if configuration has changed for a sensor"""
        new_hash = self.generate_config_hash(new_config)
        
        self.cursor.execute('''
            SELECT config_hash FROM SensorRegistration
            WHERE sensor_id = ?
        ''', (sensor_id,))
        
        result = self.cursor.fetchone()
        
        if not result or not result['config_hash']:
            return True
        
        return result['config_hash'] != new_hash


def get_sensor_master_service(db_connection):
    """
    Factory function to create a SensorMasterService instance
    
    Args:
        db_connection: SQLite database connection
        
    Returns:
        SensorMasterService instance
    """
    return SensorMasterService(db_connection)
