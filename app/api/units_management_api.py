"""
Units management API
"""

from flask import Blueprint, request, jsonify
import sqlite3
import logging

def get_db_connection_direct():
    """Get database connection without Flask context dependency"""
    try:
        # Try to use Flask context first
        from app.db import get_connection
        return get_connection()
    except RuntimeError:
        # Fall back to direct connection if outside Flask context
        from app.config import DATABASE_PATH
        return sqlite3.connect(DATABASE_PATH)

units_management_bp = Blueprint('units_management', __name__)

@units_management_bp.route('/api/units-management', methods=['GET'])
def get_all_units():
    """Get all units with filtering options"""
    try:
        category = request.args.get('category')
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        
        conn = get_db_connection_direct()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Build query
        query = """
            SELECT id, name, category, display_order, is_active, created_at
            FROM units
        """
        params = []
        conditions = []
        
        if category:
            conditions.append("category = ?")
            params.append(category)
            
        if active_only:
            conditions.append("is_active = 1")
            
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
            
        query += " ORDER BY category, display_order, name"
        
        cursor.execute(query, params)
        units = cursor.fetchall()
        
        # Group by category
        units_by_category = {}
        for unit in units:
            category = unit['category']
            if category not in units_by_category:
                units_by_category[category] = []
            units_by_category[category].append({
                'id': unit['id'],
                'name': unit['name'],
                'category': unit['category'],
                'display_order': unit['display_order'],
                'is_active': bool(unit['is_active']),
                'created_at': unit['created_at']
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'units_by_category': units_by_category,
            'total_count': len(units)
        })
        
    except Exception as e:
        logging.error(f"Error fetching units: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@units_management_bp.route('/api/units-management', methods=['POST'])
def create_unit():
    """Create a new unit"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name') or not data.get('category'):
            return jsonify({'success': False, 'error': 'Name and category are required'}), 400
        
        conn = get_db_connection_direct()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check if unit name already exists
        cursor.execute("SELECT id FROM units WHERE name = ?", (data['name'],))
        if cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'error': 'Unit name already exists'}), 400
        
        # Insert new unit
        cursor.execute("""
            INSERT INTO units (name, category, display_order, is_active)
            VALUES (?, ?, ?, ?)
        """, (
            data['name'],
            data['category'],
            data.get('display_order', 0),
            data.get('is_active', True)
        ))
        
        unit_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'unit_id': unit_id,
            'message': 'Unit created successfully'
        })
        
    except Exception as e:
        logging.error(f"Error creating unit: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@units_management_bp.route('/api/units-management/<int:unit_id>', methods=['PUT'])
def update_unit(unit_id):
    """Update an existing unit"""
    try:
        data = request.get_json()
        
        conn = get_db_connection_direct()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check if unit exists
        cursor.execute("SELECT id FROM units WHERE id = ?", (unit_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'error': 'Unit not found'}), 404
        
        # Check if new name conflicts with existing unit (excluding current unit)
        if 'name' in data:
            cursor.execute("SELECT id FROM units WHERE name = ? AND id != ?", (data['name'], unit_id))
            if cursor.fetchone():
                conn.close()
                return jsonify({'success': False, 'error': 'Unit name already exists'}), 400
        
        # Build update query
        update_fields = []
        params = []
        
        for field in ['name', 'category', 'display_order', 'is_active']:
            if field in data:
                update_fields.append(f"{field} = ?")
                params.append(data[field])
        
        if not update_fields:
            conn.close()
            return jsonify({'success': False, 'error': 'No fields to update'}), 400
        
        params.append(unit_id)
        
        cursor.execute(f"""
            UPDATE units 
            SET {', '.join(update_fields)}
            WHERE id = ?
        """, params)
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Unit updated successfully'
        })
        
    except Exception as e:
        logging.error(f"Error updating unit: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@units_management_bp.route('/api/units-management/<int:unit_id>', methods=['DELETE'])
def delete_unit(unit_id):
    """Delete a unit (soft delete by setting is_active=False)"""
    try:
        conn = get_db_connection_direct()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check if unit exists
        cursor.execute("SELECT id FROM units WHERE id = ?", (unit_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'error': 'Unit not found'}), 404
        
        # Soft delete by setting is_active = False
        cursor.execute("UPDATE units SET is_active = 0 WHERE id = ?", (unit_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Unit deleted successfully'
        })
        
    except Exception as e:
        logging.error(f"Error deleting unit: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@units_management_bp.route('/api/units-management/categories', methods=['GET'])
def get_categories():
    """Get all unit categories"""
    try:
        conn = get_db_connection_direct()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT category, COUNT(*) as unit_count
            FROM units 
            WHERE is_active = 1
            GROUP BY category 
            ORDER BY category
        """)
        
        categories = [{'name': row['category'], 'unit_count': row['unit_count']} for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'categories': categories
        })
        
    except Exception as e:
        logging.error(f"Error fetching categories: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
