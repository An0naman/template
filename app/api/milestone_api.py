"""
API endpoints for managing entry status milestones
"""

from flask import Blueprint, request, jsonify, g
from datetime import datetime, timezone, timedelta
import logging
import sqlite3

logger = logging.getLogger(__name__)

milestone_api_bp = Blueprint('milestone_api', __name__)


def get_db():
    """Get database connection from Flask g object"""
    if 'db' not in g:
        from ..db import get_connection
        g.db = get_connection()
        g.db.row_factory = sqlite3.Row
    return g.db


def update_entry_intended_end_date(entry_id, cursor):
    """
    Update the entry's intended_end_date based on total milestone duration.
    If milestones exist: intended_end_date = created_at + sum(all durations)
    If no milestones: leave intended_end_date unchanged
    """
    try:
        # Get entry created_at
        cursor.execute("SELECT created_at FROM Entry WHERE id = ?", (entry_id,))
        entry = cursor.fetchone()
        if not entry:
            return
        
        # Calculate total duration from all milestones
        cursor.execute("""
            SELECT COALESCE(SUM(duration_days), 0) as total_days
            FROM EntryStateMilestone
            WHERE entry_id = ?
        """, (entry_id,))
        result = cursor.fetchone()
        total_days = result['total_days']
        
        if total_days > 0:
            # Parse created_at and add total days
            created_at = datetime.fromisoformat(entry['created_at'].replace('Z', '+00:00'))
            new_end_date = created_at + timedelta(days=total_days)
            
            # Update entry
            cursor.execute("""
                UPDATE Entry
                SET intended_end_date = ?
                WHERE id = ?
            """, (new_end_date.isoformat(), entry_id))
            
            logger.info(f"Updated entry {entry_id} intended_end_date to {new_end_date} ({total_days} days)")
        
    except Exception as e:
        logger.error(f"Error updating intended_end_date for entry {entry_id}: {e}", exc_info=True)


@milestone_api_bp.route('/entries/<int:entry_id>/milestones', methods=['GET'])
def get_entry_milestones(entry_id):
    """Get all milestones for an entry"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get milestones with state information, ordered by order_position
        cursor.execute("""
            SELECT 
                m.id,
                m.entry_id,
                m.target_state_id,
                m.order_position,
                m.duration_days,
                m.notes,
                m.is_completed,
                m.created_at,
                m.updated_at,
                es.name as target_state_name,
                es.color as target_state_color,
                es.category as target_state_category
            FROM EntryStateMilestone m
            JOIN EntryState es ON m.target_state_id = es.id
            WHERE m.entry_id = ?
            ORDER BY m.order_position ASC
        """, (entry_id,))
        
        milestones = []
        for row in cursor.fetchall():
            milestones.append({
                'id': row['id'],
                'entry_id': row['entry_id'],
                'target_state_id': row['target_state_id'],
                'target_state_name': row['target_state_name'],
                'target_state_color': row['target_state_color'],
                'target_state_category': row['target_state_category'],
                'order_position': row['order_position'],
                'duration_days': row['duration_days'],
                'notes': row['notes'],
                'is_completed': bool(row['is_completed']),
                'created_at': row['created_at'],
                'updated_at': row['updated_at']
            })
        
        return jsonify(milestones), 200
        
    except Exception as e:
        logger.error(f"Error fetching milestones for entry {entry_id}: {e}", exc_info=True)
        return jsonify({'error': 'Failed to fetch milestones'}), 500


@milestone_api_bp.route('/entries/<int:entry_id>/milestones', methods=['POST'])
def create_milestone(entry_id):
    """Create a new milestone for an entry"""
    try:
        data = request.json
        
        # Validate required fields
        target_state_id = data.get('target_state_id')
        duration_days = data.get('duration_days')
        order_position = data.get('order_position')
        
        if not target_state_id or duration_days is None:
            return jsonify({'error': 'target_state_id and duration_days are required'}), 400
        
        # Validate duration_days is a positive integer
        try:
            duration_days = int(duration_days)
            if duration_days <= 0:
                return jsonify({'error': 'duration_days must be greater than 0'}), 400
        except (TypeError, ValueError):
            return jsonify({'error': 'duration_days must be a number'}), 400
        
        notes = data.get('notes', '')
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Verify entry exists
        cursor.execute("SELECT id FROM Entry WHERE id = ?", (entry_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Entry not found'}), 404
        
        # Verify target state exists and get its info
        cursor.execute("SELECT id, name, color FROM EntryState WHERE id = ?", (target_state_id,))
        state_row = cursor.fetchone()
        if not state_row:
            return jsonify({'error': 'Target state not found'}), 404
        
        # If order_position not provided, append to end
        if order_position is None:
            cursor.execute("""
                SELECT COALESCE(MAX(order_position), 0) + 1
                FROM EntryStateMilestone
                WHERE entry_id = ?
            """, (entry_id,))
            order_position = cursor.fetchone()[0]
        else:
            # Validate and adjust existing orders if needed
            order_position = int(order_position)
            if order_position < 1:
                order_position = 1
            
            # Shift existing milestones down to make room
            cursor.execute("""
                UPDATE EntryStateMilestone
                SET order_position = order_position + 1
                WHERE entry_id = ? AND order_position >= ?
            """, (entry_id, order_position))
        
        # Create milestone
        now = datetime.now(timezone.utc).isoformat()
        cursor.execute("""
            INSERT INTO EntryStateMilestone 
            (entry_id, target_state_id, target_state_name, target_state_color,
             order_position, duration_days, notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (entry_id, target_state_id, state_row['name'], state_row['color'],
              order_position, duration_days, notes, now, now))
        
        milestone_id = cursor.lastrowid
        
        # Update entry's intended_end_date based on total milestone duration
        update_entry_intended_end_date(entry_id, cursor)
        
        conn.commit()
        
        return jsonify({
            'message': 'Milestone created successfully',
            'milestone_id': milestone_id,
            'order_position': order_position
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating milestone for entry {entry_id}: {e}", exc_info=True)
        conn.rollback()
        return jsonify({'error': 'Failed to create milestone'}), 500


@milestone_api_bp.route('/entries/<int:entry_id>/milestones/<int:milestone_id>', methods=['PUT'])
def update_milestone(entry_id, milestone_id):
    """Update an existing milestone"""
    try:
        data = request.json
        conn = get_db()
        cursor = conn.cursor()
        
        # Verify milestone exists and belongs to this entry
        cursor.execute("""
            SELECT id, order_position FROM EntryStateMilestone 
            WHERE id = ? AND entry_id = ?
        """, (milestone_id, entry_id))
        
        row = cursor.fetchone()
        if not row:
            return jsonify({'error': 'Milestone not found'}), 404
        
        current_order = row['order_position']
        
        # Build update query
        set_clauses = []
        params = []
        
        if 'target_state_id' in data:
            # Verify state exists and get its info
            cursor.execute("SELECT id, name, color FROM EntryState WHERE id = ?", (data['target_state_id'],))
            state_row = cursor.fetchone()
            if not state_row:
                return jsonify({'error': 'Target state not found'}), 404
            set_clauses.extend(["target_state_id = ?", "target_state_name = ?", "target_state_color = ?"])
            params.extend([data['target_state_id'], state_row['name'], state_row['color']])
        
        if 'duration_days' in data:
            # Validate duration_days
            try:
                days = int(data['duration_days'])
                if days <= 0:
                    return jsonify({'error': 'duration_days must be greater than 0'}), 400
                set_clauses.append("duration_days = ?")
                params.append(days)
            except (TypeError, ValueError):
                return jsonify({'error': 'duration_days must be a number'}), 400
        
        if 'order_position' in data:
            # Handle reordering
            new_order = int(data['order_position'])
            if new_order < 1:
                new_order = 1
            
            if new_order != current_order:
                # Shift other milestones
                if new_order < current_order:
                    # Moving up - shift items down
                    cursor.execute("""
                        UPDATE EntryStateMilestone
                        SET order_position = order_position + 1
                        WHERE entry_id = ? AND order_position >= ? AND order_position < ? AND id != ?
                    """, (entry_id, new_order, current_order, milestone_id))
                else:
                    # Moving down - shift items up
                    cursor.execute("""
                        UPDATE EntryStateMilestone
                        SET order_position = order_position - 1
                        WHERE entry_id = ? AND order_position > ? AND order_position <= ? AND id != ?
                    """, (entry_id, current_order, new_order, milestone_id))
                
                set_clauses.append("order_position = ?")
                params.append(new_order)
        
        if 'notes' in data:
            set_clauses.append("notes = ?")
            params.append(data['notes'])
        
        if 'is_completed' in data:
            set_clauses.append("is_completed = ?")
            params.append(int(data['is_completed']))
        
        if not set_clauses:
            return jsonify({'message': 'No fields to update'}), 200
        
        # Add updated_at
        set_clauses.append("updated_at = ?")
        params.append(datetime.now(timezone.utc).isoformat())
        
        # Add WHERE clause parameters
        params.extend([milestone_id, entry_id])
        
        # Execute update
        query = f"UPDATE EntryStateMilestone SET {', '.join(set_clauses)} WHERE id = ? AND entry_id = ?"
        cursor.execute(query, params)
        
        # Update entry's intended_end_date based on total milestone duration
        update_entry_intended_end_date(entry_id, cursor)
        
        conn.commit()
        
        return jsonify({'message': 'Milestone updated successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error updating milestone {milestone_id}: {e}", exc_info=True)
        conn.rollback()
        return jsonify({'error': 'Failed to update milestone'}), 500


@milestone_api_bp.route('/entries/<int:entry_id>/milestones/<int:milestone_id>', methods=['DELETE'])
def delete_milestone(entry_id, milestone_id):
    """Delete a milestone"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Delete milestone (verify it belongs to this entry)
        cursor.execute("""
            DELETE FROM EntryStateMilestone 
            WHERE id = ? AND entry_id = ?
        """, (milestone_id, entry_id))
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'Milestone not found'}), 404
        
        # Update entry's intended_end_date based on remaining milestone duration
        update_entry_intended_end_date(entry_id, cursor)
        
        conn.commit()
        
        return jsonify({'message': 'Milestone deleted successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error deleting milestone {milestone_id}: {e}", exc_info=True)
        conn.rollback()
        return jsonify({'error': 'Failed to delete milestone'}), 500
