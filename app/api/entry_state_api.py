# template_app/app/api/entry_state_api.py
from flask import Blueprint, request, jsonify, g, current_app
import sqlite3
from datetime import datetime, timezone
import logging

# Define a Blueprint for Entry State API
entry_state_api_bp = Blueprint('entry_state_api', __name__)

# Get a logger for this module
logger = logging.getLogger(__name__)

def get_db():
    if 'db' not in g:
        db_path = current_app.config['DATABASE_PATH']
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
    return g.db

@entry_state_api_bp.route('/entry_types/<int:entry_type_id>/states', methods=['GET'])
def get_entry_states(entry_type_id):
    """Get all states for a specific entry type"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, entry_type_id, name, category, color, display_order, is_default, created_at
            FROM EntryState
            WHERE entry_type_id = ?
            ORDER BY display_order ASC, name ASC
        ''', (entry_type_id,))
        
        rows = cursor.fetchall()
        states = []
        for row in rows:
            states.append({
                'id': row['id'],
                'entry_type_id': row['entry_type_id'],
                'name': row['name'],
                'category': row['category'],
                'color': row['color'],
                'display_order': row['display_order'],
                'is_default': bool(row['is_default']),
                'created_at': row['created_at']
            })
        
        return jsonify(states), 200
    except Exception as e:
        logger.error(f"Error fetching entry states: {e}", exc_info=True)
        return jsonify({'error': 'An internal error occurred.'}), 500

@entry_state_api_bp.route('/entry_types/<int:entry_type_id>/states', methods=['POST'])
def create_entry_state(entry_type_id):
    """Create a new state for an entry type"""
    try:
        data = request.json
        name = data.get('name')
        category = data.get('category')
        color = data.get('color', '#6c757d')
        display_order = data.get('display_order', 0)
        is_default = data.get('is_default', 0)
        
        if not name or not category:
            return jsonify({'error': 'Name and category are required.'}), 400
        
        if category not in ['active', 'inactive']:
            return jsonify({'error': 'Category must be either "active" or "inactive".'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Verify entry type exists
        cursor.execute("SELECT id FROM EntryType WHERE id = ?", (entry_type_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Entry type not found.'}), 404
        
        # If this state is set as default, unset any existing default for this entry type
        if is_default:
            cursor.execute(
                "UPDATE EntryState SET is_default = 0 WHERE entry_type_id = ?",
                (entry_type_id,)
            )
        
        cursor.execute('''
            INSERT INTO EntryState (entry_type_id, name, category, color, display_order, is_default, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (entry_type_id, name, category, color, display_order, is_default, datetime.now(timezone.utc).isoformat()))
        
        conn.commit()
        
        return jsonify({
            'message': 'State created successfully!',
            'state_id': cursor.lastrowid
        }), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': 'A state with this name already exists for this entry type.'}), 400
    except Exception as e:
        logger.error(f"Error creating entry state: {e}", exc_info=True)
        conn.rollback()
        return jsonify({'error': 'An internal error occurred.'}), 500

@entry_state_api_bp.route('/entry_types/<int:entry_type_id>/states/<int:state_id>', methods=['PUT'])
def update_entry_state(entry_type_id, state_id):
    """Update an existing state"""
    try:
        data = request.json
        conn = get_db()
        cursor = conn.cursor()
        
        # Verify state exists and belongs to this entry type
        cursor.execute(
            "SELECT id FROM EntryState WHERE id = ? AND entry_type_id = ?",
            (state_id, entry_type_id)
        )
        if not cursor.fetchone():
            return jsonify({'error': 'State not found.'}), 404
        
        set_clauses = []
        params = []
        
        if 'name' in data:
            set_clauses.append("name = ?")
            params.append(data['name'])
        if 'category' in data:
            if data['category'] not in ['active', 'inactive']:
                return jsonify({'error': 'Category must be either "active" or "inactive".'}), 400
            set_clauses.append("category = ?")
            params.append(data['category'])
        if 'color' in data:
            set_clauses.append("color = ?")
            params.append(data['color'])
        if 'display_order' in data:
            set_clauses.append("display_order = ?")
            params.append(data['display_order'])
        if 'is_default' in data:
            is_default = data['is_default']
            # If setting as default, unset any existing default
            if is_default:
                cursor.execute(
                    "UPDATE EntryState SET is_default = 0 WHERE entry_type_id = ? AND id != ?",
                    (entry_type_id, state_id)
                )
            set_clauses.append("is_default = ?")
            params.append(1 if is_default else 0)
        
        if not set_clauses:
            return jsonify({'message': 'No fields provided for update.'}), 200
        
        params.append(state_id)
        params.append(entry_type_id)
        query = f"UPDATE EntryState SET {', '.join(set_clauses)} WHERE id = ? AND entry_type_id = ?"
        
        cursor.execute(query, tuple(params))
        conn.commit()
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'State not found or no changes made.'}), 404
        
        return jsonify({'message': 'State updated successfully!'}), 200
    except sqlite3.IntegrityError:
        return jsonify({'error': 'A state with this name already exists for this entry type.'}), 400
    except Exception as e:
        logger.error(f"Error updating entry state: {e}", exc_info=True)
        conn.rollback()
        return jsonify({'error': 'An internal error occurred.'}), 500

@entry_state_api_bp.route('/entry_types/<int:entry_type_id>/states/<int:state_id>', methods=['DELETE'])
def delete_entry_state(entry_type_id, state_id):
    """Delete a state"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if this state is in use by any entries
        cursor.execute('''
            SELECT COUNT(*) as count
            FROM Entry e
            JOIN EntryState es ON e.status = es.name
            WHERE es.id = ? AND es.entry_type_id = ? AND e.entry_type_id = ?
        ''', (state_id, entry_type_id, entry_type_id))
        
        result = cursor.fetchone()
        if result and result['count'] > 0:
            return jsonify({
                'error': f'Cannot delete state. It is currently used by {result["count"]} entry/entries.'
            }), 400
        
        # Check if there are at least 2 states before deletion
        cursor.execute(
            "SELECT COUNT(*) as count FROM EntryState WHERE entry_type_id = ?",
            (entry_type_id,)
        )
        state_count = cursor.fetchone()['count']
        
        if state_count <= 1:
            return jsonify({'error': 'Cannot delete the last state. Each entry type must have at least one state.'}), 400
        
        # Delete the state
        cursor.execute(
            "DELETE FROM EntryState WHERE id = ? AND entry_type_id = ?",
            (state_id, entry_type_id)
        )
        conn.commit()
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'State not found.'}), 404
        
        return jsonify({'message': 'State deleted successfully!'}), 200
    except Exception as e:
        logger.error(f"Error deleting entry state: {e}", exc_info=True)
        conn.rollback()
        return jsonify({'error': 'An internal error occurred.'}), 500

@entry_state_api_bp.route('/entries/<int:entry_id>/available_states', methods=['GET'])
def get_available_states_for_entry(entry_id):
    """Get available states for a specific entry based on its entry type"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get the entry's type
        cursor.execute("SELECT entry_type_id FROM Entry WHERE id = ?", (entry_id,))
        entry = cursor.fetchone()
        
        if not entry:
            return jsonify({'error': 'Entry not found.'}), 404
        
        entry_type_id = entry['entry_type_id']
        
        # Get all states for this entry type
        cursor.execute('''
            SELECT id, name, category, color, display_order, is_default
            FROM EntryState
            WHERE entry_type_id = ?
            ORDER BY display_order ASC, name ASC
        ''', (entry_type_id,))
        
        rows = cursor.fetchall()
        states = []
        for row in rows:
            states.append({
                'id': row['id'],
                'name': row['name'],
                'category': row['category'],
                'color': row['color'],
                'display_order': row['display_order'],
                'is_default': bool(row['is_default'])
            })
        
        return jsonify(states), 200
    except Exception as e:
        logger.error(f"Error fetching available states: {e}", exc_info=True)
        return jsonify({'error': 'An internal error occurred.'}), 500
