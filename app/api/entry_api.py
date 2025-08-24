# template_app/app/api/entry_api.py
from flask import Blueprint, request, jsonify, g, url_for, current_app
import sqlite3
from datetime import datetime, timezone
import logging
from ..utils.sensor_type_manager import auto_register_sensor_types

# Define a Blueprint for Entry API
entry_api_bp = Blueprint('entry_api', __name__)

# Get a logger for this module
logger = logging.getLogger(__name__)

def get_db():
    if 'db' not in g:
        db_path = current_app.config['DATABASE_PATH']
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
    return g.db

@entry_api_bp.route('/entries', methods=['GET'])
def get_all_entries():
    """Get all entries"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT e.id, e.title, e.description, e.intended_end_date, e.actual_end_date, 
                   e.status, e.created_at, et.singular_label AS entry_type_label
            FROM Entry e
            JOIN EntryType et ON e.entry_type_id = et.id
            ORDER BY e.created_at DESC
        ''')
        
        rows = cursor.fetchall()
        entries = []
        for row in rows:
            entries.append({
                'id': row['id'],
                'name': row['title'],  # Using 'name' for consistency with frontend expectations
                'title': row['title'],
                'description': row['description'],
                'intended_end_date': row['intended_end_date'],
                'actual_end_date': row['actual_end_date'],
                'status': row['status'],
                'created_at': row['created_at'],
                'entry_type_label': row['entry_type_label']
            })
        
        return jsonify(entries)
        
    except Exception as e:
        logger.error(f"Error fetching entries: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@entry_api_bp.route('/entries/sensor-enabled', methods=['GET'])
def get_sensor_enabled_entries():
    """Get entries that belong to entry types with sensors enabled"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT e.id, e.title, e.description, e.intended_end_date, e.actual_end_date, 
                   e.status, e.created_at, et.singular_label AS entry_type_label, 
                   et.enabled_sensor_types
            FROM Entry e
            JOIN EntryType et ON e.entry_type_id = et.id
            WHERE et.has_sensors = 1 AND et.enabled_sensor_types IS NOT NULL AND et.enabled_sensor_types != ''
            ORDER BY e.created_at DESC
        ''')
        
        rows = cursor.fetchall()
        entries = []
        for row in rows:
            entries.append({
                'id': row['id'],
                'name': row['title'],  # Using 'name' for consistency with frontend expectations
                'title': row['title'],
                'description': row['description'],
                'intended_end_date': row['intended_end_date'],
                'actual_end_date': row['actual_end_date'],
                'status': row['status'],
                'created_at': row['created_at'],
                'entry_type_label': row['entry_type_label'],
                'enabled_sensor_types': row['enabled_sensor_types']
            })
        
        return jsonify(entries)
        
    except Exception as e:
        logger.error(f"Error fetching sensor-enabled entries: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@entry_api_bp.route('/entries', methods=['POST'])
def add_entry():
    data = request.json
    title = data.get('title')
    description = data.get('description')
    entry_type_id = data.get('entry_type_id')
    intended_end_date = data.get('intended_end_date')
    status = data.get('status', 'active')

    if not title or not entry_type_id:
        return jsonify({'error': 'Title and Entry Type are required.'}), 400

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO Entry (title, description, entry_type_id, intended_end_date, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (title, description, entry_type_id, intended_end_date, status, datetime.now(timezone.utc).isoformat())
        )
        conn.commit()
        # Use main_bp.entry_detail_page because it's in a different blueprint
        return jsonify({'message': 'Entry added successfully!', 'redirect': url_for('main.entry_detail_page', entry_id=cursor.lastrowid)}), 201
    except Exception as e:
        logger.error(f"Error adding entry: {e}", exc_info=True)
        conn.rollback()
        return jsonify({'error': 'An internal error occurred.'}), 500

@entry_api_bp.route('/entries/<int:entry_id>', methods=['PATCH'])
def update_entry(entry_id):
    data = request.json
    conn = get_db()
    cursor = conn.cursor()

    set_clauses = []
    params = []

    if 'title' in data:
        set_clauses.append("title = ?")
        params.append(data['title'])
    if 'description' in data:
        set_clauses.append("description = ?")
        params.append(data['description'])
    if 'entry_type_id' in data:
        set_clauses.append("entry_type_id = ?")
        params.append(data['entry_type_id'])
    if 'intended_end_date' in data:
        set_clauses.append("intended_end_date = ?")
        params.append(data['intended_end_date'])
    if 'actual_end_date' in data:
        set_clauses.append("actual_end_date = ?")
        params.append(data['actual_end_date'])
    if 'status' in data:
        set_clauses.append("status = ?")
        params.append(data['status'])

    if not set_clauses:
        return jsonify({'message': 'No fields provided for update.'}), 200

    params.append(entry_id)
    query = f"UPDATE Entry SET {', '.join(set_clauses)} WHERE id = ?"

    try:
        cursor.execute(query, tuple(params))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({'error': 'Entry not found or no changes made.'}), 404
        return jsonify({'message': 'Entry updated successfully!'}), 200
    except Exception as e:
        logger.error(f"Error updating entry {entry_id}: {e}", exc_info=True)
        conn.rollback()
        return jsonify({'error': 'An internal error occurred.'}), 500

@entry_api_bp.route('/entries/<int:entry_id>', methods=['DELETE'])
def delete_entry(entry_id):
    conn = get_db()
    cursor = conn.cursor()
    try:
        # Delete related notes
        cursor.execute("DELETE FROM Note WHERE entry_id = ?", (entry_id,))
        # Delete related entry relationships (from either side)
        cursor.execute("DELETE FROM EntryRelationship WHERE source_entry_id = ? OR target_entry_id = ?", (entry_id, entry_id))
        # Finally, delete the entry
        cursor.execute("DELETE FROM Entry WHERE id = ?", (entry_id,))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({'error': 'Entry not found.'}), 404
        return jsonify({'message': 'Entry and its related data deleted successfully!'}), 200
    except Exception as e:
        logger.error(f"Error deleting entry {entry_id}: {e}", exc_info=True)
        conn.rollback()
        return jsonify({'error': 'An internal error occurred.'}), 500

@entry_api_bp.route('/search_entries', methods=['GET'])
def search_entries():
    query = request.args.get('q', '').strip()
    entry_type_id = request.args.get('entry_type_id', type=int)
    conn = get_db()
    cursor = conn.cursor()
    results = []

    search_query_param = f"%{query}%" # Correct way to use LIKE with parameters
    sql = '''
        SELECT e.id, e.title, et.singular_label AS entry_type_label
        FROM Entry e
        JOIN EntryType et ON e.entry_type_id = et.id
        WHERE (e.title LIKE ? OR e.description LIKE ?)
    '''
    params = [search_query_param, search_query_param]

    if entry_type_id:
        sql += " AND e.entry_type_id = ?"
        params.append(entry_type_id)

    sql += " LIMIT 10"

    try:
        cursor.execute(sql, tuple(params))
        rows = cursor.fetchall()
        for row in rows:
            results.append({
                'id': row['id'],
                'title': row['title'],
                'entry_type_label': row['entry_type_label']
            })
        return jsonify(results)
    except Exception as e:
        logger.error(f"Error searching entries: {e}", exc_info=True)
        return jsonify({'error': 'An internal error occurred during search.'}), 500

# --- Sensor Data Endpoints ---

@entry_api_bp.route('/entries/<int:entry_id>/sensor_data', methods=['GET'])
def get_sensor_data_for_entry(entry_id):
    """Get all sensor data for a specific entry"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, sensor_type, value, recorded_at FROM SensorData WHERE entry_id = ? ORDER BY recorded_at DESC", 
            (entry_id,)
        )
        sensor_data = cursor.fetchall()
        return jsonify([dict(row) for row in sensor_data])
    except Exception as e:
        logger.error(f"Error fetching sensor data for entry {entry_id}: {e}", exc_info=True)
        return jsonify({'error': 'An internal error occurred while fetching sensor data.'}), 500

@entry_api_bp.route('/entries/<int:entry_id>/sensor_data', methods=['POST'])
def add_sensor_data_to_entry(entry_id):
    """Add sensor data to a specific entry"""
    try:
        data = request.json
        sensor_type = data.get('sensor_type')
        value = data.get('value')
        recorded_at = data.get('recorded_at', datetime.now(timezone.utc).isoformat())

        if not sensor_type or not value:
            return jsonify({'error': 'Sensor type and value are required.'}), 400

        conn = get_db()
        cursor = conn.cursor()
        
        # Check if the entry is active - don't allow sensor data for inactive entries
        cursor.execute('SELECT status FROM Entry WHERE id = ?', (entry_id,))
        entry_result = cursor.fetchone()
        if not entry_result:
            return jsonify({'error': 'Entry not found.'}), 404
        if entry_result['status'] == 'inactive':
            return jsonify({'error': 'Cannot add sensor data to inactive entries.'}), 400

        # Auto-register the sensor type if it doesn't exist
        sensor_data_points = [{'sensor_type': sensor_type}]
        new_types = auto_register_sensor_types(sensor_data_points, f"manual entry for entry {entry_id}")
        if new_types:
            logger.info(f"Auto-registered sensor type '{sensor_type}' from manual entry")
        
        cursor.execute(
            "INSERT INTO SensorData (entry_id, sensor_type, value, recorded_at) VALUES (?, ?, ?, ?)",
            (entry_id, sensor_type, value, recorded_at)
        )
        conn.commit()
        sensor_id = cursor.lastrowid
        
        # Check sensor notification rules
        try:
            from ..api.notifications_api import check_sensor_rules
            check_sensor_rules(entry_id, sensor_type, value, recorded_at)
        except Exception as e:
            logger.warning(f"Error checking sensor rules for entry {entry_id}: {e}")
            # Don't fail the sensor data creation if notification checking fails
        
        return jsonify({'message': 'Sensor data added successfully!', 'sensor_id': sensor_id}), 201
        
    except sqlite3.IntegrityError:
        # This occurs if entry_id doesn't exist due to FOREIGN KEY constraint
        conn.rollback()
        return jsonify({'error': 'Entry not found for adding sensor data.'}), 404
    except Exception as e:
        logger.error(f"Error adding sensor data to entry {entry_id}: {e}", exc_info=True)
        conn.rollback()
        return jsonify({'error': 'An internal error occurred.'}), 500

@entry_api_bp.route('/sensor_data/<int:sensor_id>', methods=['DELETE'])
def delete_sensor_data(sensor_id):
    """Delete a specific sensor data record"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM SensorData WHERE id = ?", (sensor_id,))
        if cursor.rowcount == 0:
            return jsonify({'error': 'Sensor data not found.'}), 404
        
        conn.commit()
        return jsonify({'message': 'Sensor data deleted successfully!'}), 200
        
    except Exception as e:
        logger.error(f"Error deleting sensor data {sensor_id}: {e}", exc_info=True)
        conn.rollback()
        return jsonify({'error': 'An internal error occurred.'}), 500