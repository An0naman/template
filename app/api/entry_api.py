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
                   e.status, e.created_at, e.commenced_at, e.entry_type_id, et.singular_label AS entry_type_label
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
                'commenced_at': row['commenced_at'],
                'entry_type_id': row['entry_type_id'],
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
                   e.status, e.created_at, e.commenced_at, et.singular_label AS entry_type_label, 
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
                'commenced_at': row['commenced_at'],
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
    commenced_at = data.get('commenced_at')  # Optional: when work actually started
    status = data.get('status')

    if not title or not entry_type_id:
        return jsonify({'error': 'Title and Entry Type are required.'}), 400

    conn = get_db()
    cursor = conn.cursor()
    try:
        # If no status provided, get the default state for this entry type
        if not status:
            cursor.execute('''
                SELECT name FROM EntryState
                WHERE entry_type_id = ? AND is_default = 1
                ORDER BY display_order ASC
                LIMIT 1
            ''', (entry_type_id,))
            default_state = cursor.fetchone()
            status = default_state['name'] if default_state else 'Active'
        
        now = datetime.now(timezone.utc).isoformat()
        cursor.execute(
            "INSERT INTO Entry (title, description, entry_type_id, intended_end_date, commenced_at, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (title, description, entry_type_id, intended_end_date, commenced_at, status, now)
        )
        conn.commit()
        # Use main_bp.entry_detail_v2 because it's in a different blueprint (now the default view)
        return jsonify({'message': 'Entry added successfully!', 'redirect': url_for('main.entry_detail_v2', entry_id=cursor.lastrowid)}), 201
    except Exception as e:
        logger.error(f"Error adding entry: {e}", exc_info=True)
        conn.rollback()
        return jsonify({'error': 'An internal error occurred.'}), 500

@entry_api_bp.route('/entries/<int:entry_id>', methods=['GET'])
def get_entry(entry_id):
    """Get a single entry by ID with its entry type information"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT e.id, e.title, e.description, e.intended_end_date, e.actual_end_date, 
                   e.status, e.created_at, e.commenced_at, e.entry_type_id, 
                   et.singular_label AS entry_type_label,
                   et.name AS entry_type_name,
                   et.has_sensors,
                   et.enabled_sensor_types
            FROM Entry e
            JOIN EntryType et ON e.entry_type_id = et.id
            WHERE e.id = ?
        ''', (entry_id,))
        
        row = cursor.fetchone()
        if not row:
            return jsonify({'error': 'Entry not found'}), 404
        
        entry = {
            'id': row['id'],
            'title': row['title'],
            'description': row['description'],
            'intended_end_date': row['intended_end_date'],
            'actual_end_date': row['actual_end_date'],
            'status': row['status'],
            'created_at': row['created_at'],
            'commenced_at': row['commenced_at'],
            'entry_type_id': row['entry_type_id'],
            'entry_type_label': row['entry_type_label'],
            'entry_type_name': row['entry_type_name'],
            'has_sensors': bool(row['has_sensors']),
            'enabled_sensor_types': row['enabled_sensor_types'] or ''
        }
        
        return jsonify(entry)
        
    except Exception as e:
        logger.error(f"Error fetching entry {entry_id}: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@entry_api_bp.route('/entries/<int:entry_id>', methods=['PATCH'])
def update_entry(entry_id):
    data = request.json
    conn = get_db()
    cursor = conn.cursor()

    # Get the current entry to check for status changes
    cursor.execute("SELECT title, status, entry_type_id, commenced_at, actual_end_date FROM Entry WHERE id = ?", (entry_id,))
    current_entry = cursor.fetchone()
    
    if not current_entry:
        return jsonify({'error': 'Entry not found.'}), 404
    
    old_status = current_entry['status']
    entry_title = current_entry['title']
    entry_type_id = current_entry['entry_type_id']

    set_clauses = []
    params = []

    if 'title' in data:
        set_clauses.append("title = ?")
        params.append(data['title'])
    if 'description' in data:
        set_clauses.append("description = ?")
        params.append(data['description'])
    if 'entry_type_id' in data:
        # Validate that the entry_type_id is not None, null, or NaN
        entry_type_id_value = data['entry_type_id']
        if entry_type_id_value is not None and entry_type_id_value != '' and str(entry_type_id_value).lower() != 'nan':
            set_clauses.append("entry_type_id = ?")
            params.append(entry_type_id_value)
        else:
            logger.warning(f"Invalid entry_type_id value received: {entry_type_id_value}. Skipping update.")
    if 'intended_end_date' in data:
        set_clauses.append("intended_end_date = ?")
        params.append(data['intended_end_date'])
    if 'commenced_at' in data:
        set_clauses.append("commenced_at = ?")
        params.append(data['commenced_at'])
    if 'actual_end_date' in data:
        set_clauses.append("actual_end_date = ?")
        params.append(data['actual_end_date'])
    if 'status' in data:
        new_status = data['status']
        set_clauses.append("status = ?")
        params.append(new_status)
        
        # Check if this status has triggers that should set dates
        if new_status != old_status:
            cursor.execute("""
                SELECT sets_commenced, sets_ended
                FROM EntryState
                WHERE entry_type_id = ? AND name = ?
            """, (entry_type_id, new_status))
            
            state_info = cursor.fetchone()
            if state_info:
                # Auto-set commenced_at if status triggers it and it's not already set
                if state_info['sets_commenced'] and not current_entry['commenced_at']:
                    now = datetime.now(timezone.utc).isoformat()
                    set_clauses.append("commenced_at = ?")
                    params.append(now)
                    logger.info(f"Auto-setting commenced_at for entry {entry_id} due to status '{new_status}'")
                
                # Auto-set actual_end_date if status triggers it and it's not already set
                if state_info['sets_ended'] and not current_entry['actual_end_date']:
                    now = datetime.now(timezone.utc).isoformat()
                    set_clauses.append("actual_end_date = ?")
                    params.append(now)
                    logger.info(f"Auto-setting actual_end_date for entry {entry_id} due to status '{new_status}'")

    if not set_clauses:
        return jsonify({'message': 'No fields provided for update.'}), 200

    params.append(entry_id)
    query = f"UPDATE Entry SET {', '.join(set_clauses)} WHERE id = ?"

    try:
        cursor.execute(query, tuple(params))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({'error': 'Entry not found or no changes made.'}), 404
        
        # Check if status changed and create an auto-note
        new_status = data.get('status')
        if new_status and new_status != old_status:
            try:
                # Create automatic note for status change
                note_title = "Status Change"
                note_text = f"Status automatically changed from '{old_status}' to '{new_status}'"
                note_type = "System"  # Use System type for automatic notes
                
                cursor.execute(
                    "INSERT INTO Note (entry_id, note_title, note_text, type, created_at) VALUES (?, ?, ?, ?, ?)",
                    (entry_id, note_title, note_text, note_type, datetime.now(timezone.utc).isoformat())
                )
                conn.commit()
                logger.info(f"Created auto-note for status change on entry {entry_id}: {old_status} -> {new_status}")
            except Exception as e:
                logger.error(f"Error creating auto-note for status change: {e}", exc_info=True)
                # Don't fail the update if note creation fails
        
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
    """Get all sensor data for a specific entry (supports legacy, shared, and range-based data)"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        all_data = []
        
        # Get the entry's enabled sensor types to filter data
        cursor.execute('''
            SELECT et.enabled_sensor_types
            FROM Entry e
            JOIN EntryType et ON e.entry_type_id = et.id
            WHERE e.id = ?
        ''', (entry_id,))
        result = cursor.fetchone()
        enabled_sensor_types = None
        if result and result['enabled_sensor_types']:
            enabled_sensor_types = [t.strip() for t in result['enabled_sensor_types'].split(',')]
        
        # 1. Try to get data from range-based sensor model first (most efficient)
        try:
            from ..services.range_based_sensor_service import RangeBasedSensorService
            range_data = RangeBasedSensorService.get_sensor_data_for_entry(entry_id)
            
            if range_data:
                # Convert to format expected by frontend
                for item in range_data:
                    all_data.append({
                        'id': item['id'],
                        'sensor_type': item['sensor_type'],
                        'value': item['value'],
                        'recorded_at': item['recorded_at'],
                        'source': 'range_based',
                        'link_type': 'primary',  # Range-based doesn't store link_type per reading
                        'total_linked_entries': 1  # Will be calculated if needed
                    })
        except ImportError:
            pass  # Range-based service not available
        
        # 2. Try to get data from shared sensor model (fallback)
        try:
            from ..services.shared_sensor_service import SharedSensorDataService
            shared_data = SharedSensorDataService.get_sensor_data_for_entry(entry_id)
            
            if shared_data:
                # Convert to format expected by frontend
                for item in shared_data:
                    all_data.append({
                        'id': item['id'],
                        'sensor_type': item['sensor_type'],
                        'value': item['value'],
                        'recorded_at': item['recorded_at'],
                        'source': 'shared',
                        'source_type': item.get('source_type'),
                        'source_id': item.get('source_id'),
                        'link_type': item.get('link_type', 'primary'),
                        'total_linked_entries': item.get('total_linked_entries', 1)
                    })
        except ImportError:
            pass  # Fall back to legacy model
        
        # 3. Fall back to legacy SensorData table
        cursor.execute(
            "SELECT id, sensor_type, value, recorded_at FROM SensorData WHERE entry_id = ? ORDER BY recorded_at DESC", 
            (entry_id,)
        )
        sensor_data = cursor.fetchall()
        
        # Add source info for legacy data
        for row in sensor_data:
            all_data.append({
                'id': row['id'],
                'sensor_type': row['sensor_type'],
                'value': row['value'],
                'recorded_at': row['recorded_at'],
                'source': 'legacy',
                'link_type': 'primary',
                'total_linked_entries': 1
            })
        
        # Filter by enabled sensor types if configured
        if enabled_sensor_types is not None:
            all_data = [d for d in all_data if d['sensor_type'] in enabled_sensor_types]
        
        # Sort all data by recorded_at descending
        all_data.sort(key=lambda x: x['recorded_at'], reverse=True)
        
        return jsonify(all_data)
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
        additional_entry_ids = data.get('additional_entry_ids', [])  # New: support multiple entries

        if not sensor_type or not value:
            return jsonify({'error': 'Sensor type and value are required.'}), 400

        conn = get_db()
        cursor = conn.cursor()
        
        # Check if the primary entry is active and supports this sensor type
        cursor.execute('''
            SELECT e.status, et.enabled_sensor_types, et.singular_label
            FROM Entry e
            JOIN EntryType et ON e.entry_type_id = et.id
            WHERE e.id = ?
        ''', (entry_id,))
        entry_result = cursor.fetchone()
        if not entry_result:
            return jsonify({'error': 'Entry not found.'}), 404
        if entry_result['status'] == 'inactive':
            return jsonify({'error': 'Cannot add sensor data to inactive entries.'}), 400
        
        # Validate sensor type is enabled for this entry
        if entry_result['enabled_sensor_types']:
            enabled_types = [t.strip() for t in entry_result['enabled_sensor_types'].split(',')]
            if sensor_type not in enabled_types:
                return jsonify({
                    'error': f'Sensor type "{sensor_type}" is not enabled for {entry_result["singular_label"]}.',
                    'enabled_types': enabled_types
                }), 400

        # Prepare all entry IDs (primary + additional)
        all_entry_ids = [entry_id] + [int(eid) for eid in additional_entry_ids if eid != entry_id]
        
        # Try to use shared sensor data service if available
        try:
            from ..services.shared_sensor_service import SharedSensorDataService
            
            shared_sensor_id = SharedSensorDataService.add_sensor_data(
                sensor_type=sensor_type,
                value=value,
                entry_ids=all_entry_ids,
                recorded_at=recorded_at,
                source_type='manual',
                source_id=f"entry_{entry_id}"
            )
            
            # Check sensor notification rules for primary entry
            try:
                from ..api.notifications_api import check_sensor_rules
                check_sensor_rules(entry_id, sensor_type, value, recorded_at)
            except Exception as e:
                logger.warning(f"Error checking sensor rules for entry {entry_id}: {e}")
            
            message = f'Sensor data added successfully to {len(all_entry_ids)} entries!'
            return jsonify({
                'message': message, 
                'shared_sensor_id': shared_sensor_id,
                'linked_entries': all_entry_ids
            }), 201
            
        except ImportError:
            # Fall back to legacy single-entry model
            pass

        # Legacy fallback - only support single entry
        if additional_entry_ids:
            return jsonify({'error': 'Multiple entry linking not supported in legacy mode.'}), 400

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


@entry_api_bp.route('/filter_by_relationships', methods=['POST'])
def filter_by_relationships():
    """
    Filter entries based on their relationships with other entries.
    
    Request body format:
    {
        "filters": [
            {
                "relationship_def_id": 16,  // Relationship definition ID
                "target_entry_id": 5,        // Target entry ID
                "direction": "to"            // "to" or "from"
            }
        ],
        "logic": "AND"  // "AND" or "OR" - how to combine multiple filters
    }
    
    Returns entry IDs that match the specified relationship filters.
    """
    try:
        data = request.json
        filters = data.get('filters', [])
        logic = data.get('logic', 'AND').upper()
        
        if not filters:
            # No filters, return all entries
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM Entry")
            entry_ids = [row['id'] for row in cursor.fetchall()]
            return jsonify({'entry_ids': entry_ids}), 200
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Collect results from each filter
        filter_result_sets = []
        
        for filter_spec in filters:
            rel_def_id = filter_spec.get('relationship_def_id')
            target_entry_id = filter_spec.get('target_entry_id')
            direction = filter_spec.get('direction', 'to')
            
            if not rel_def_id or not target_entry_id:
                continue
            
            # Query depends on direction
            if direction == 'to':
                # Find entries that have a relationship TO the target
                # (source_entry_id is what we're looking for, target_entry_id is the filter)
                query = """
                    SELECT DISTINCT source_entry_id as entry_id
                    FROM EntryRelationship
                    WHERE relationship_type = ? AND target_entry_id = ?
                """
                cursor.execute(query, (rel_def_id, target_entry_id))
            else:  # direction == 'from'
                # Find entries that have a relationship FROM the target
                # (target_entry_id is what we're looking for, source_entry_id is the filter)
                query = """
                    SELECT DISTINCT target_entry_id as entry_id
                    FROM EntryRelationship
                    WHERE relationship_type = ? AND source_entry_id = ?
                """
                cursor.execute(query, (rel_def_id, target_entry_id))
            
            filter_results = set(row['entry_id'] for row in cursor.fetchall())
            filter_result_sets.append(filter_results)
        
        # Apply logic (AND or OR)
        if not filter_result_sets:
            result_ids = []
        elif logic == 'OR':
            # Union of all result sets (match ANY filter)
            matching_entry_ids = set()
            for result_set in filter_result_sets:
                matching_entry_ids = matching_entry_ids.union(result_set)
            result_ids = list(matching_entry_ids)
        else:  # AND logic
            # Intersection of all result sets (match ALL filters)
            matching_entry_ids = filter_result_sets[0]
            for result_set in filter_result_sets[1:]:
                matching_entry_ids = matching_entry_ids.intersection(result_set)
            result_ids = list(matching_entry_ids)
        
        logger.info(f"Relationship filter ({logic}) returned {len(result_ids)} matching entries")
        return jsonify({'entry_ids': result_ids}), 200
        
    except Exception as e:
        logger.error(f"Error filtering by relationships: {e}", exc_info=True)
        return jsonify({'error': 'An internal error occurred.'}), 500


@entry_api_bp.route('/custom_sql_filter', methods=['POST'])
def custom_sql_filter():
    """
    Filter entries using a custom SQL query (full query or WHERE clause fragment).
    
    Expected JSON payload:
    {
        "full_query": "SELECT DISTINCT e.id FROM Entry e WHERE e.title LIKE '%wine%'"
    }
    OR
    {
        "where_clause": "e.title LIKE '%wine%' AND e.entry_type_id = 2"
    }
    
    Returns:
    {
        "entry_ids": [1, 5, 10],
        "count": 3,
        "warning": "optional warning message"
    }
    """
    try:
        data = request.get_json()
        full_query = data.get('full_query', '').strip()
        where_clause = data.get('where_clause', '').strip()
        
        if not full_query and not where_clause:
            return jsonify({'entry_ids': [], 'count': 0}), 200
        
        # No security restrictions - user knows what they're doing
        query_upper = (full_query if full_query else where_clause).upper()
        
        # Use full query if provided, otherwise build from WHERE clause
        if full_query:
            final_query = full_query
            logger.info(f"Executing full custom SQL query: {final_query}")
        else:
            # Build the query with the custom WHERE clause fragment
            base_query = """
                SELECT DISTINCT e.id 
                FROM Entry e
                LEFT JOIN EntryType et ON e.entry_type_id = et.id
                LEFT JOIN EntryRelationship er_from ON e.id = er_from.source_entry_id
                LEFT JOIN EntryRelationship er_to ON e.id = er_to.target_entry_id
            """
            final_query = f"{base_query} WHERE ({where_clause})"
            logger.info(f"Executing custom SQL query from fragment: {final_query}")
        
        # Execute the query
        cursor = get_db().execute(final_query)
        results = cursor.fetchall()
        
        entry_ids = [row[0] for row in results]
        
        logger.info(f"Custom SQL query returned {len(entry_ids)} entries")
        
        return jsonify({
            'entry_ids': entry_ids,
            'count': len(entry_ids)
        }), 200
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error executing custom SQL query: {error_msg}", exc_info=True)
        return jsonify({
            'error': f'SQL query error: {error_msg}',
            'hint': 'Check your SQL syntax. Use "e" as the Entry table alias.'
        }), 400


@entry_api_bp.route('/entries/<int:entry_id>/drawio', methods=['GET', 'POST'])
def manage_drawio_diagram(entry_id):
    """Get or save Draw.io diagram data for an entry"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Verify entry exists
        cursor.execute("SELECT id FROM Entry WHERE id = ?", (entry_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Entry not found'}), 404
        
        if request.method == 'GET':
            # Retrieve diagram data
            cursor.execute("""
                SELECT diagram_data, updated_at 
                FROM EntryDrawioDiagram 
                WHERE entry_id = ?
            """, (entry_id,))
            
            row = cursor.fetchone()
            if row:
                return jsonify({
                    'entry_id': entry_id,
                    'diagram_data': row['diagram_data'],
                    'updated_at': row['updated_at']
                }), 200
            else:
                return jsonify({
                    'entry_id': entry_id,
                    'diagram_data': None,
                    'updated_at': None
                }), 200
        
        elif request.method == 'POST':
            # Save diagram data
            data = request.get_json()
            diagram_data = data.get('diagram_data', '')
            
            # Check if record exists
            cursor.execute("""
                SELECT entry_id FROM EntryDrawioDiagram WHERE entry_id = ?
            """, (entry_id,))
            
            existing = cursor.fetchone()
            current_time = datetime.now(timezone.utc).isoformat()
            
            if existing:
                # Update existing diagram
                cursor.execute("""
                    UPDATE EntryDrawioDiagram 
                    SET diagram_data = ?, updated_at = ?
                    WHERE entry_id = ?
                """, (diagram_data, current_time, entry_id))
            else:
                # Insert new diagram
                cursor.execute("""
                    INSERT INTO EntryDrawioDiagram (entry_id, diagram_data, created_at, updated_at)
                    VALUES (?, ?, ?, ?)
                """, (entry_id, diagram_data, current_time, current_time))
            
            conn.commit()
            
            return jsonify({
                'success': True,
                'entry_id': entry_id,
                'updated_at': current_time
            }), 200
    
    except Exception as e:
        logger.error(f"Error managing Draw.io diagram for entry {entry_id}: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500