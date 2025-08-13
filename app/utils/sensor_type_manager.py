# app/utils/sensor_type_manager.py
"""
Utility functions for managing sensor types dynamically based on device discovery
"""
import logging
from ..db import get_connection

logger = logging.getLogger(__name__)

def auto_register_sensor_types(sensor_data_points, device_name=None):
    """
    Automatically register sensor types based on discovered device data
    
    Args:
        sensor_data_points: List of sensor data dictionaries with 'sensor_type' field
        device_name: Optional device name for logging
    
    Returns:
        List of newly created sensor types
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Get current sensor types
        cursor.execute("SELECT parameter_value FROM SystemParameters WHERE parameter_name = 'sensor_types'")
        result = cursor.fetchone()
        
        if result and result[0]:
            current_types = [t.strip() for t in result[0].split(',') if t.strip()]
        else:
            current_types = []
        
        # Extract unique sensor types from the data points
        discovered_types = set()
        for point in sensor_data_points:
            if 'sensor_type' in point and point['sensor_type']:
                discovered_types.add(point['sensor_type'].strip())
        
        # Find new types that need to be added
        new_types = []
        for sensor_type in discovered_types:
            if sensor_type not in current_types:
                new_types.append(sensor_type)
                current_types.append(sensor_type)
        
        if new_types:
            # Update the system parameters with new sensor types
            updated_types_str = ','.join(current_types)
            cursor.execute(
                "UPDATE SystemParameters SET parameter_value = ? WHERE parameter_name = 'sensor_types'",
                (updated_types_str,)
            )
            
            # If no sensor_types parameter exists, create it
            if cursor.rowcount == 0:
                cursor.execute(
                    "INSERT INTO SystemParameters (parameter_name, parameter_value) VALUES (?, ?)",
                    ('sensor_types', updated_types_str)
                )
            
            conn.commit()
            
            device_info = f" from device '{device_name}'" if device_name else ""
            logger.info(f"Auto-registered {len(new_types)} new sensor types{device_info}: {', '.join(new_types)}")
        
        return new_types
        
    except Exception as e:
        logger.error(f"Error auto-registering sensor types: {e}", exc_info=True)
        return []

def ensure_sensor_type_exists(sensor_type):
    """
    Ensure a single sensor type exists in the system
    
    Args:
        sensor_type: The sensor type to ensure exists
    
    Returns:
        bool: True if type was created/exists, False on error
    """
    if not sensor_type or not sensor_type.strip():
        return False
        
    return len(auto_register_sensor_types([{'sensor_type': sensor_type.strip()}])) >= 0

def get_sensor_types_from_device_data(device_data):
    """
    Extract potential sensor types from raw device data structure
    
    Args:
        device_data: Raw JSON data from device
        
    Returns:
        List of sensor type strings that could be created
        
    Note: This function extracts the actual field names from device data.
    These should match exactly what users see when configuring data points.
    """
    sensor_types = []
    
    def extract_from_dict(data, prefix=""):
        """Recursively extract sensor types from nested data"""
        if isinstance(data, dict):
            for key, value in data.items():
                # Skip non-sensor data
                if key.lower() in ['device_id', 'device_name', 'timestamp']:
                    continue
                
                # Only include numeric values or meaningful text values
                if isinstance(value, (int, float)) or (isinstance(value, str) and value.strip()):
                    # Build the full field name including nested path
                    if prefix:
                        full_field_name = f"{prefix}.{key}"
                    else:
                        full_field_name = key
                    
                    # Use the actual field name as the sensor type
                    # This ensures what users see in Configure Data Points matches the sensor type
                    if full_field_name not in sensor_types:
                        sensor_types.append(full_field_name)
                
                # Recurse into nested objects
                if isinstance(value, dict):
                    new_prefix = f"{prefix}.{key}" if prefix else key
                    extract_from_dict(value, new_prefix)
                elif isinstance(value, list) and value and isinstance(value[0], dict):
                    new_prefix = f"{prefix}.{key}" if prefix else key
                    extract_from_dict(value[0], new_prefix)
    
    extract_from_dict(device_data)
    return sensor_types

def clean_unused_sensor_types():
    """
    Remove sensor types that are no longer used by any devices or entries
    This is an optional maintenance function
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Get current sensor types
        cursor.execute("SELECT parameter_value FROM SystemParameters WHERE parameter_name = 'sensor_types'")
        result = cursor.fetchone()
        
        if not result or not result[0]:
            return []
        
        current_types = [t.strip() for t in result[0].split(',') if t.strip()]
        
        # Get sensor types actually used in sensor data
        cursor.execute("SELECT DISTINCT sensor_type FROM SensorData")
        used_types = set(row[0] for row in cursor.fetchall())
        
        # Get sensor types used in device mappings
        cursor.execute("SELECT DISTINCT entry_field FROM DeviceSensorMapping WHERE enabled = 1")
        mapped_types = set(row[0] for row in cursor.fetchall())
        
        # Get sensor types used in notification rules
        cursor.execute("SELECT DISTINCT sensor_type FROM NotificationRule WHERE is_active = 1")
        alarm_types = set(row[0] for row in cursor.fetchall())
        
        # Combine all used types
        all_used_types = used_types | mapped_types | alarm_types
        
        # Find unused types
        unused_types = [t for t in current_types if t not in all_used_types]
        
        if unused_types:
            # Remove unused types
            remaining_types = [t for t in current_types if t in all_used_types]
            updated_types_str = ','.join(remaining_types)
            
            cursor.execute(
                "UPDATE SystemParameters SET parameter_value = ? WHERE parameter_name = 'sensor_types'",
                (updated_types_str,)
            )
            conn.commit()
            
            logger.info(f"Cleaned up {len(unused_types)} unused sensor types: {', '.join(unused_types)}")
        
        return unused_types
        
    except Exception as e:
        logger.error(f"Error cleaning unused sensor types: {e}", exc_info=True)
        return []
