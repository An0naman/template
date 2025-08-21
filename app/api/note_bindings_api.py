# template_app/app/api/note_bindings_api.py
from flask import Blueprint, request, jsonify, g
import sqlite3
from datetime import datetime
import logging
from ..db import get_connection

# Get the logger for this module
logger = logging.getLogger(__name__)

note_bindings_bp = Blueprint('note_bindings', __name__)

@note_bindings_bp.route('/note_bindings', methods=['GET'])
def get_note_bindings():
    """Get all note bindings for the current entry (as source)"""
    try:
        entry_id = request.args.get('entry_id', type=int)
        if not entry_id:
            return jsonify({'error': 'entry_id is required'}), 400

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT nb.*, e.title as target_entry_title
                FROM NoteBinding nb
                JOIN Entry e ON nb.target_entry_id = e.id
                WHERE nb.source_entry_id = ? AND nb.enabled = 1
                ORDER BY e.title
            ''', (entry_id,))
            
            bindings = []
            for row in cursor.fetchall():
                bindings.append({
                    'id': row['id'],
                    'source_entry_id': row['source_entry_id'],
                    'target_entry_id': row['target_entry_id'],
                    'target_entry_title': row['target_entry_title'],
                    'enabled': bool(row['enabled']),
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                })
            
            return jsonify(bindings)
    
    except Exception as e:
        logger.error(f"Error getting note bindings: {e}")
        return jsonify({'error': str(e)}), 500

@note_bindings_bp.route('/note_bindings', methods=['POST'])
def create_or_update_note_binding():
    """Create or update a note binding"""
    try:
        data = request.get_json()
        source_entry_id = data.get('source_entry_id')
        target_entry_id = data.get('target_entry_id')
        enabled = data.get('enabled', True)
        
        if not source_entry_id or not target_entry_id:
            return jsonify({'error': 'source_entry_id and target_entry_id are required'}), 400
        
        if source_entry_id == target_entry_id:
            return jsonify({'error': 'Cannot bind an entry to itself'}), 400

        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if binding already exists
            cursor.execute('''
                SELECT id FROM NoteBinding 
                WHERE source_entry_id = ? AND target_entry_id = ?
            ''', (source_entry_id, target_entry_id))
            
            existing = cursor.fetchone()
            
            if existing:
                # Update existing binding
                cursor.execute('''
                    UPDATE NoteBinding 
                    SET enabled = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (enabled, existing['id']))
                binding_id = existing['id']
                logger.info(f"Updated note binding {binding_id}: source={source_entry_id}, target={target_entry_id}, enabled={enabled}")
            else:
                # Create new binding
                cursor.execute('''
                    INSERT INTO NoteBinding (source_entry_id, target_entry_id, enabled)
                    VALUES (?, ?, ?)
                ''', (source_entry_id, target_entry_id, enabled))
                binding_id = cursor.lastrowid
                logger.info(f"Created note binding {binding_id}: source={source_entry_id}, target={target_entry_id}, enabled={enabled}")
            
            conn.commit()
            
            # Return the created/updated binding
            cursor.execute('''
                SELECT nb.*, e.title as target_entry_title
                FROM NoteBinding nb
                JOIN Entry e ON nb.target_entry_id = e.id
                WHERE nb.id = ?
            ''', (binding_id,))
            
            row = cursor.fetchone()
            binding = {
                'id': row['id'],
                'source_entry_id': row['source_entry_id'],
                'target_entry_id': row['target_entry_id'],
                'target_entry_title': row['target_entry_title'],
                'enabled': bool(row['enabled']),
                'created_at': row['created_at'],
                'updated_at': row['updated_at']
            }
            
            return jsonify(binding), 201 if not existing else 200
    
    except Exception as e:
        logger.error(f"Error creating/updating note binding: {e}")
        return jsonify({'error': str(e)}), 500

@note_bindings_bp.route('/note_bindings/<int:binding_id>', methods=['DELETE'])
def delete_note_binding(binding_id):
    """Delete a note binding"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if binding exists
            cursor.execute('SELECT * FROM NoteBinding WHERE id = ?', (binding_id,))
            binding = cursor.fetchone()
            
            if not binding:
                return jsonify({'error': 'Note binding not found'}), 404
            
            # Delete the binding
            cursor.execute('DELETE FROM NoteBinding WHERE id = ?', (binding_id,))
            conn.commit()
            
            logger.info(f"Deleted note binding {binding_id}: source={binding['source_entry_id']}, target={binding['target_entry_id']}")
            
            return jsonify({'message': 'Note binding deleted successfully'})
    
    except Exception as e:
        logger.error(f"Error deleting note binding: {e}")
        return jsonify({'error': str(e)}), 500

@note_bindings_bp.route('/note_bindings/cleanup', methods=['POST'])
def cleanup_note_bindings():
    """Clean up note bindings when relationships are deleted"""
    try:
        data = request.get_json()
        source_entry_id = data.get('source_entry_id')
        target_entry_id = data.get('target_entry_id')
        
        if not source_entry_id or not target_entry_id:
            return jsonify({'error': 'source_entry_id and target_entry_id are required'}), 400

        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if there are any relationships left between these entries
            cursor.execute('''
                SELECT COUNT(*) as count FROM EntryRelationship 
                WHERE (source_entry_id = ? AND target_entry_id = ?) 
                   OR (source_entry_id = ? AND target_entry_id = ?)
            ''', (source_entry_id, target_entry_id, target_entry_id, source_entry_id))
            
            relationship_count = cursor.fetchone()['count']
            
            if relationship_count == 0:
                # No relationships left, remove note bindings in both directions
                cursor.execute('''
                    DELETE FROM NoteBinding 
                    WHERE (source_entry_id = ? AND target_entry_id = ?)
                       OR (source_entry_id = ? AND target_entry_id = ?)
                ''', (source_entry_id, target_entry_id, target_entry_id, source_entry_id))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                logger.info(f"Cleaned up {deleted_count} note binding(s) between entries {source_entry_id} and {target_entry_id}")
                
                return jsonify({
                    'message': f'Cleaned up {deleted_count} note binding(s)',
                    'deleted_count': deleted_count
                })
            else:
                return jsonify({
                    'message': 'Note bindings preserved - relationships still exist',
                    'deleted_count': 0
                })
    
    except Exception as e:
        logger.error(f"Error cleaning up note bindings: {e}")
        return jsonify({'error': str(e)}), 500
