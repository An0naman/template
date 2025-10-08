"""
Shared Sensor Data API Service
Handles sensor data that can be linked to multiple entries efficiently
"""

from flask import current_app, g
import sqlite3
import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

def get_db():
    """Get database connection"""
    if 'db' not in g:
        db_path = current_app.config['DATABASE_PATH']
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
    return g.db

class SharedSensorDataService:
    """Service for managing shared sensor data"""
    
    @staticmethod
    def add_sensor_data(sensor_type: str, value: str, entry_ids: List[int], 
                       recorded_at: Optional[str] = None, source_type: str = 'manual',
                       source_id: Optional[str] = None, metadata: Optional[Dict] = None) -> int:
        """
        Add sensor data that can be linked to multiple entries
        
        Args:
            sensor_type: Type of sensor (e.g., 'Temperature', 'Humidity')
            value: Sensor reading value
            entry_ids: List of entry IDs to link this data to
            recorded_at: ISO timestamp when data was recorded
            source_type: Source of data ('device', 'manual', 'api')
            source_id: ID of the source (device_id, user_id, etc.)
            metadata: Additional metadata as dict
            
        Returns:
            ID of the created SharedSensorData record
        """
        if not sensor_type or not value or not entry_ids:
            raise ValueError("sensor_type, value, and entry_ids are required")
            
        conn = get_db()
        cursor = conn.cursor()
        
        try:
            # Set defaults
            if recorded_at is None:
                recorded_at = datetime.now(timezone.utc).isoformat()
            if metadata is None:
                metadata = {}
                
            # Validate all entry IDs exist and support sensors
            placeholders = ','.join(['?' for _ in entry_ids])
            cursor.execute(f'''
                SELECT e.id, et.has_sensors, et.enabled_sensor_types
                FROM Entry e
                JOIN EntryType et ON e.entry_type_id = et.id
                WHERE e.id IN ({placeholders})
            ''', entry_ids)
            
            entries = cursor.fetchall()
            if len(entries) != len(entry_ids):
                missing_ids = set(entry_ids) - {row['id'] for row in entries}
                raise ValueError(f"Entry IDs not found: {missing_ids}")
            
            # Check if entries support sensors and the specific sensor type
            for entry in entries:
                if not entry['has_sensors']:
                    raise ValueError(f"Entry {entry['id']} does not support sensors")
                
                if entry['enabled_sensor_types']:
                    enabled_types = [t.strip() for t in entry['enabled_sensor_types'].split(',')]
                    if sensor_type not in enabled_types:
                        logger.warning(f"Entry {entry['id']} doesn't have {sensor_type} enabled, but allowing anyway")
            
            # Create shared sensor data record
            cursor.execute('''
                INSERT INTO SharedSensorData (sensor_type, value, recorded_at, source_type, source_id, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (sensor_type, value, recorded_at, source_type, source_id, json.dumps(metadata)))
            
            shared_sensor_id = cursor.lastrowid
            
            # Create links to all specified entries
            for i, entry_id in enumerate(entry_ids):
                link_type = 'primary' if i == 0 else 'secondary'  # First entry is primary
                cursor.execute('''
                    INSERT INTO SensorDataEntryLinks (shared_sensor_data_id, entry_id, link_type)
                    VALUES (?, ?, ?)
                ''', (shared_sensor_id, entry_id, link_type))
            
            conn.commit()
            
            # Auto-register sensor type if needed
            try:
                from ..utils.sensor_type_manager import auto_register_sensor_types
                sensor_data_points = [{'sensor_type': sensor_type}]
                auto_register_sensor_types(sensor_data_points, f"shared sensor data from {source_type}")
            except Exception as e:
                logger.warning(f"Failed to auto-register sensor type: {e}")
            
            logger.info(f"Created shared sensor data {shared_sensor_id} for {len(entry_ids)} entries")
            return shared_sensor_id
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to add shared sensor data: {e}")
            raise
    
    @staticmethod
    def get_sensor_data_for_entry(entry_id: int, sensor_type: Optional[str] = None,
                                 limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get sensor data for a specific entry
        
        Args:
            entry_id: Entry ID to get data for
            sensor_type: Optional filter by sensor type
            limit: Optional limit on number of records
            
        Returns:
            List of sensor data records with metadata
        """
        conn = get_db()
        cursor = conn.cursor()
        
        query = '''
            SELECT ssd.id, ssd.sensor_type, ssd.value, ssd.recorded_at, 
                   ssd.source_type, ssd.source_id, ssd.metadata,
                   sel.link_type, sel.created_at as linked_at,
                   COUNT(sel2.entry_id) as total_linked_entries
            FROM SharedSensorData ssd
            JOIN SensorDataEntryLinks sel ON ssd.id = sel.shared_sensor_data_id
            LEFT JOIN SensorDataEntryLinks sel2 ON ssd.id = sel2.shared_sensor_data_id
            WHERE sel.entry_id = ?
        '''
        params = [entry_id]
        
        if sensor_type:
            query += ' AND ssd.sensor_type = ?'
            params.append(sensor_type)
            
        query += ' GROUP BY ssd.id ORDER BY ssd.recorded_at DESC'
        
        if limit:
            query += ' LIMIT ?'
            params.append(limit)
            
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        result = []
        for row in rows:
            try:
                metadata = json.loads(row['metadata']) if row['metadata'] else {}
            except json.JSONDecodeError:
                metadata = {}
                
            result.append({
                'id': row['id'],
                'sensor_type': row['sensor_type'], 
                'value': row['value'],
                'recorded_at': row['recorded_at'],
                'source_type': row['source_type'],
                'source_id': row['source_id'],
                'metadata': metadata,
                'link_type': row['link_type'],
                'linked_at': row['linked_at'],
                'total_linked_entries': row['total_linked_entries']
            })
            
        return result
    
    @staticmethod
    def link_existing_sensor_data(shared_sensor_id: int, entry_ids: List[int], 
                                 link_type: str = 'secondary') -> int:
        """
        Link existing sensor data to additional entries
        
        Args:
            shared_sensor_id: ID of existing SharedSensorData record
            entry_ids: List of entry IDs to link to
            link_type: Type of link ('primary', 'secondary', 'reference')
            
        Returns:
            Number of new links created
        """
        conn = get_db()
        cursor = conn.cursor()
        
        try:
            # Verify shared sensor data exists
            cursor.execute('SELECT id FROM SharedSensorData WHERE id = ?', (shared_sensor_id,))
            if not cursor.fetchone():
                raise ValueError(f"SharedSensorData {shared_sensor_id} not found")
            
            links_created = 0
            for entry_id in entry_ids:
                try:
                    cursor.execute('''
                        INSERT INTO SensorDataEntryLinks (shared_sensor_data_id, entry_id, link_type)
                        VALUES (?, ?, ?)
                    ''', (shared_sensor_id, entry_id, link_type))
                    links_created += 1
                except sqlite3.IntegrityError:
                    # Link already exists, skip
                    logger.debug(f"Link between sensor {shared_sensor_id} and entry {entry_id} already exists")
                    
            conn.commit()
            logger.info(f"Created {links_created} new sensor data links")
            return links_created
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to link sensor data: {e}")
            raise
    
    @staticmethod
    def unlink_sensor_data(shared_sensor_id: int, entry_id: int) -> bool:
        """
        Remove link between sensor data and an entry
        
        Args:
            shared_sensor_id: ID of SharedSensorData record
            entry_id: Entry ID to unlink
            
        Returns:
            True if link was removed, False if it didn't exist
        """
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM SensorDataEntryLinks 
            WHERE shared_sensor_data_id = ? AND entry_id = ?
        ''', (shared_sensor_id, entry_id))
        
        removed = cursor.rowcount > 0
        
        # If this was the last link, optionally delete the sensor data
        cursor.execute('''
            SELECT COUNT(*) FROM SensorDataEntryLinks 
            WHERE shared_sensor_data_id = ?
        ''', (shared_sensor_id,))
        
        remaining_links = cursor.fetchone()[0]
        if remaining_links == 0:
            logger.info(f"SharedSensorData {shared_sensor_id} has no more links - consider cleanup")
        
        conn.commit()
        return removed
    
    @staticmethod
    def get_sensor_data_summary(entry_id: int) -> Dict[str, Any]:
        """
        Get summary statistics for sensor data linked to an entry
        
        Args:
            entry_id: Entry ID
            
        Returns:
            Summary with counts, types, date ranges, etc.
        """
        conn = get_db()
        cursor = conn.cursor()
        
        # Get basic counts and types
        cursor.execute('''
            SELECT 
                COUNT(DISTINCT ssd.id) as total_readings,
                COUNT(DISTINCT ssd.sensor_type) as sensor_types_count,
                GROUP_CONCAT(DISTINCT ssd.sensor_type) as sensor_types,
                MIN(ssd.recorded_at) as earliest_reading,
                MAX(ssd.recorded_at) as latest_reading,
                COUNT(CASE WHEN sel.link_type = 'primary' THEN 1 END) as primary_links,
                COUNT(CASE WHEN sel.link_type = 'secondary' THEN 1 END) as secondary_links
            FROM SharedSensorData ssd
            JOIN SensorDataEntryLinks sel ON ssd.id = sel.shared_sensor_data_id
            WHERE sel.entry_id = ?
        ''', (entry_id,))
        
        summary = dict(cursor.fetchone())
        
        if summary['sensor_types']:
            summary['sensor_types'] = [t.strip() for t in summary['sensor_types'].split(',')]
        else:
            summary['sensor_types'] = []
            
        return summary
