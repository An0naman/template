# template_app/app/api/entry_api.py
from flask import Blueprint, request, jsonify, g, url_for, current_app
import sqlite3
from datetime import datetime
import logging

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

@entry_api_bp.route('/entries', methods=['POST'])
def add_entry():
    data = request.json
    title = data.get('title')
    description = data.get('description')
    entry_type_id = data.get('entry_type_id')

    if not title or not entry_type_id:
        return jsonify({'error': 'Title and Entry Type are required.'}), 400

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO Entry (title, description, entry_type_id, created_at) VALUES (?, ?, ?, ?)",
            (title, description, entry_type_id, datetime.now().isoformat())
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
        WHERE e.title LIKE ? OR e.description LIKE ?
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