# template_app/app/api/entry_type_api.py
from flask import Blueprint, request, jsonify, g, current_app
import sqlite3
import logging

# Define a Blueprint for EntryType API
entry_type_api_bp = Blueprint('entry_type_api', __name__)

# Get a logger for this module
logger = logging.getLogger(__name__)

def get_db():
    if 'db' not in g:
        db_path = current_app.config['DATABASE_PATH']
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
    return g.db

@entry_type_api_bp.route('/entry_types', methods=['GET'])
def get_entry_types_api():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, singular_label, plural_label, description, note_types, is_primary, has_sensors, enabled_sensor_types FROM EntryType ORDER BY singular_label")
    entry_types_rows = cursor.fetchall()
    entry_types_list = []
    for row in entry_types_rows:
        entry_types_list.append(dict(row))
    return jsonify(entry_types_list)

@entry_type_api_bp.route('/entry_types', methods=['POST'])
def add_entry_type():
    data = request.json
    name = data.get('name')
    singular_label = data.get('singular_label')
    plural_label = data.get('plural_label')
    description = data.get('description')
    note_types = data.get('note_types', 'General')
    is_primary = int(data.get('is_primary', 0))
    has_sensors = int(data.get('has_sensors', 0))

    if not all([name, singular_label, plural_label]):
        return jsonify({'error': 'Name, singular label, and plural label are required.'}), 400

    conn = get_db()
    cursor = conn.cursor()

    try:
        if is_primary:
            cursor.execute("UPDATE EntryType SET is_primary = 0 WHERE is_primary = 1")

        cursor.execute(
            "INSERT INTO EntryType (name, singular_label, plural_label, description, note_types, is_primary, has_sensors) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (name, singular_label, plural_label, description, note_types, is_primary, has_sensors)
        )
        conn.commit()
        return jsonify({'message': 'Entry type added successfully!', 'id': cursor.lastrowid}), 201
    except sqlite3.IntegrityError:
        conn.rollback()
        return jsonify({'error': f'Entry type with name "{name}" already exists.'}), 409
    except Exception as e:
        logger.error(f"Error adding entry type: {e}", exc_info=True)
        conn.rollback()
        return jsonify({'error': 'An internal error occurred.'}), 500

@entry_type_api_bp.route('/entry_types/<int:entry_type_id>', methods=['PATCH'])
def update_entry_type(entry_type_id):
    data = request.json
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM EntryType WHERE id = ?", (entry_type_id,))
    existing_type = cursor.fetchone()
    if not existing_type:
        return jsonify({'error': 'Entry type not found.'}), 404

    set_clauses = []
    params = []

    if 'name' in data:
        set_clauses.append("name = ?")
        params.append(data['name'])
    if 'singular_label' in data:
        set_clauses.append("singular_label = ?")
        params.append(data['singular_label'])
    if 'plural_label' in data:
        set_clauses.append("plural_label = ?")
        params.append(data['plural_label'])
    if 'description' in data:
        set_clauses.append("description = ?")
        params.append(data['description'])
    if 'note_types' in data:
        set_clauses.append("note_types = ?")
        params.append(data['note_types'])

    if 'is_primary' in data:
        is_primary = int(data['is_primary'])
        if is_primary:
            # If this type is being set as primary, unset others
            cursor.execute("UPDATE EntryType SET is_primary = 0 WHERE is_primary = 1 AND id != ?", (entry_type_id,))
        set_clauses.append("is_primary = ?")
        params.append(is_primary)
    
    if 'has_sensors' in data:
        set_clauses.append("has_sensors = ?")
        params.append(int(data['has_sensors']))
    
    if 'enabled_sensor_types' in data:
        set_clauses.append("enabled_sensor_types = ?")
        params.append(data['enabled_sensor_types'])

    if not set_clauses:
        return jsonify({'message': 'No fields provided for update.'}), 200

    params.append(entry_type_id)
    query = f"UPDATE EntryType SET {', '.join(set_clauses)} WHERE id = ?"

    try:
        cursor.execute(query, tuple(params))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({'error': 'Entry type not found or no changes made.'}), 404
        return jsonify({'message': 'Entry type updated successfully!'}), 200
    except sqlite3.IntegrityError:
        conn.rollback()
        return jsonify({'error': 'An entry type with that name already exists.'}), 409
    except Exception as e:
        logger.error(f"Error updating entry type {entry_type_id}: {e}", exc_info=True)
        conn.rollback()
        return jsonify({'error': 'An internal error occurred.'}), 500

@entry_type_api_bp.route('/entry_types/<int:entry_type_id>', methods=['DELETE'])
def delete_entry_type(entry_type_id):
    conn = get_db()
    cursor = conn.cursor()

    try:
        # Check for dependencies in 'Entry' table
        cursor.execute("SELECT COUNT(*) FROM Entry WHERE entry_type_id = ?", (entry_type_id,))
        entry_count = cursor.fetchone()[0]
        if entry_count > 0:
            return jsonify({'error': f'Cannot delete entry type. {entry_count} entries are linked to it. Please delete linked entries first.'}), 409

        # Check for dependencies in 'RelationshipDefinition' table
        cursor.execute("SELECT COUNT(*) FROM RelationshipDefinition WHERE entry_type_id_from = ? OR entry_type_id_to = ?", (entry_type_id, entry_type_id))
        rel_def_count = cursor.fetchone()[0]
        if rel_def_count > 0:
            return jsonify({'error': f'Cannot delete entry type. {rel_def_count} relationship definitions are linked to it. Please delete linked relationship definitions first.'}), 409

        cursor.execute("DELETE FROM EntryType WHERE id = ?", (entry_type_id,))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({'error': 'Entry type not found.'}), 404
        return jsonify({'message': 'Entry type deleted successfully!'}), 200
    except Exception as e:
        logger.error(f"Error deleting entry type {entry_type_id}: {e}", exc_info=True)
        conn.rollback()
        return jsonify({'error': 'An internal error occurred.'}), 500