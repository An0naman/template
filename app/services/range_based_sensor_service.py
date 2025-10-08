"""
Range-based Sensor Data Service
Provides efficient sensor data management using sensor ID ranges instead of individual links
"""

import sqlite3
import json
import logging
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Union
from app.db import get_connection

logger = logging.getLogger(__name__)

class RangeBasedSensorService:
    """
    Service for managing sensor data using efficient range-based linking
    Maps entries to sensor ID ranges instead of individual sensor records
    """
    
    @staticmethod
    def add_sensor_data_range(entry_ids: List[int], sensor_type: str, values: List[Dict], 
                             link_type: str = 'primary', metadata: Dict = None) -> Dict:
        """
        Add sensor data for multiple entries using range-based linking
        
        Args:
            entry_ids: List of entry IDs to link
            sensor_type: Type of sensor data
            values: List of sensor readings (dicts with 'value', 'recorded_at', etc.)
            link_type: Type of link ('primary', 'secondary', 'reference')
            metadata: Additional metadata for the range
            
        Returns:
            Dict with operation results
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            # Add sensor data records
            sensor_ids = []
            for value_data in values:
                cursor.execute('''
                    INSERT INTO SharedSensorData 
                    (sensor_type, value, recorded_at, source_type, source_id, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    sensor_type,
                    value_data.get('value'),
                    value_data.get('recorded_at', datetime.now().isoformat()),
                    value_data.get('source_type', 'manual'),
                    value_data.get('source_id'),
                    json.dumps(value_data.get('metadata', {}))
                ))
                sensor_ids.append(cursor.lastrowid)
            
            # Create ranges for each entry
            ranges_created = []
            for entry_id in entry_ids:
                if sensor_ids:
                    start_sensor_id = min(sensor_ids)
                    end_sensor_id = max(sensor_ids)
                    
                    cursor.execute('''
                        INSERT INTO SensorDataEntryRanges 
                        (entry_id, sensor_type, start_sensor_id, end_sensor_id, link_type, metadata)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        entry_id, sensor_type, start_sensor_id, end_sensor_id, 
                        link_type, json.dumps(metadata or {})
                    ))
                    
                    ranges_created.append({
                        'range_id': cursor.lastrowid,
                        'entry_id': entry_id,
                        'start_sensor_id': start_sensor_id,
                        'end_sensor_id': end_sensor_id,
                        'sensor_count': len(sensor_ids)
                    })
            
            conn.commit()
            
            return {
                'success': True,
                'sensor_data_added': len(sensor_ids),
                'sensor_ids': sensor_ids,
                'ranges_created': ranges_created,
                'entries_linked': len(entry_ids)
            }
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error adding range-based sensor data: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()
    
    @staticmethod
    def get_sensor_data_for_entry(entry_id: int, sensor_type: str = None, 
                                  limit: int = None, offset: int = 0) -> List[Dict]:
        """
        Get sensor data for an entry using range-based lookup
        Much more efficient than individual link queries
        
        Args:
            entry_id: Entry ID
            sensor_type: Optional sensor type filter
            limit: Optional limit on results
            offset: Optional offset for pagination
            
        Returns:
            List of sensor data records
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            # Build query with range-based joins
            query = '''
                SELECT DISTINCT ssd.* 
                FROM SharedSensorData ssd
                JOIN SensorDataEntryRanges sder ON ssd.id BETWEEN sder.start_sensor_id AND sder.end_sensor_id
                WHERE sder.entry_id = ?
            '''
            params = [entry_id]
            
            if sensor_type:
                query += ' AND sder.sensor_type = ? AND ssd.sensor_type = ?'
                params.extend([sensor_type, sensor_type])
            
            query += ' ORDER BY ssd.recorded_at DESC'
            
            if limit:
                query += ' LIMIT ? OFFSET ?'
                params.extend([limit, offset])
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"Error getting sensor data for entry {entry_id}: {e}")
            return []
        finally:
            conn.close()
    
    @staticmethod
    def get_sensor_summary_for_entry(entry_id: int) -> Dict:
        """
        Get sensor data summary for an entry using efficient range queries
        
        Args:
            entry_id: Entry ID
            
        Returns:
            Summary statistics
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            # Get range summary
            cursor.execute('''
                SELECT 
                    sder.sensor_type,
                    COUNT(*) as range_count,
                    MIN(sder.start_sensor_id) as earliest_sensor_id,
                    MAX(sder.end_sensor_id) as latest_sensor_id,
                    SUM(sder.end_sensor_id - sder.start_sensor_id + 1) as total_readings_in_ranges,
                    sder.link_type
                FROM SensorDataEntryRanges sder
                WHERE sder.entry_id = ?
                GROUP BY sder.sensor_type, sder.link_type
            ''', (entry_id,))
            
            range_stats = cursor.fetchall()
            
            # Get actual sensor data statistics
            cursor.execute('''
                SELECT 
                    ssd.sensor_type,
                    COUNT(*) as actual_readings,
                    MIN(ssd.recorded_at) as earliest_reading,
                    MAX(ssd.recorded_at) as latest_reading
                FROM SharedSensorData ssd
                JOIN SensorDataEntryRanges sder ON ssd.id BETWEEN sder.start_sensor_id AND sder.end_sensor_id
                WHERE sder.entry_id = ?
                GROUP BY ssd.sensor_type
            ''', (entry_id,))
            
            actual_stats = cursor.fetchall()
            
            # Combine statistics
            summary = {
                'entry_id': entry_id,
                'range_statistics': [dict(row) for row in range_stats],
                'actual_statistics': [dict(row) for row in actual_stats],
                'sensor_types': list(set(row['sensor_type'] for row in actual_stats)),
                'total_ranges': len(range_stats),
                'total_actual_readings': sum(row['actual_readings'] for row in actual_stats)
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting sensor summary for entry {entry_id}: {e}")
            return {'entry_id': entry_id, 'error': str(e)}
        finally:
            conn.close()
    
    @staticmethod
    def optimize_ranges_for_entry(entry_id: int) -> Dict:
        """
        Optimize sensor data ranges for an entry by merging overlapping/consecutive ranges
        
        Args:
            entry_id: Entry ID to optimize
            
        Returns:
            Optimization results
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            # Get all ranges for the entry
            cursor.execute('''
                SELECT * FROM SensorDataEntryRanges 
                WHERE entry_id = ? 
                ORDER BY sensor_type, start_sensor_id
            ''', (entry_id,))
            
            ranges = cursor.fetchall()
            optimizations = []
            
            # Group by sensor type
            ranges_by_type = {}
            for range_row in ranges:
                sensor_type = range_row['sensor_type']
                if sensor_type not in ranges_by_type:
                    ranges_by_type[sensor_type] = []
                ranges_by_type[sensor_type].append(dict(range_row))
            
            # Optimize each sensor type
            for sensor_type, type_ranges in ranges_by_type.items():
                optimized_ranges = RangeBasedSensorService._merge_overlapping_ranges(type_ranges)
                
                if len(optimized_ranges) < len(type_ranges):
                    # Delete old ranges
                    range_ids = [r['id'] for r in type_ranges]
                    cursor.execute(f'''
                        DELETE FROM SensorDataEntryRanges 
                        WHERE id IN ({','.join(['?'] * len(range_ids))})
                    ''', range_ids)
                    
                    # Insert optimized ranges
                    for opt_range in optimized_ranges:
                        cursor.execute('''
                            INSERT INTO SensorDataEntryRanges 
                            (entry_id, sensor_type, start_sensor_id, end_sensor_id, link_type, metadata)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (
                            entry_id, sensor_type, 
                            opt_range['start_sensor_id'], opt_range['end_sensor_id'],
                            opt_range['link_type'], json.dumps(opt_range['metadata'])
                        ))
                    
                    optimizations.append({
                        'sensor_type': sensor_type,
                        'original_ranges': len(type_ranges),
                        'optimized_ranges': len(optimized_ranges),
                        'reduction': len(type_ranges) - len(optimized_ranges)
                    })
            
            conn.commit()
            
            return {
                'success': True,
                'entry_id': entry_id,
                'optimizations': optimizations,
                'total_reduction': sum(opt['reduction'] for opt in optimizations)
            }
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error optimizing ranges for entry {entry_id}: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()
    
    @staticmethod
    def _merge_overlapping_ranges(ranges: List[Dict]) -> List[Dict]:
        """
        Merge overlapping or consecutive ranges
        
        Args:
            ranges: List of range dictionaries
            
        Returns:
            List of merged ranges
        """
        if not ranges:
            return []
        
        # Sort by start_sensor_id
        sorted_ranges = sorted(ranges, key=lambda r: r['start_sensor_id'])
        merged = [sorted_ranges[0].copy()]
        
        for current in sorted_ranges[1:]:
            last_merged = merged[-1]
            
            # Check if current range overlaps or is consecutive with last merged range
            if (current['start_sensor_id'] <= last_merged['end_sensor_id'] + 1 and
                current['link_type'] == last_merged['link_type']):
                # Merge ranges
                last_merged['end_sensor_id'] = max(last_merged['end_sensor_id'], current['end_sensor_id'])
                # Merge metadata
                last_metadata = json.loads(last_merged.get('metadata', '{}'))
                current_metadata = json.loads(current.get('metadata', '{}'))
                merged_metadata = {**last_metadata, **current_metadata, 'merged': True}
                last_merged['metadata'] = merged_metadata
            else:
                # No overlap, add as new range
                merged.append(current.copy())
        
        return merged
    
    @staticmethod
    def get_entries_for_sensor_range(start_sensor_id: int, end_sensor_id: int) -> List[Dict]:
        """
        Get all entries that have links to a sensor ID range
        
        Args:
            start_sensor_id: Start of sensor ID range
            end_sensor_id: End of sensor ID range
            
        Returns:
            List of entries with their range links
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT 
                    e.id as entry_id,
                    e.title,
                    e.description,
                    sder.sensor_type,
                    sder.start_sensor_id,
                    sder.end_sensor_id,
                    sder.link_type,
                    sder.metadata
                FROM Entry e
                JOIN SensorDataEntryRanges sder ON e.id = sder.entry_id
                WHERE sder.start_sensor_id <= ? AND sder.end_sensor_id >= ?
                ORDER BY e.id, sder.sensor_type
            ''', (end_sensor_id, start_sensor_id))
            
            results = cursor.fetchall()
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"Error getting entries for sensor range {start_sensor_id}-{end_sensor_id}: {e}")
            return []
        finally:
            conn.close()
    
    @staticmethod
    def delete_sensor_data_range(entry_id: int, sensor_type: str = None) -> Dict:
        """
        Delete sensor data ranges for an entry
        
        Args:
            entry_id: Entry ID
            sensor_type: Optional sensor type filter
            
        Returns:
            Deletion results
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            if sensor_type:
                cursor.execute('''
                    DELETE FROM SensorDataEntryRanges 
                    WHERE entry_id = ? AND sensor_type = ?
                ''', (entry_id, sensor_type))
            else:
                cursor.execute('''
                    DELETE FROM SensorDataEntryRanges 
                    WHERE entry_id = ?
                ''', (entry_id,))
            
            deleted_count = cursor.rowcount
            conn.commit()
            
            return {
                'success': True,
                'deleted_ranges': deleted_count,
                'entry_id': entry_id,
                'sensor_type': sensor_type
            }
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error deleting sensor ranges for entry {entry_id}: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()
