"""
Range-based Sensor Data API
REST API endpoints for efficient sensor data management using ranges
"""

from flask import Blueprint, request, jsonify
import logging
from app.services.range_based_sensor_service import RangeBasedSensorService

logger = logging.getLogger(__name__)

range_sensor_api = Blueprint('range_sensor_api', __name__)

@range_sensor_api.route('/range_sensor_data', methods=['POST'])
def add_range_sensor_data():
    """
    Add sensor data for multiple entries using range-based linking
    
    Expected JSON:
    {
        "entry_ids": [22, 39, 42],
        "sensor_type": "Temperature",
        "values": [
            {"value": "23.5", "recorded_at": "2025-09-05T10:00:00"},
            {"value": "24.1", "recorded_at": "2025-09-05T10:05:00"}
        ],
        "link_type": "primary",
        "metadata": {"source": "weather_station", "location": "room_1"}
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Validate required fields
        required_fields = ['entry_ids', 'sensor_type', 'values']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        if not isinstance(data['entry_ids'], list) or not data['entry_ids']:
            return jsonify({'error': 'entry_ids must be a non-empty list'}), 400
        
        if not isinstance(data['values'], list) or not data['values']:
            return jsonify({'error': 'values must be a non-empty list'}), 400
        
        # Add the sensor data with range-based linking
        result = RangeBasedSensorService.add_sensor_data_range(
            entry_ids=data['entry_ids'],
            sensor_type=data['sensor_type'],
            values=data['values'],
            link_type=data.get('link_type', 'primary'),
            metadata=data.get('metadata', {})
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': f"Added {result['sensor_data_added']} sensor readings for {result['entries_linked']} entries",
                'data': result
            }), 201
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        logger.error(f"Error in add_range_sensor_data: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@range_sensor_api.route('/entries/<int:entry_id>/range_sensor_data', methods=['GET'])
def get_entry_range_sensor_data(entry_id):
    """
    Get sensor data for an entry using range-based lookup
    
    Query parameters:
    - sensor_type: Optional sensor type filter
    - limit: Optional limit on results (default: 100)
    - offset: Optional offset for pagination (default: 0)
    """
    try:
        sensor_type = request.args.get('sensor_type')
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        sensor_data = RangeBasedSensorService.get_sensor_data_for_entry(
            entry_id=entry_id,
            sensor_type=sensor_type,
            limit=limit,
            offset=offset
        )
        
        return jsonify({
            'success': True,
            'entry_id': entry_id,
            'sensor_data': sensor_data,
            'count': len(sensor_data),
            'pagination': {
                'limit': limit,
                'offset': offset,
                'has_more': len(sensor_data) == limit
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting range sensor data for entry {entry_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@range_sensor_api.route('/entries/<int:entry_id>/range_sensor_summary', methods=['GET'])
def get_entry_range_sensor_summary(entry_id):
    """
    Get sensor data summary for an entry using efficient range queries
    """
    try:
        summary = RangeBasedSensorService.get_sensor_summary_for_entry(entry_id)
        
        return jsonify({
            'success': True,
            'summary': summary
        })
        
    except Exception as e:
        logger.error(f"Error getting range sensor summary for entry {entry_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@range_sensor_api.route('/entries/<int:entry_id>/optimize_ranges', methods=['POST'])
def optimize_entry_ranges(entry_id):
    """
    Optimize sensor data ranges for an entry by merging overlapping/consecutive ranges
    """
    try:
        result = RangeBasedSensorService.optimize_ranges_for_entry(entry_id)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': f"Optimized ranges for entry {entry_id}",
                'optimization_results': result
            })
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        logger.error(f"Error optimizing ranges for entry {entry_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@range_sensor_api.route('/sensor_ranges/<int:start_sensor_id>/<int:end_sensor_id>/entries', methods=['GET'])
def get_entries_for_sensor_range(start_sensor_id, end_sensor_id):
    """
    Get all entries that have links to a sensor ID range
    """
    try:
        if start_sensor_id > end_sensor_id:
            return jsonify({'error': 'start_sensor_id must be <= end_sensor_id'}), 400
        
        entries = RangeBasedSensorService.get_entries_for_sensor_range(start_sensor_id, end_sensor_id)
        
        return jsonify({
            'success': True,
            'sensor_range': {'start': start_sensor_id, 'end': end_sensor_id},
            'entries': entries,
            'count': len(entries)
        })
        
    except Exception as e:
        logger.error(f"Error getting entries for sensor range {start_sensor_id}-{end_sensor_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@range_sensor_api.route('/entries/<int:entry_id>/range_sensor_data', methods=['DELETE'])
def delete_entry_range_sensor_data(entry_id):
    """
    Delete sensor data ranges for an entry
    
    Query parameters:
    - sensor_type: Optional sensor type filter
    """
    try:
        sensor_type = request.args.get('sensor_type')
        
        result = RangeBasedSensorService.delete_sensor_data_range(
            entry_id=entry_id,
            sensor_type=sensor_type
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': f"Deleted {result['deleted_ranges']} ranges for entry {entry_id}",
                'details': result
            })
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        logger.error(f"Error deleting range sensor data for entry {entry_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@range_sensor_api.route('/range_sensor_data/bulk_create', methods=['POST'])
def bulk_create_range_sensor_data():
    """
    Create multiple sensor data ranges in a single operation
    
    Expected JSON:
    {
        "operations": [
            {
                "entry_ids": [22, 39],
                "sensor_type": "Temperature",
                "values": [{"value": "23.5", "recorded_at": "2025-09-05T10:00:00"}],
                "link_type": "primary"
            },
            {
                "entry_ids": [42],
                "sensor_type": "Humidity", 
                "values": [{"value": "65.0", "recorded_at": "2025-09-05T10:00:00"}],
                "link_type": "secondary"
            }
        ]
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'operations' not in data:
            return jsonify({'error': 'Missing operations array'}), 400
        
        operations = data['operations']
        if not isinstance(operations, list):
            return jsonify({'error': 'operations must be an array'}), 400
        
        results = []
        total_success = 0
        total_errors = 0
        
        for i, operation in enumerate(operations):
            try:
                # Validate operation
                required_fields = ['entry_ids', 'sensor_type', 'values']
                for field in required_fields:
                    if field not in operation:
                        results.append({
                            'operation_index': i,
                            'success': False,
                            'error': f'Missing required field: {field}'
                        })
                        total_errors += 1
                        continue
                
                # Execute operation
                result = RangeBasedSensorService.add_sensor_data_range(
                    entry_ids=operation['entry_ids'],
                    sensor_type=operation['sensor_type'],
                    values=operation['values'],
                    link_type=operation.get('link_type', 'primary'),
                    metadata=operation.get('metadata', {})
                )
                
                results.append({
                    'operation_index': i,
                    'success': result['success'],
                    'data': result if result['success'] else None,
                    'error': result.get('error') if not result['success'] else None
                })
                
                if result['success']:
                    total_success += 1
                else:
                    total_errors += 1
                    
            except Exception as e:
                results.append({
                    'operation_index': i,
                    'success': False,
                    'error': str(e)
                })
                total_errors += 1
        
        return jsonify({
            'success': total_errors == 0,
            'summary': {
                'total_operations': len(operations),
                'successful': total_success,
                'failed': total_errors
            },
            'results': results
        }), 200 if total_errors == 0 else 207  # 207 Multi-Status for partial success
        
    except Exception as e:
        logger.error(f"Error in bulk_create_range_sensor_data: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@range_sensor_api.route('/range_sensor_data/stats', methods=['GET'])
def get_range_sensor_stats():
    """
    Get global statistics about range-based sensor data
    """
    try:
        from app.db import get_connection
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Get range statistics
        cursor.execute('''
            SELECT 
                COUNT(*) as total_ranges,
                COUNT(DISTINCT entry_id) as entries_with_ranges,
                COUNT(DISTINCT sensor_type) as sensor_types,
                AVG(end_sensor_id - start_sensor_id + 1) as avg_range_size,
                MAX(end_sensor_id - start_sensor_id + 1) as max_range_size,
                MIN(end_sensor_id - start_sensor_id + 1) as min_range_size
            FROM SensorDataEntryRanges
        ''')
        
        range_stats = dict(cursor.fetchone())
        
        # Get sensor data statistics
        cursor.execute('''
            SELECT 
                COUNT(*) as total_sensor_records,
                COUNT(DISTINCT sensor_type) as unique_sensor_types,
                MIN(recorded_at) as earliest_record,
                MAX(recorded_at) as latest_record
            FROM SharedSensorData
        ''')
        
        sensor_stats = dict(cursor.fetchone())
        
        # Get efficiency metrics
        cursor.execute('''
            SELECT 
                COUNT(*) as old_individual_links,
                'individual_links' as link_type
            FROM SensorDataEntryLinks
            UNION ALL
            SELECT 
                SUM(end_sensor_id - start_sensor_id + 1) as range_covered_readings,
                'range_links' as link_type
            FROM SensorDataEntryRanges
        ''')
        
        efficiency_data = cursor.fetchall()
        
        conn.close()
        
        return jsonify({
            'success': True,
            'statistics': {
                'range_statistics': range_stats,
                'sensor_data_statistics': sensor_stats,
                'efficiency_metrics': [dict(row) for row in efficiency_data]
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting range sensor stats: {e}")
        return jsonify({'error': 'Internal server error'}), 500
