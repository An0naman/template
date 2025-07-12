# template_app/app/api/notes_api.py
from flask import Blueprint, request, jsonify, g, current_app
import sqlite3
from datetime import datetime
import json
import logging
from ..serializers import serialize_note # Import the serializer

# Define a Blueprint for Notes API
notes_api_bp = Blueprint('notes_api', __name__)

# Get a logger for this module
logger = logging.getLogger(__name__)

def get_db():
    if 'db' not in g:
        db_path = current_app.config['DATABASE_PATH']
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
    return g.db

@notes_api_bp.route('/entries/<int:entry_id>/notes', methods=['POST'])
def add_note_to_entry(entry_id):
    data = request.json
    note_title = data.get('note_title')
    note_text = data.get('note_text')
    note_type = data.get('note_type', 'General')

    if not note_text:
        return jsonify({'message': 'Note content cannot be empty!'}), 400

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO Note (entry_id, note_title, note_text, type, created_at, image_paths) VALUES (?, ?, ?, ?, ?, ?)",
            (entry_id, note_title, note_text, note_type, datetime.now().isoformat(), json.dumps([]))
        )
        conn.commit()
        return jsonify({'message': 'Note added successfully!', 'note_id': cursor.lastrowid}), 201
    except sqlite3.IntegrityError:
        conn.rollback()
        return jsonify({'message': 'Entry not found for adding note.'}), 404
    except Exception as e:
        logger.error(f"Error adding note to entry {entry_id}: {e}", exc_info=True)
        conn.rollback()
        return jsonify({'message': 'An internal error occurred.'}), 500

@notes_api_bp.route('/entries/<int:entry_id>/notes', methods=['GET'])
def get_notes_for_entry(entry_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, entry_id, note_title, note_text, type, created_at, image_paths FROM Note WHERE entry_id = ? ORDER BY created_at DESC", (entry_id,))
    notes = cursor.fetchall()
    return jsonify([serialize_note(note) for note in notes])

@notes_api_bp.route('/notes/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM Note WHERE id = ?", (note_id,))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({'error': 'Note not found.'}), 404
        return jsonify({'message': 'Note deleted successfully!'}), 200
    except Exception as e:
        logger.error(f"Error deleting note {note_id}: {e}", exc_info=True)
        conn.rollback()
        return jsonify({'error': 'An internal error occurred.'}), 500