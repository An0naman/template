"""
API endpoints for managing milestone templates
Allows entries to be marked as templates and shared with related entry types
"""

from flask import Blueprint, request, jsonify, g
from datetime import datetime, timezone
import logging
import sqlite3

logger = logging.getLogger(__name__)

milestone_template_api_bp = Blueprint('milestone_template_api', __name__)


def get_db():
    """Get database connection from Flask g object"""
    if 'db' not in g:
        from app.db import get_connection
        g.db = get_connection()
    return g.db


@milestone_template_api_bp.route('/entries/<int:entry_id>/milestone-template', methods=['GET'])
def get_template_status(entry_id):
    """Get template configuration for an entry"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get entry with template fields
        cursor.execute("""
            SELECT 
                e.id,
                e.title,
                e.entry_type_id,
                e.is_milestone_template,
                e.template_name,
                e.template_description,
                e.template_distribution_status,
                et.name as entry_type_name
            FROM Entry e
            JOIN EntryType et ON e.entry_type_id = et.id
            WHERE e.id = ?
        """, (entry_id,))
        
        entry = cursor.fetchone()
        if not entry:
            return jsonify({'error': 'Entry not found'}), 404
        
        # Count milestones for this entry
        cursor.execute("""
            SELECT COUNT(*) as milestone_count
            FROM EntryStateMilestone
            WHERE entry_id = ?
        """, (entry_id,))
        
        milestone_count = cursor.fetchone()['milestone_count']
        
        # Get actual milestones with state information for preview
        cursor.execute("""
            SELECT 
                esm.id,
                esm.order_position,
                esm.duration_days,
                esm.target_state_id,
                es.name as target_state_name,
                es.color as target_state_color
            FROM EntryStateMilestone esm
            JOIN EntryState es ON esm.target_state_id = es.id
            WHERE esm.entry_id = ?
            ORDER BY esm.order_position
        """, (entry_id,))
        
        milestones = []
        total_days = 0
        for row in cursor.fetchall():
            milestones.append({
                'id': row['id'],
                'order_position': row['order_position'],
                'duration_days': row['duration_days'],
                'target_state_id': row['target_state_id'],
                'target_state_name': row['target_state_name'],
                'target_state_color': row['target_state_color']
            })
            total_days += row['duration_days']
        
        # Get template usage count (how many entries have imported this template)
        # This would require tracking imports, for now return 0
        usage_count = 0
        
        return jsonify({
            'entry_id': entry['id'],
            'entry_title': entry['title'],
            'entry_type_id': entry['entry_type_id'],
            'entry_type_name': entry['entry_type_name'],
            'is_template': bool(entry['is_milestone_template']),
            'template_name': entry['template_name'],
            'template_description': entry['template_description'],
            'distribution_status': entry['template_distribution_status'] or 'private',
            'milestone_count': milestone_count,
            'milestones': milestones,
            'total_days': total_days,
            'usage_count': usage_count
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting template status for entry {entry_id}: {e}", exc_info=True)
        return jsonify({'error': 'Failed to get template status'}), 500


@milestone_template_api_bp.route('/entries/<int:entry_id>/milestone-template', methods=['PUT'])
def update_template_config(entry_id):
    """Mark an entry as a template or update template configuration"""
    try:
        data = request.get_json()
        
        is_template = data.get('is_template', False)
        template_name = data.get('template_name', '').strip()
        template_description = data.get('template_description', '').strip()
        
        # Validation
        if is_template and not template_name:
            return jsonify({'error': 'Template name is required when marking as template'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Verify entry exists
        cursor.execute("SELECT id FROM Entry WHERE id = ?", (entry_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Entry not found'}), 404
        
        # If marking as template, check that entry has milestones
        if is_template:
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM EntryStateMilestone 
                WHERE entry_id = ?
            """, (entry_id,))
            
            milestone_count = cursor.fetchone()['count']
            if milestone_count == 0:
                return jsonify({
                    'error': 'Cannot create template from entry with no milestones',
                    'message': 'Please add at least one milestone before creating a template'
                }), 400
        
        # Update entry template fields
        now = datetime.now(timezone.utc).isoformat()
        
        cursor.execute("""
            UPDATE Entry
            SET is_milestone_template = ?,
                template_name = ?,
                template_description = ?,
                template_distribution_status = CASE 
                    WHEN ? = 0 THEN 'private'
                    ELSE template_distribution_status
                END
            WHERE id = ?
        """, (
            1 if is_template else 0,
            template_name if is_template else None,
            template_description if is_template else None,
            1 if is_template else 0,
            entry_id
        ))
        
        conn.commit()
        
        action = 'marked as template' if is_template else 'unmarked as template'
        
        return jsonify({
            'success': True,
            'message': f'Entry {action} successfully',
            'is_template': is_template,
            'template_name': template_name if is_template else None
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating template config for entry {entry_id}: {e}", exc_info=True)
        conn.rollback()
        return jsonify({'error': 'Failed to update template configuration'}), 500


@milestone_template_api_bp.route('/entries/<int:entry_id>/milestone-template/distribution', methods=['PUT'])
def update_distribution_status(entry_id):
    """Update the distribution status of a template"""
    try:
        data = request.get_json()
        distribution_status = data.get('distribution_status', 'private')
        
        # Validate distribution status
        valid_statuses = ['private', 'marked_for_distribution', 'distributed']
        if distribution_status not in valid_statuses:
            return jsonify({
                'error': f'Invalid distribution status. Must be one of: {", ".join(valid_statuses)}'
            }), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Verify entry is a template
        cursor.execute("""
            SELECT is_milestone_template, template_name
            FROM Entry
            WHERE id = ?
        """, (entry_id,))
        
        entry = cursor.fetchone()
        if not entry:
            return jsonify({'error': 'Entry not found'}), 404
        
        if not entry['is_milestone_template']:
            return jsonify({
                'error': 'Entry is not a template',
                'message': 'Mark this entry as a template before setting distribution status'
            }), 400
        
        # Update distribution status
        cursor.execute("""
            UPDATE Entry
            SET template_distribution_status = ?
            WHERE id = ?
        """, (distribution_status, entry_id))
        
        conn.commit()
        
        status_label = distribution_status.replace('_', ' ').title()
        
        return jsonify({
            'success': True,
            'message': f'Template distribution status updated to: {status_label}',
            'distribution_status': distribution_status
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating distribution status for entry {entry_id}: {e}", exc_info=True)
        conn.rollback()
        return jsonify({'error': 'Failed to update distribution status'}), 500


@milestone_template_api_bp.route('/entries/<int:entry_id>/available-templates', methods=['GET'])
def get_available_templates(entry_id):
    """Get all milestone templates available for this entry's type"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get the entry's type
        cursor.execute("""
            SELECT entry_type_id
            FROM Entry
            WHERE id = ?
        """, (entry_id,))
        
        entry = cursor.fetchone()
        if not entry:
            return jsonify({'error': 'Entry not found'}), 404
        
        entry_type_id = entry['entry_type_id']
        
        # Find all entry types that have a relationship with this entry's type
        # and can share templates
        cursor.execute("""
            SELECT DISTINCT
                CASE 
                    -- If this entry type is the 'from' side
                    WHEN etr.from_entry_type_id = ? THEN etr.to_entry_type_id
                    -- If this entry type is the 'to' side
                    WHEN etr.to_entry_type_id = ? THEN etr.from_entry_type_id
                END as related_type_id
            FROM EntryTypeRelationship etr
            WHERE etr.can_share_templates = 1
            AND (
                (etr.from_entry_type_id = ? AND etr.relationship_type IN ('template_source', 'bidirectional'))
                OR
                (etr.to_entry_type_id = ? AND etr.relationship_type IN ('template_target', 'bidirectional'))
            )
        """, (entry_type_id, entry_type_id, entry_type_id, entry_type_id))
        
        related_types = [row['related_type_id'] for row in cursor.fetchall() if row['related_type_id']]
        
        # Include the same type (entries can use templates from their own type)
        related_types.append(entry_type_id)
        
        if not related_types:
            return jsonify([]), 200
        
        # Get all template entries from related types that are marked for distribution
        placeholders = ','.join('?' * len(related_types))
        
        cursor.execute(f"""
            SELECT 
                e.id as template_entry_id,
                e.title as entry_title,
                e.template_name,
                e.template_description,
                e.entry_type_id,
                et.name as owner_entry_type,
                et.singular_label as owner_type_label,
                (
                    SELECT COUNT(*) 
                    FROM EntryStateMilestone 
                    WHERE entry_id = e.id
                ) as milestone_count,
                (
                    SELECT SUM(duration_days)
                    FROM EntryStateMilestone
                    WHERE entry_id = e.id
                ) as total_days
            FROM Entry e
            JOIN EntryType et ON e.entry_type_id = et.id
            WHERE e.is_milestone_template = 1
            AND e.template_distribution_status = 'marked_for_distribution'
            AND e.entry_type_id IN ({placeholders})
            AND e.id != ?  -- Don't show this entry itself
            ORDER BY e.template_name
        """, (*related_types, entry_id))
        
        templates = []
        for row in cursor.fetchall():
            # Get milestone details for this template
            cursor.execute("""
                SELECT 
                    id,
                    target_state_name,
                    target_state_color,
                    order_position,
                    duration_days,
                    notes
                FROM EntryStateMilestone
                WHERE entry_id = ?
                ORDER BY order_position ASC
            """, (row['template_entry_id'],))
            
            milestones = []
            for m in cursor.fetchall():
                milestones.append({
                    'id': m['id'],
                    'target_state_name': m['target_state_name'],
                    'target_state_color': m['target_state_color'],
                    'order_position': m['order_position'],
                    'duration_days': m['duration_days'],
                    'notes': m['notes']
                })
            
            templates.append({
                'template_entry_id': row['template_entry_id'],
                'entry_title': row['entry_title'],
                'template_name': row['template_name'],
                'template_description': row['template_description'],
                'owner_entry_type': row['owner_entry_type'],
                'owner_type_label': row['owner_type_label'],
                'milestone_count': row['milestone_count'] or 0,
                'total_days': row['total_days'] or 0,
                'milestones': milestones
            })
        
        return jsonify(templates), 200
        
    except Exception as e:
        logger.error(f"Error getting available templates for entry {entry_id}: {e}", exc_info=True)
        return jsonify({'error': 'Failed to get available templates'}), 500


@milestone_template_api_bp.route('/entries/<int:entry_id>/import-template', methods=['POST'])
def import_template(entry_id):
    """Import milestones from a template into this entry"""
    try:
        data = request.get_json()
        
        template_entry_id = data.get('template_entry_id')
        import_mode = data.get('import_mode', 'replace')  # 'replace' or 'append'
        
        if not template_entry_id:
            return jsonify({'error': 'template_entry_id is required'}), 400
        
        if import_mode not in ['replace', 'append']:
            return jsonify({'error': 'import_mode must be "replace" or "append"'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Verify target entry exists
        cursor.execute("SELECT id, entry_type_id FROM Entry WHERE id = ?", (entry_id,))
        target_entry = cursor.fetchone()
        if not target_entry:
            return jsonify({'error': 'Target entry not found'}), 404
        
        # Verify template entry exists and is a template
        cursor.execute("""
            SELECT 
                id, 
                entry_type_id,
                is_milestone_template,
                template_distribution_status,
                template_name
            FROM Entry 
            WHERE id = ?
        """, (template_entry_id,))
        
        template_entry = cursor.fetchone()
        if not template_entry:
            return jsonify({'error': 'Template entry not found'}), 404
        
        if not template_entry['is_milestone_template']:
            return jsonify({'error': 'Source entry is not a template'}), 400
        
        if template_entry['template_distribution_status'] != 'marked_for_distribution':
            return jsonify({'error': 'Template is not marked for distribution'}), 403
        
        # Verify entry types are related (or same type)
        if target_entry['entry_type_id'] != template_entry['entry_type_id']:
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM EntryTypeRelationship
                WHERE can_share_templates = 1
                AND (
                    (from_entry_type_id = ? AND to_entry_type_id = ?)
                    OR
                    (from_entry_type_id = ? AND to_entry_type_id = ?)
                )
            """, (
                target_entry['entry_type_id'], 
                template_entry['entry_type_id'],
                template_entry['entry_type_id'],
                target_entry['entry_type_id']
            ))
            
            if cursor.fetchone()['count'] == 0:
                return jsonify({
                    'error': 'Entry types are not related',
                    'message': 'Cannot import template from unrelated entry type'
                }), 403
        
        # Get template milestones
        cursor.execute("""
            SELECT 
                target_state_id,
                target_state_name,
                target_state_color,
                order_position,
                duration_days,
                notes
            FROM EntryStateMilestone
            WHERE entry_id = ?
            ORDER BY order_position ASC
        """, (template_entry_id,))
        
        template_milestones = cursor.fetchall()
        
        if not template_milestones:
            return jsonify({
                'error': 'Template has no milestones',
                'message': 'The template entry does not have any milestones to import'
            }), 400
        
        # Handle import mode
        if import_mode == 'replace':
            # Delete existing milestones
            cursor.execute("""
                DELETE FROM EntryStateMilestone
                WHERE entry_id = ?
            """, (entry_id,))
            
            start_order = 1
        else:  # append
            # Get the highest order position
            cursor.execute("""
                SELECT COALESCE(MAX(order_position), 0) as max_order
                FROM EntryStateMilestone
                WHERE entry_id = ?
            """, (entry_id,))
            
            max_order = cursor.fetchone()['max_order']
            start_order = max_order + 1
        
        # Import milestones
        now = datetime.now(timezone.utc).isoformat()
        imported_milestones = []
        
        for idx, milestone in enumerate(template_milestones):
            new_order = start_order + idx
            
            cursor.execute("""
                INSERT INTO EntryStateMilestone 
                (entry_id, target_state_id, target_state_name, target_state_color,
                 order_position, duration_days, notes, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entry_id,
                milestone['target_state_id'],
                milestone['target_state_name'],
                milestone['target_state_color'],
                new_order,
                milestone['duration_days'],
                f"Imported from template: {template_entry['template_name']}" + 
                (f"\n{milestone['notes']}" if milestone['notes'] else ""),
                now,
                now
            ))
            
            imported_milestones.append({
                'order_position': new_order,
                'target_state_name': milestone['target_state_name'],
                'duration_days': milestone['duration_days']
            })
        
        
        # Update entry's intended_end_date based on new milestones
        from app.api.milestone_api import update_entry_intended_end_date
        update_entry_intended_end_date(entry_id, cursor)
        
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': f'Successfully imported {len(imported_milestones)} milestone(s) from template',
            'template_name': template_entry['template_name'],
            'import_mode': import_mode,
            'imported_count': len(imported_milestones),
            'milestones': imported_milestones
        }), 200
        
    except Exception as e:
        logger.error(f"Error importing template for entry {entry_id}: {e}", exc_info=True)
        conn.rollback()
        return jsonify({'error': 'Failed to import template'}), 500


@milestone_template_api_bp.route('/entries/<int:entry_id>/template-relationship-sharing', methods=['GET'])
def get_template_relationship_sharing(entry_id):
    """Get which parent entries this template can be shared through"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                trs.id,
                trs.relationship_definition_id,
                trs.source_entry_id,
                rd.label_from_side,
                rd.label_to_side,
                e.title as source_entry_title,
                trs.created_at
            FROM TemplateRelationshipSharing trs
            JOIN RelationshipDefinition rd ON trs.relationship_definition_id = rd.id
            LEFT JOIN Entry e ON trs.source_entry_id = e.id
            WHERE trs.template_entry_id = ?
        """, (entry_id,))
        
        relationships = []
        for row in cursor.fetchall():
            relationships.append({
                'id': row['id'],
                'relationship_definition_id': row['relationship_definition_id'],
                'source_entry_id': row['source_entry_id'],
                'source_entry_title': row['source_entry_title'],
                'label_from_side': row['label_from_side'],
                'label_to_side': row['label_to_side'],
                'created_at': row['created_at']
            })
        
        return jsonify(relationships), 200
        
    except Exception as e:
        logger.error(f"Error getting template relationship sharing for entry {entry_id}: {e}", exc_info=True)
        return jsonify({'error': 'Failed to get template sharing configuration'}), 500


@milestone_template_api_bp.route('/templates/shared-via/<int:parent_entry_id>/<int:rel_def_id>', methods=['GET'])
def get_templates_shared_via_parent(parent_entry_id, rel_def_id):
    """Find templates that are shared via a specific parent entry and relationship type"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Find all templates that are shared via this parent entry and relationship type
        cursor.execute("""
            SELECT 
                e.id as template_entry_id,
                e.title as entry_title,
                e.template_name,
                e.template_description,
                (
                    SELECT COUNT(*) 
                    FROM EntryStateMilestone 
                    WHERE entry_id = e.id
                ) as milestone_count
            FROM TemplateRelationshipSharing trs
            JOIN Entry e ON trs.template_entry_id = e.id
            WHERE trs.source_entry_id = ?
            AND trs.relationship_definition_id = ?
            AND e.is_milestone_template = 1
        """, (parent_entry_id, rel_def_id))
        
        templates = []
        for row in cursor.fetchall():
            templates.append({
                'template_entry_id': row['template_entry_id'],
                'entry_title': row['entry_title'],
                'template_name': row['template_name'],
                'template_description': row['template_description'],
                'milestone_count': row['milestone_count']
            })
        
        return jsonify(templates), 200
        
    except Exception as e:
        logger.error(f"Error finding templates shared via parent {parent_entry_id}: {e}", exc_info=True)
        return jsonify({'error': 'Failed to find shared templates'}), 500



@milestone_template_api_bp.route('/entries/<int:entry_id>/template-relationship-sharing', methods=['PUT'])
def update_template_relationship_sharing(entry_id):
    """Configure which parent entries this template can be shared through"""
    try:
        data = request.get_json()
        sharing = data.get('sharing', [])  # Array of {relationship_definition_id, source_entry_id}
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Verify entry is a template
        cursor.execute("""
            SELECT is_milestone_template 
            FROM Entry 
            WHERE id = ?
        """, (entry_id,))
        
        entry = cursor.fetchone()
        if not entry:
            return jsonify({'error': 'Entry not found'}), 404
        
        if not entry['is_milestone_template']:
            return jsonify({'error': 'Entry is not configured as a template'}), 400
        
        # Delete existing sharing configuration
        cursor.execute("""
            DELETE FROM TemplateRelationshipSharing 
            WHERE template_entry_id = ?
        """, (entry_id,))
        
        # Insert new sharing configuration with source_entry_id
        now = datetime.now(timezone.utc).isoformat()
        for item in sharing:
            rel_def_id = item.get('relationship_definition_id')
            source_entry_id = item.get('source_entry_id')
            
            if rel_def_id and source_entry_id:
                cursor.execute("""
                    INSERT INTO TemplateRelationshipSharing 
                    (template_entry_id, relationship_definition_id, source_entry_id, created_at)
                    VALUES (?, ?, ?, ?)
                """, (entry_id, rel_def_id, source_entry_id, now))
        
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'Template sharing configuration updated',
            'shared_via_count': len(sharing)
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating template relationship sharing for entry {entry_id}: {e}", exc_info=True)
        conn.rollback()
        return jsonify({'error': 'Failed to update template sharing configuration'}), 500

