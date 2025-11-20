# template_app/app/api/kanban_api.py
"""
Kanban API Blueprint
Provides endpoints for managing kanban boards and columns
"""

from flask import Blueprint, request, jsonify, g, current_app
import sqlite3
import json
import logging
from datetime import datetime

# Define a Blueprint for Kanban API
kanban_api_bp = Blueprint('kanban_api', __name__)

# Get a logger for this module
logger = logging.getLogger(__name__)

def get_db():
    """Get database connection"""
    if 'db' not in g:
        db_path = current_app.config['DATABASE_PATH']
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
    return g.db

# ============================================================================
# Kanban Board Management Endpoints
# ============================================================================

@kanban_api_bp.route('/kanban/boards', methods=['GET'])
def get_kanban_boards():
    """Get all kanban boards"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT kb.id, kb.name, kb.description, kb.entry_type_id, kb.is_default,
                   kb.created_at, kb.updated_at,
                   et.singular_label AS entry_type_label,
                   et.name AS entry_type_name
            FROM KanbanBoard kb
            JOIN EntryType et ON kb.entry_type_id = et.id
            ORDER BY kb.is_default DESC, kb.name ASC
        """)
        
        boards = []
        for row in cursor.fetchall():
            boards.append({
                'id': row['id'],
                'name': row['name'],
                'description': row['description'],
                'entry_type_id': row['entry_type_id'],
                'entry_type_label': row['entry_type_label'],
                'entry_type_name': row['entry_type_name'],
                'is_default': bool(row['is_default']),
                'created_at': row['created_at'],
                'updated_at': row['updated_at']
            })
        
        return jsonify(boards), 200
        
    except Exception as e:
        logger.error(f"Error getting kanban boards: {e}", exc_info=True)
        return jsonify({'error': 'Failed to get kanban boards'}), 500

@kanban_api_bp.route('/kanban/boards/<int:board_id>', methods=['GET'])
def get_kanban_board(board_id):
    """Get a specific kanban board with its columns"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get board
        cursor.execute("""
            SELECT kb.id, kb.name, kb.description, kb.entry_type_id, kb.is_default,
                   kb.created_at, kb.updated_at,
                   et.singular_label AS entry_type_label,
                   et.name AS entry_type_name
            FROM KanbanBoard kb
            JOIN EntryType et ON kb.entry_type_id = et.id
            WHERE kb.id = ?
        """, (board_id,))
        
        board_row = cursor.fetchone()
        if not board_row:
            return jsonify({'error': 'Kanban board not found'}), 404
        
        # Get columns for this board
        cursor.execute("""
            SELECT kc.id, kc.board_id, kc.state_name, kc.display_order, kc.wip_limit,
                   kc.created_at,
                   es.color, es.category
            FROM KanbanColumn kc
            LEFT JOIN EntryState es ON es.entry_type_id = ? AND es.name = kc.state_name
            WHERE kc.board_id = ?
            ORDER BY kc.display_order, kc.id
        """, (board_row['entry_type_id'], board_id))
        
        columns = []
        for row in cursor.fetchall():
            columns.append({
                'id': row['id'],
                'board_id': row['board_id'],
                'state_name': row['state_name'],
                'display_order': row['display_order'],
                'wip_limit': row['wip_limit'],
                'color': row['color'],
                'category': row['category'],
                'created_at': row['created_at']
            })
        
        board = {
            'id': board_row['id'],
            'name': board_row['name'],
            'description': board_row['description'],
            'entry_type_id': board_row['entry_type_id'],
            'entry_type_label': board_row['entry_type_label'],
            'entry_type_name': board_row['entry_type_name'],
            'is_default': bool(board_row['is_default']),
            'created_at': board_row['created_at'],
            'updated_at': board_row['updated_at'],
            'columns': columns
        }
        
        return jsonify(board), 200
        
    except Exception as e:
        logger.error(f"Error getting kanban board: {e}", exc_info=True)
        return jsonify({'error': 'Failed to get kanban board'}), 500

@kanban_api_bp.route('/kanban/boards', methods=['POST'])
def create_kanban_board():
    """Create a new kanban board"""
    try:
        data = request.get_json()
        
        if not data.get('name'):
            return jsonify({'error': 'Board name is required'}), 400
        
        if not data.get('entry_type_id'):
            return jsonify({'error': 'Entry type is required'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if this should be the default board
        is_default = data.get('is_default', False)
        if is_default:
            # Unset ALL other default boards (only one default allowed globally)
            cursor.execute("""
                UPDATE KanbanBoard 
                SET is_default = 0 
                WHERE is_default = 1
            """)
        
        # Create the board
        cursor.execute("""
            INSERT INTO KanbanBoard (name, description, entry_type_id, is_default)
            VALUES (?, ?, ?, ?)
        """, (data['name'], data.get('description', ''), data['entry_type_id'], 1 if is_default else 0))
        
        board_id = cursor.lastrowid
        
        # If columns are provided, create them
        if 'columns' in data and data['columns']:
            for i, column in enumerate(data['columns']):
                cursor.execute("""
                    INSERT INTO KanbanColumn (board_id, state_name, display_order, wip_limit)
                    VALUES (?, ?, ?, ?)
                """, (board_id, column['state_name'], column.get('display_order', i), column.get('wip_limit')))
        
        conn.commit()
        
        return jsonify({
            'id': board_id,
            'message': 'Kanban board created successfully'
        }), 201
        
    except sqlite3.IntegrityError as e:
        logger.error(f"Integrity error creating kanban board: {e}")
        return jsonify({'error': 'A board with this name already exists'}), 400
    except Exception as e:
        logger.error(f"Error creating kanban board: {e}", exc_info=True)
        return jsonify({'error': 'Failed to create kanban board'}), 500

@kanban_api_bp.route('/kanban/boards/<int:board_id>', methods=['PUT'])
def update_kanban_board(board_id):
    """Update a kanban board"""
    try:
        data = request.get_json()
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if board exists
        cursor.execute("SELECT entry_type_id FROM KanbanBoard WHERE id = ?", (board_id,))
        board = cursor.fetchone()
        if not board:
            return jsonify({'error': 'Kanban board not found'}), 404
        
        # Check if this should be the default board
        is_default = data.get('is_default', False)
        if is_default:
            # Unset ALL other default boards (only one default allowed globally)
            cursor.execute("""
                UPDATE KanbanBoard 
                SET is_default = 0 
                WHERE is_default = 1 AND id != ?
            """, (board_id,))
        
        # Update the board
        cursor.execute("""
            UPDATE KanbanBoard 
            SET name = ?, description = ?, is_default = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (data.get('name'), data.get('description', ''), 1 if is_default else 0, board_id))
        
        conn.commit()
        
        return jsonify({'message': 'Kanban board updated successfully'}), 200
        
    except sqlite3.IntegrityError as e:
        logger.error(f"Integrity error updating kanban board: {e}")
        return jsonify({'error': 'A board with this name already exists'}), 400
    except Exception as e:
        logger.error(f"Error updating kanban board: {e}", exc_info=True)
        return jsonify({'error': 'Failed to update kanban board'}), 500

@kanban_api_bp.route('/kanban/boards/<int:board_id>', methods=['DELETE'])
def delete_kanban_board(board_id):
    """Delete a kanban board"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if board exists
        cursor.execute("SELECT id FROM KanbanBoard WHERE id = ?", (board_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Kanban board not found'}), 404
        
        # Delete the board (columns will be deleted via CASCADE)
        cursor.execute("DELETE FROM KanbanBoard WHERE id = ?", (board_id,))
        conn.commit()
        
        return jsonify({'message': 'Kanban board deleted successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error deleting kanban board: {e}", exc_info=True)
        return jsonify({'error': 'Failed to delete kanban board'}), 500

# ============================================================================
# Kanban Column Management Endpoints
# ============================================================================

@kanban_api_bp.route('/kanban/boards/<int:board_id>/columns', methods=['POST'])
def add_column_to_board(board_id):
    """Add a new column to a kanban board"""
    try:
        data = request.get_json()
        
        if not data.get('state_name'):
            return jsonify({'error': 'State name is required'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if board exists
        cursor.execute("SELECT id FROM KanbanBoard WHERE id = ?", (board_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Kanban board not found'}), 404
        
        # Insert the column
        cursor.execute("""
            INSERT INTO KanbanColumn (board_id, state_name, display_order, wip_limit)
            VALUES (?, ?, ?, ?)
        """, (board_id, data['state_name'], data.get('display_order', 0), data.get('wip_limit')))
        
        column_id = cursor.lastrowid
        conn.commit()
        
        return jsonify({
            'id': column_id,
            'message': 'Column added successfully'
        }), 201
        
    except sqlite3.IntegrityError as e:
        logger.error(f"Integrity error adding column: {e}")
        return jsonify({'error': 'This state already exists in the board'}), 400
    except Exception as e:
        logger.error(f"Error adding column: {e}", exc_info=True)
        return jsonify({'error': 'Failed to add column'}), 500

@kanban_api_bp.route('/kanban/columns/<int:column_id>', methods=['PUT'])
def update_column(column_id):
    """Update a kanban column"""
    try:
        data = request.get_json()
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if column exists
        cursor.execute("SELECT id FROM KanbanColumn WHERE id = ?", (column_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Column not found'}), 404
        
        # Update the column
        cursor.execute("""
            UPDATE KanbanColumn 
            SET display_order = ?, wip_limit = ?
            WHERE id = ?
        """, (data.get('display_order', 0), data.get('wip_limit'), column_id))
        
        conn.commit()
        
        return jsonify({'message': 'Column updated successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error updating column: {e}", exc_info=True)
        return jsonify({'error': 'Failed to update column'}), 500

@kanban_api_bp.route('/kanban/columns/<int:column_id>', methods=['DELETE'])
def delete_column(column_id):
    """Delete a kanban column"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if column exists
        cursor.execute("SELECT id FROM KanbanColumn WHERE id = ?", (column_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Column not found'}), 404
        
        # Delete the column
        cursor.execute("DELETE FROM KanbanColumn WHERE id = ?", (column_id,))
        conn.commit()
        
        return jsonify({'message': 'Column deleted successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error deleting column: {e}", exc_info=True)
        return jsonify({'error': 'Failed to delete column'}), 500

@kanban_api_bp.route('/kanban/columns/reorder', methods=['POST'])
def reorder_columns():
    """Reorder columns in a kanban board"""
    try:
        data = request.get_json()
        
        if not data.get('columns'):
            return jsonify({'error': 'Columns array is required'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Update display order for each column
        for column in data['columns']:
            cursor.execute("""
                UPDATE KanbanColumn 
                SET display_order = ?
                WHERE id = ?
            """, (column['display_order'], column['id']))
        
        conn.commit()
        
        return jsonify({'message': 'Columns reordered successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error reordering columns: {e}", exc_info=True)
        return jsonify({'error': 'Failed to reorder columns'}), 500

# ============================================================================
# Kanban Data Endpoints
# ============================================================================

@kanban_api_bp.route('/kanban/boards/<int:board_id>/entries', methods=['GET'])
def get_board_entries(board_id):
    """Get all entries for a kanban board organized by column"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get board info including entry type
        cursor.execute("""
            SELECT kb.id, kb.name, kb.entry_type_id,
                   et.singular_label AS entry_type_label
            FROM KanbanBoard kb
            JOIN EntryType et ON kb.entry_type_id = et.id
            WHERE kb.id = ?
        """, (board_id,))
        
        board_row = cursor.fetchone()
        if not board_row:
            return jsonify({'error': 'Kanban board not found'}), 404
        
        entry_type_id = board_row['entry_type_id']
        
        # Get all columns for this board
        cursor.execute("""
            SELECT kc.id, kc.state_name, kc.display_order, kc.wip_limit,
                   es.color, es.category
            FROM KanbanColumn kc
            LEFT JOIN EntryState es ON es.entry_type_id = ? AND es.name = kc.state_name
            WHERE kc.board_id = ?
            ORDER BY kc.display_order, kc.id
        """, (entry_type_id, board_id))
        
        columns = []
        state_names = []
        for row in cursor.fetchall():
            column = {
                'id': row['id'],
                'state_name': row['state_name'],
                'display_order': row['display_order'],
                'wip_limit': row['wip_limit'],
                'color': row['color'],
                'category': row['category'],
                'entries': []
            }
            columns.append(column)
            state_names.append(row['state_name'])
        
        # Get all entries for this entry type with the states in the board
        if state_names:
            placeholders = ','.join('?' * len(state_names))
            cursor.execute(f"""
                SELECT e.id, e.title, e.description, e.status, e.created_at, e.commenced_at,
                       e.intended_end_date, e.actual_end_date,
                       es.color, es.category
                FROM Entry e
                LEFT JOIN EntryState es ON es.entry_type_id = e.entry_type_id AND es.name = e.status
                WHERE e.entry_type_id = ? AND e.status IN ({placeholders})
                ORDER BY e.created_at DESC
            """, (entry_type_id, *state_names))
            
            entries = cursor.fetchall()
            
            # Organize entries by column
            for entry_row in entries:
                entry = {
                    'id': entry_row['id'],
                    'title': entry_row['title'],
                    'description': entry_row['description'],
                    'status': entry_row['status'],
                    'created_at': entry_row['created_at'],
                    'commenced_at': entry_row['commenced_at'],
                    'intended_end_date': entry_row['intended_end_date'],
                    'actual_end_date': entry_row['actual_end_date'],
                    'color': entry_row['color'],
                    'category': entry_row['category']
                }
                
                # Add entry to the appropriate column
                for column in columns:
                    if column['state_name'] == entry_row['status']:
                        column['entries'].append(entry)
                        break
        
        result = {
            'board_id': board_row['id'],
            'board_name': board_row['name'],
            'entry_type_id': entry_type_id,
            'entry_type_label': board_row['entry_type_label'],
            'columns': columns
        }
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error getting board entries: {e}", exc_info=True)
        return jsonify({'error': 'Failed to get board entries'}), 500

@kanban_api_bp.route('/kanban/entry/<int:entry_id>/move', methods=['PUT'])
def move_entry(entry_id):
    """Move an entry to a different column (change its status)"""
    try:
        data = request.get_json()
        
        if not data.get('new_status'):
            return jsonify({'error': 'New status is required'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if entry exists and get current status
        cursor.execute("""
            SELECT id, entry_type_id, status, title, commenced_at, actual_end_date 
            FROM Entry 
            WHERE id = ?
        """, (entry_id,))
        entry = cursor.fetchone()
        if not entry:
            return jsonify({'error': 'Entry not found'}), 404
        
        old_status = entry['status']
        new_status = data['new_status']
        
        # If status hasn't changed, no action needed
        if old_status == new_status:
            return jsonify({'message': 'Status unchanged'}), 200
        
        # Verify that the new status exists for this entry type and get triggers
        cursor.execute("""
            SELECT id, sets_commenced, sets_ended 
            FROM EntryState 
            WHERE entry_type_id = ? AND name = ?
        """, (entry['entry_type_id'], new_status))
        
        new_state = cursor.fetchone()
        if not new_state:
            return jsonify({'error': 'Invalid status for this entry type'}), 400
        
        # Build update query
        update_parts = ["status = ?"]
        update_params = [new_status]
        
        # Check for status triggers
        now = datetime.now().isoformat()
        
        # Auto-set commenced_at if status triggers it and it's not already set
        if new_state['sets_commenced'] and not entry['commenced_at']:
            update_parts.append("commenced_at = ?")
            update_params.append(now)
            logger.info(f"Auto-setting commenced_at for entry {entry_id} due to Kanban move to '{new_status}'")
        
        # Auto-set actual_end_date if status triggers it and it's not already set
        if new_state['sets_ended'] and not entry['actual_end_date']:
            update_parts.append("actual_end_date = ?")
            update_params.append(now)
            logger.info(f"Auto-setting actual_end_date for entry {entry_id} due to Kanban move to '{new_status}'")
        
        # Update the entry
        update_query = f"UPDATE Entry SET {', '.join(update_parts)} WHERE id = ?"
        update_params.append(entry_id)
        cursor.execute(update_query, update_params)
        
        # Create a system note documenting the status change
        note_text = f"Status changed from '{old_status}' to '{new_status}' via Kanban board"
        cursor.execute("""
            INSERT INTO Note (entry_id, note_title, note_text, type, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (entry_id, "Status Change", note_text, "System", now))
        
        conn.commit()
        
        logger.info(f"Entry {entry_id} ('{entry['title']}') moved from '{old_status}' to '{new_status}' via Kanban")
        
        return jsonify({'message': 'Entry moved successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error moving entry: {e}", exc_info=True)
        conn.rollback()
        return jsonify({'error': 'Failed to move entry'}), 500

# ============================================================================
# Helper Endpoints
# ============================================================================

@kanban_api_bp.route('/kanban/entry-types/<int:entry_type_id>/states', methods=['GET'])
def get_entry_type_states(entry_type_id):
    """Get all states for a specific entry type (for column configuration)"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, category, color, display_order, is_default
            FROM EntryState
            WHERE entry_type_id = ?
            ORDER BY display_order, name
        """, (entry_type_id,))
        
        states = []
        for row in cursor.fetchall():
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
        logger.error(f"Error getting entry type states: {e}", exc_info=True)
        return jsonify({'error': 'Failed to get entry type states'}), 500
