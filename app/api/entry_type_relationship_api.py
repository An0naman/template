"""
API endpoints for managing entry type relationships
Defines which entry types can share milestone templates with each other
"""

from flask import Blueprint, request, jsonify, g
from datetime import datetime, timezone
import logging
import sqlite3

logger = logging.getLogger(__name__)

entry_type_relationship_api_bp = Blueprint('entry_type_relationship_api', __name__)


def get_db():
    """Get database connection from Flask g object"""
    if 'db' not in g:
        from app.db import get_connection
        g.db = get_connection()
    return g.db


@entry_type_relationship_api_bp.route('/entry-types/<int:type_id>/relationships', methods=['GET'])
def get_type_relationships(type_id):
    """Get all entry types related to this one"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Verify entry type exists
        cursor.execute("""
            SELECT id, name, singular_label, plural_label
            FROM EntryType
            WHERE id = ?
        """, (type_id,))
        
        entry_type = cursor.fetchone()
        if not entry_type:
            return jsonify({'error': 'Entry type not found'}), 404
        
        # Get all relationships where this type is involved
        cursor.execute("""
            SELECT 
                etr.id as relationship_id,
                etr.from_entry_type_id,
                etr.to_entry_type_id,
                etr.relationship_type,
                etr.can_share_templates,
                etr.created_at,
                et_from.name as from_type_name,
                et_from.singular_label as from_type_label,
                et_to.name as to_type_name,
                et_to.singular_label as to_type_label
            FROM EntryTypeRelationship etr
            JOIN EntryType et_from ON etr.from_entry_type_id = et_from.id
            JOIN EntryType et_to ON etr.to_entry_type_id = et_to.id
            WHERE etr.from_entry_type_id = ? OR etr.to_entry_type_id = ?
            ORDER BY et_from.name, et_to.name
        """, (type_id, type_id))
        
        relationships = []
        for row in cursor.fetchall():
            # Determine the "other" type in the relationship
            if row['from_entry_type_id'] == type_id:
                other_type_id = row['to_entry_type_id']
                other_type_name = row['to_type_name']
                other_type_label = row['to_type_label']
                direction = 'outgoing'
            else:
                other_type_id = row['from_entry_type_id']
                other_type_name = row['from_type_name']
                other_type_label = row['from_type_label']
                direction = 'incoming'
            
            relationships.append({
                'id': row['relationship_id'],
                'other_type_id': other_type_id,
                'other_type_name': other_type_name,
                'other_type_label': other_type_label,
                'from_type_id': row['from_entry_type_id'],
                'from_type_name': row['from_type_name'],
                'to_type_id': row['to_entry_type_id'],
                'to_type_name': row['to_type_name'],
                'relationship_type': row['relationship_type'],
                'can_share_templates': bool(row['can_share_templates']),
                'direction': direction,
                'created_at': row['created_at']
            })
        
        return jsonify({
            'entry_type': {
                'id': entry_type['id'],
                'name': entry_type['name'],
                'singular_label': entry_type['singular_label'],
                'plural_label': entry_type['plural_label']
            },
            'relationships': relationships
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting relationships for type {type_id}: {e}", exc_info=True)
        return jsonify({'error': 'Failed to get entry type relationships'}), 500


@entry_type_relationship_api_bp.route('/entry-types/relationships', methods=['GET'])
def get_all_relationships():
    """Get all entry type relationships"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                etr.id,
                etr.from_entry_type_id,
                etr.to_entry_type_id,
                etr.relationship_type,
                etr.can_share_templates,
                etr.created_at,
                et_from.name as from_type_name,
                et_from.singular_label as from_type_label,
                et_to.name as to_type_name,
                et_to.singular_label as to_type_label
            FROM EntryTypeRelationship etr
            JOIN EntryType et_from ON etr.from_entry_type_id = et_from.id
            JOIN EntryType et_to ON etr.to_entry_type_id = et_to.id
            ORDER BY et_from.name, et_to.name
        """)
        
        relationships = []
        for row in cursor.fetchall():
            relationships.append({
                'id': row['id'],
                'from_type_id': row['from_entry_type_id'],
                'from_type_name': row['from_type_name'],
                'from_type_label': row['from_type_label'],
                'to_type_id': row['to_entry_type_id'],
                'to_type_name': row['to_type_name'],
                'to_type_label': row['to_type_label'],
                'relationship_type': row['relationship_type'],
                'can_share_templates': bool(row['can_share_templates']),
                'created_at': row['created_at']
            })
        
        return jsonify(relationships), 200
        
    except Exception as e:
        logger.error(f"Error getting all relationships: {e}", exc_info=True)
        return jsonify({'error': 'Failed to get relationships'}), 500


@entry_type_relationship_api_bp.route('/entry-types/relationships', methods=['POST'])
def create_relationship():
    """Create a relationship between two entry types"""
    try:
        data = request.get_json()
        
        from_type_id = data.get('from_type_id')
        to_type_id = data.get('to_type_id')
        relationship_type = data.get('relationship_type', 'bidirectional')
        can_share_templates = data.get('can_share_templates', True)
        
        # Validation
        if not from_type_id or not to_type_id:
            return jsonify({'error': 'Both from_type_id and to_type_id are required'}), 400
        
        if from_type_id == to_type_id:
            return jsonify({'error': 'Cannot create relationship with same entry type'}), 400
        
        valid_types = ['template_source', 'template_target', 'bidirectional']
        if relationship_type not in valid_types:
            return jsonify({
                'error': f'Invalid relationship_type. Must be one of: {", ".join(valid_types)}'
            }), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Verify both entry types exist
        cursor.execute("""
            SELECT id, name FROM EntryType WHERE id IN (?, ?)
        """, (from_type_id, to_type_id))
        
        types = cursor.fetchall()
        if len(types) != 2:
            return jsonify({'error': 'One or both entry types not found'}), 404
        
        # Check if relationship already exists (in either direction)
        cursor.execute("""
            SELECT id FROM EntryTypeRelationship
            WHERE (from_entry_type_id = ? AND to_entry_type_id = ?)
            OR (from_entry_type_id = ? AND to_entry_type_id = ?)
        """, (from_type_id, to_type_id, to_type_id, from_type_id))
        
        if cursor.fetchone():
            return jsonify({
                'error': 'Relationship already exists between these entry types',
                'message': 'Please edit the existing relationship instead'
            }), 409
        
        # Create relationship
        now = datetime.now(timezone.utc).isoformat()
        
        cursor.execute("""
            INSERT INTO EntryTypeRelationship
            (from_entry_type_id, to_entry_type_id, relationship_type, 
             can_share_templates, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (from_type_id, to_type_id, relationship_type, 
              1 if can_share_templates else 0, now, now))
        
        relationship_id = cursor.lastrowid
        conn.commit()
        
        # Get the created relationship with names
        cursor.execute("""
            SELECT 
                etr.id,
                etr.from_entry_type_id,
                etr.to_entry_type_id,
                etr.relationship_type,
                etr.can_share_templates,
                et_from.name as from_type_name,
                et_to.name as to_type_name
            FROM EntryTypeRelationship etr
            JOIN EntryType et_from ON etr.from_entry_type_id = et_from.id
            JOIN EntryType et_to ON etr.to_entry_type_id = et_to.id
            WHERE etr.id = ?
        """, (relationship_id,))
        
        rel = cursor.fetchone()
        
        return jsonify({
            'success': True,
            'message': 'Relationship created successfully',
            'relationship': {
                'id': rel['id'],
                'from_type_id': rel['from_entry_type_id'],
                'from_type_name': rel['from_type_name'],
                'to_type_id': rel['to_entry_type_id'],
                'to_type_name': rel['to_type_name'],
                'relationship_type': rel['relationship_type'],
                'can_share_templates': bool(rel['can_share_templates'])
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating relationship: {e}", exc_info=True)
        conn.rollback()
        return jsonify({'error': 'Failed to create relationship'}), 500


@entry_type_relationship_api_bp.route('/entry-types/relationships/<int:relationship_id>', methods=['PUT'])
def update_relationship(relationship_id):
    """Update an existing relationship"""
    try:
        data = request.get_json()
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Verify relationship exists
        cursor.execute("""
            SELECT id, relationship_type, can_share_templates
            FROM EntryTypeRelationship
            WHERE id = ?
        """, (relationship_id,))
        
        relationship = cursor.fetchone()
        if not relationship:
            return jsonify({'error': 'Relationship not found'}), 404
        
        # Update fields
        relationship_type = data.get('relationship_type', relationship['relationship_type'])
        can_share_templates = data.get('can_share_templates', bool(relationship['can_share_templates']))
        
        # Validate relationship_type
        valid_types = ['template_source', 'template_target', 'bidirectional']
        if relationship_type not in valid_types:
            return jsonify({
                'error': f'Invalid relationship_type. Must be one of: {", ".join(valid_types)}'
            }), 400
        
        # Update
        now = datetime.now(timezone.utc).isoformat()
        
        cursor.execute("""
            UPDATE EntryTypeRelationship
            SET relationship_type = ?,
                can_share_templates = ?,
                updated_at = ?
            WHERE id = ?
        """, (relationship_type, 1 if can_share_templates else 0, now, relationship_id))
        
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'Relationship updated successfully',
            'relationship_id': relationship_id
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating relationship {relationship_id}: {e}", exc_info=True)
        conn.rollback()
        return jsonify({'error': 'Failed to update relationship'}), 500


@entry_type_relationship_api_bp.route('/entry-types/relationships/<int:relationship_id>', methods=['DELETE'])
def delete_relationship(relationship_id):
    """Delete a relationship"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Verify relationship exists
        cursor.execute("""
            SELECT id FROM EntryTypeRelationship WHERE id = ?
        """, (relationship_id,))
        
        if not cursor.fetchone():
            return jsonify({'error': 'Relationship not found'}), 404
        
        # Delete relationship
        cursor.execute("""
            DELETE FROM EntryTypeRelationship WHERE id = ?
        """, (relationship_id,))
        
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'Relationship deleted successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error deleting relationship {relationship_id}: {e}", exc_info=True)
        conn.rollback()
        return jsonify({'error': 'Failed to delete relationship'}), 500


@entry_type_relationship_api_bp.route('/entry-types', methods=['GET'])
def get_all_entry_types():
    """Get all entry types (helper endpoint for UI)"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                id,
                name,
                singular_label,
                plural_label,
                description,
                is_primary
            FROM EntryType
            ORDER BY is_primary DESC, name ASC
        """)
        
        entry_types = []
        for row in cursor.fetchall():
            entry_types.append({
                'id': row['id'],
                'name': row['name'],
                'singular_label': row['singular_label'],
                'plural_label': row['plural_label'],
                'description': row['description'],
                'is_primary': bool(row['is_primary'])
            })
        
        return jsonify(entry_types), 200
        
    except Exception as e:
        logger.error(f"Error getting entry types: {e}", exc_info=True)
        return jsonify({'error': 'Failed to get entry types'}), 500
