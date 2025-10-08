"""
Shared Sensor Data API endpoints
Provides REST API for managing sensor data that can be shared across multiple entries
"""

from flask import Blueprint, request, jsonify, g, current_app
import sqlite3
import json
import logging
from datetime import datetime, timezone
from ..services.shared_sensor_service import SharedSensorDataService

# Define a Blueprint for Shared Sensor Data API
shared_sensor_api_bp = Blueprint('shared_sensor_api', __name__)

logger = logging.getLogger(__name__)

def get_db():
    if 'db' not in g:
        db_path = current_app.config['DATABASE_PATH']
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
    return g.db

@shared_sensor_api_bp.route('/shared_sensor_data', methods=['POST'])
def create_shared_sensor_data():
    """
    Create sensor data that can be linked to multiple entries
    
    Body:
    {
        "sensor_type": "Temperature",
        "value": "25.5",
        "entry_ids": [101, 102, 103],
        "recorded_at": "2025-09-05T18:00:00Z",
        "source_type": "device",
        "source_id": "ESP32_001",
        "metadata": {"location": "fermentation_room"}
    }
    """
    try:
        data = request.json
        
        # Required fields
        sensor_type = data.get('sensor_type')
        value = data.get('value')
        entry_ids = data.get('entry_ids', [])
        
        # Optional fields
        recorded_at = data.get('recorded_at')
        source_type = data.get('source_type', 'manual')
        source_id = data.get('source_id')
        metadata = data.get('metadata', {})
        
        if not sensor_type or not value or not entry_ids:
            return jsonify({'error': 'sensor_type, value, and entry_ids are required'}), 400
            
        if not isinstance(entry_ids, list) or len(entry_ids) == 0:
            return jsonify({'error': 'entry_ids must be a non-empty array'}), 400
        
        shared_sensor_id = SharedSensorDataService.add_sensor_data(
            sensor_type=sensor_type,
            value=value,
            entry_ids=entry_ids,
            recorded_at=recorded_at,
            source_type=source_type,
            source_id=source_id,
            metadata=metadata
        )
        
        return jsonify({
            'message': f'Sensor data created and linked to {len(entry_ids)} entries',
            'shared_sensor_id': shared_sensor_id,
            'linked_entries': entry_ids
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error creating shared sensor data: {e}", exc_info=True)
        return jsonify({'error': 'An internal error occurred'}), 500

@shared_sensor_api_bp.route('/shared_sensor_data/<int:shared_sensor_id>/link', methods=['POST'])
def link_sensor_data_to_entries(shared_sensor_id):
    """
    Link existing sensor data to additional entries
    
    Body:
    {
        "entry_ids": [104, 105],
        "link_type": "secondary"
    }
    """
    try:
        data = request.json
        entry_ids = data.get('entry_ids', [])
        link_type = data.get('link_type', 'secondary')
        
        if not entry_ids:
            return jsonify({'error': 'entry_ids are required'}), 400
            
        links_created = SharedSensorDataService.link_existing_sensor_data(
            shared_sensor_id=shared_sensor_id,
            entry_ids=entry_ids,
            link_type=link_type
        )
        
        return jsonify({
            'message': f'Created {links_created} new links',
            'links_created': links_created,
            'entry_ids': entry_ids
        })
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error linking sensor data: {e}", exc_info=True)
        return jsonify({'error': 'An internal error occurred'}), 500

@shared_sensor_api_bp.route('/shared_sensor_data/<int:shared_sensor_id>/unlink/<int:entry_id>', methods=['DELETE'])
def unlink_sensor_data_from_entry(shared_sensor_id, entry_id):
    """Remove link between sensor data and an entry"""
    try:
        removed = SharedSensorDataService.unlink_sensor_data(shared_sensor_id, entry_id)
        
        if removed:
            return jsonify({'message': 'Link removed successfully'})
        else:
            return jsonify({'error': 'Link not found'}), 404
            
    except Exception as e:
        logger.error(f"Error unlinking sensor data: {e}", exc_info=True)
        return jsonify({'error': 'An internal error occurred'}), 500

@shared_sensor_api_bp.route('/entries/<int:entry_id>/sensor_summary', methods=['GET'])
def get_entry_sensor_summary(entry_id):
    """Get sensor data summary for an entry"""
    try:
        summary = SharedSensorDataService.get_sensor_data_summary(entry_id)
        return jsonify(summary)
        
    except Exception as e:
        logger.error(f"Error getting sensor summary for entry {entry_id}: {e}", exc_info=True)
        return jsonify({'error': 'An internal error occurred'}), 500

@shared_sensor_api_bp.route('/shared_sensor_data/<int:shared_sensor_id>', methods=['GET'])
def get_shared_sensor_data_details(shared_sensor_id):
    """Get details about shared sensor data including all linked entries"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get sensor data details
        cursor.execute('''
            SELECT id, sensor_type, value, recorded_at, source_type, source_id, metadata, created_at
            FROM SharedSensorData
            WHERE id = ?
        ''', (shared_sensor_id,))
        
        sensor_row = cursor.fetchone()
        if not sensor_row:
            return jsonify({'error': 'Shared sensor data not found'}), 404
            
        # Get all linked entries
        cursor.execute('''
            SELECT sel.entry_id, sel.link_type, sel.created_at as linked_at,
                   e.title as entry_title, et.singular_label as entry_type
            FROM SensorDataEntryLinks sel
            JOIN Entry e ON sel.entry_id = e.id
            JOIN EntryType et ON e.entry_type_id = et.id
            WHERE sel.shared_sensor_data_id = ?
            ORDER BY sel.link_type, sel.created_at
        ''', (shared_sensor_id,))
        
        linked_entries = cursor.fetchall()
        
        # Parse metadata
        try:
            metadata = json.loads(sensor_row['metadata']) if sensor_row['metadata'] else {}
        except json.JSONDecodeError:
            metadata = {}
            
        result = {
            'id': sensor_row['id'],
            'sensor_type': sensor_row['sensor_type'],
            'value': sensor_row['value'],
            'recorded_at': sensor_row['recorded_at'],
            'source_type': sensor_row['source_type'],
            'source_id': sensor_row['source_id'],
            'metadata': metadata,
            'created_at': sensor_row['created_at'],
            'linked_entries': [
                {
                    'entry_id': row['entry_id'],
                    'entry_title': row['entry_title'],
                    'entry_type': row['entry_type'],
                    'link_type': row['link_type'],
                    'linked_at': row['linked_at']
                }
                for row in linked_entries
            ],
            'total_linked_entries': len(linked_entries)
        }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting shared sensor data details: {e}", exc_info=True)
        return jsonify({'error': 'An internal error occurred'}), 500

@shared_sensor_api_bp.route('/shared_sensor_data', methods=['GET'])
def list_shared_sensor_data():
    """
    List shared sensor data with optional filtering
    
    Query params:
    - sensor_type: filter by sensor type
    - source_type: filter by source type  
    - entry_id: filter by linked entry
    - limit: max records to return
    - offset: pagination offset
    """
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Build query with filters
        query = '''
            SELECT DISTINCT ssd.id, ssd.sensor_type, ssd.value, ssd.recorded_at, 
                   ssd.source_type, ssd.source_id, ssd.created_at,
                   COUNT(sel.entry_id) as linked_entry_count
            FROM SharedSensorData ssd
            LEFT JOIN SensorDataEntryLinks sel ON ssd.id = sel.shared_sensor_data_id
        '''
        
        conditions = []
        params = []
        
        if request.args.get('sensor_type'):
            conditions.append('ssd.sensor_type = ?')
            params.append(request.args.get('sensor_type'))
            
        if request.args.get('source_type'):
            conditions.append('ssd.source_type = ?')
            params.append(request.args.get('source_type'))
            
        if request.args.get('entry_id'):
            query += ' JOIN SensorDataEntryLinks sel2 ON ssd.id = sel2.shared_sensor_data_id'
            conditions.append('sel2.entry_id = ?')
            params.append(int(request.args.get('entry_id')))
            
        if conditions:
            query += ' WHERE ' + ' AND '.join(conditions)
            
        query += ' GROUP BY ssd.id ORDER BY ssd.recorded_at DESC'
        
        # Add pagination
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        query += ' LIMIT ? OFFSET ?'
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        result = []
        for row in rows:
            result.append({
                'id': row['id'],
                'sensor_type': row['sensor_type'],
                'value': row['value'], 
                'recorded_at': row['recorded_at'],
                'source_type': row['source_type'],
                'source_id': row['source_id'],
                'created_at': row['created_at'],
                'linked_entry_count': row['linked_entry_count']
            })
            
        return jsonify({
            'data': result,
            'count': len(result),
            'limit': limit,
            'offset': offset
        })
        
    except Exception as e:
        logger.error(f"Error listing shared sensor data: {e}", exc_info=True)
        return jsonify({'error': 'An internal error occurred'}), 500
