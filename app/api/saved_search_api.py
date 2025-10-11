# template_app/app/api/saved_search_api.py
from flask import Blueprint, request, jsonify, g, current_app
import sqlite3
import logging
from datetime import datetime

# Define a Blueprint for Saved Search API
saved_search_api_bp = Blueprint('saved_search_api', __name__)

# Get a logger for this module
logger = logging.getLogger(__name__)

def get_db():
    if 'db' not in g:
        db_path = current_app.config['DATABASE_PATH']
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
    return g.db

@saved_search_api_bp.route('/saved_searches', methods=['GET'])
def get_saved_searches():
    """Get all saved searches"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, search_term, type_filter, status_filter, specific_states,
                   date_range, sort_by, content_display, result_limit, is_default,
                   created_at, updated_at
            FROM SavedSearch
            ORDER BY is_default DESC, name ASC
        """)
        
        searches = []
        for row in cursor.fetchall():
            searches.append({
                'id': row['id'],
                'name': row['name'],
                'search_term': row['search_term'],
                'type_filter': row['type_filter'],
                'status_filter': row['status_filter'],
                'specific_states': row['specific_states'],
                'date_range': row['date_range'],
                'sort_by': row['sort_by'],
                'content_display': row['content_display'],
                'result_limit': row['result_limit'],
                'is_default': bool(row['is_default']),
                'created_at': row['created_at'],
                'updated_at': row['updated_at']
            })
        
        return jsonify(searches), 200
        
    except Exception as e:
        logger.error(f"Error getting saved searches: {e}", exc_info=True)
        return jsonify({'error': 'Failed to get saved searches'}), 500

@saved_search_api_bp.route('/saved_searches', methods=['POST'])
def create_saved_search():
    """Create a new saved search"""
    try:
        data = request.json
        if not data or 'name' not in data:
            return jsonify({'error': 'Search name is required'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if name already exists
        cursor.execute("SELECT id FROM SavedSearch WHERE name = ?", (data['name'],))
        if cursor.fetchone():
            return jsonify({'error': 'A saved search with this name already exists'}), 400
        
        cursor.execute("""
            INSERT INTO SavedSearch (
                name, search_term, type_filter, status_filter, specific_states,
                date_range, sort_by, content_display, result_limit
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data['name'],
            data.get('search_term', ''),
            data.get('type_filter', ''),
            data.get('status_filter', ''),
            data.get('specific_states', ''),
            data.get('date_range', ''),
            data.get('sort_by', 'created_desc'),
            data.get('content_display', ''),
            data.get('result_limit', '50')
        ))
        
        conn.commit()
        search_id = cursor.lastrowid
        
        return jsonify({'id': search_id, 'message': 'Saved search created successfully'}), 201
        
    except Exception as e:
        logger.error(f"Error creating saved search: {e}", exc_info=True)
        return jsonify({'error': 'Failed to create saved search'}), 500

@saved_search_api_bp.route('/saved_searches/<int:search_id>', methods=['PUT'])
def update_saved_search(search_id):
    """Update an existing saved search"""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if search exists
        cursor.execute("SELECT id FROM SavedSearch WHERE id = ?", (search_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Saved search not found'}), 404
        
        # If name is being updated, check for duplicates
        if 'name' in data:
            cursor.execute("SELECT id FROM SavedSearch WHERE name = ? AND id != ?", (data['name'], search_id))
            if cursor.fetchone():
                return jsonify({'error': 'A saved search with this name already exists'}), 400
        
        cursor.execute("""
            UPDATE SavedSearch SET
                name = ?,
                search_term = ?,
                type_filter = ?,
                status_filter = ?,
                specific_states = ?,
                date_range = ?,
                sort_by = ?,
                content_display = ?,
                result_limit = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            data.get('name', ''),
            data.get('search_term', ''),
            data.get('type_filter', ''),
            data.get('status_filter', ''),
            data.get('specific_states', ''),
            data.get('date_range', ''),
            data.get('sort_by', 'created_desc'),
            data.get('content_display', ''),
            data.get('result_limit', '50'),
            search_id
        ))
        
        conn.commit()
        
        return jsonify({'message': 'Saved search updated successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error updating saved search: {e}", exc_info=True)
        return jsonify({'error': 'Failed to update saved search'}), 500

@saved_search_api_bp.route('/saved_searches/<int:search_id>/set_default', methods=['POST'])
def set_default_search(search_id):
    """Set a saved search as the default"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if search exists
        cursor.execute("SELECT id FROM SavedSearch WHERE id = ?", (search_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Saved search not found'}), 404
        
        # Clear all defaults first
        cursor.execute("UPDATE SavedSearch SET is_default = 0")
        
        # Set this search as default
        cursor.execute("UPDATE SavedSearch SET is_default = 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (search_id,))
        
        conn.commit()
        
        return jsonify({'message': 'Default search updated successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error setting default search: {e}", exc_info=True)
        return jsonify({'error': 'Failed to set default search'}), 500

@saved_search_api_bp.route('/saved_searches/<int:search_id>', methods=['DELETE'])
def delete_saved_search(search_id):
    """Delete a saved search"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM SavedSearch WHERE id = ?", (search_id,))
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'Saved search not found'}), 404
        
        conn.commit()
        
        return jsonify({'message': 'Saved search deleted successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error deleting saved search: {e}", exc_info=True)
        return jsonify({'error': 'Failed to delete saved search'}), 500
