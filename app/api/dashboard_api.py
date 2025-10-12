# template_app/app/api/dashboard_api.py
"""
Dashboard API Blueprint
Provides endpoints for managing dashboards and retrieving widget data
"""

from flask import Blueprint, request, jsonify, g, current_app
import sqlite3
import json
import logging
from datetime import datetime
from app.services.dashboard_service import DashboardService

# Define a Blueprint for Dashboard API
dashboard_api_bp = Blueprint('dashboard_api', __name__)

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
# Dashboard Management Endpoints
# ============================================================================

@dashboard_api_bp.route('/dashboards', methods=['GET'])
def get_dashboards():
    """Get all dashboards"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, description, is_default, layout_config, created_at, updated_at
            FROM Dashboard
            ORDER BY is_default DESC, name ASC
        """)
        
        dashboards = []
        for row in cursor.fetchall():
            dashboards.append({
                'id': row['id'],
                'name': row['name'],
                'description': row['description'],
                'is_default': bool(row['is_default']),
                'layout_config': json.loads(row['layout_config']),
                'created_at': row['created_at'],
                'updated_at': row['updated_at']
            })
        
        return jsonify(dashboards), 200
        
    except Exception as e:
        logger.error(f"Error getting dashboards: {e}", exc_info=True)
        return jsonify({'error': 'Failed to get dashboards'}), 500

@dashboard_api_bp.route('/dashboards/<int:dashboard_id>', methods=['GET'])
def get_dashboard(dashboard_id):
    """Get a specific dashboard with its widgets"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get dashboard
        cursor.execute("""
            SELECT id, name, description, is_default, layout_config, created_at, updated_at
            FROM Dashboard
            WHERE id = ?
        """, (dashboard_id,))
        
        dashboard_row = cursor.fetchone()
        if not dashboard_row:
            return jsonify({'error': 'Dashboard not found'}), 404
        
        # Get widgets for this dashboard
        cursor.execute("""
            SELECT id, dashboard_id, widget_type, title, position_x, position_y,
                   width, height, config, data_source_type, data_source_id,
                   refresh_interval, created_at, updated_at
            FROM DashboardWidget
            WHERE dashboard_id = ?
            ORDER BY position_y, position_x
        """, (dashboard_id,))
        
        widgets = []
        for row in cursor.fetchall():
            widgets.append({
                'id': row['id'],
                'dashboard_id': row['dashboard_id'],
                'widget_type': row['widget_type'],
                'title': row['title'],
                'position_x': row['position_x'],
                'position_y': row['position_y'],
                'width': row['width'],
                'height': row['height'],
                'config': json.loads(row['config'] or '{}'),
                'data_source_type': row['data_source_type'],
                'data_source_id': row['data_source_id'],
                'refresh_interval': row['refresh_interval'],
                'created_at': row['created_at'],
                'updated_at': row['updated_at']
            })
        
        dashboard = {
            'id': dashboard_row['id'],
            'name': dashboard_row['name'],
            'description': dashboard_row['description'],
            'is_default': bool(dashboard_row['is_default']),
            'layout_config': json.loads(dashboard_row['layout_config']),
            'widgets': widgets,
            'created_at': dashboard_row['created_at'],
            'updated_at': dashboard_row['updated_at']
        }
        
        return jsonify(dashboard), 200
        
    except Exception as e:
        logger.error(f"Error getting dashboard: {e}", exc_info=True)
        return jsonify({'error': 'Failed to get dashboard'}), 500

@dashboard_api_bp.route('/dashboards', methods=['POST'])
def create_dashboard():
    """Create a new dashboard"""
    try:
        data = request.json
        if not data or 'name' not in data:
            return jsonify({'error': 'Dashboard name is required'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if name already exists
        cursor.execute("SELECT id FROM Dashboard WHERE name = ?", (data['name'],))
        if cursor.fetchone():
            return jsonify({'error': 'A dashboard with this name already exists'}), 400
        
        # If this is set as default, clear other defaults
        if data.get('is_default', False):
            cursor.execute("UPDATE Dashboard SET is_default = 0")
        
        layout_config = json.dumps(data.get('layout_config', {'cols': 12, 'rowHeight': 100}))
        
        cursor.execute("""
            INSERT INTO Dashboard (name, description, is_default, layout_config)
            VALUES (?, ?, ?, ?)
        """, (
            data['name'],
            data.get('description', ''),
            1 if data.get('is_default', False) else 0,
            layout_config
        ))
        
        conn.commit()
        dashboard_id = cursor.lastrowid
        
        logger.info(f"Created dashboard: {data['name']} (ID: {dashboard_id})")
        
        return jsonify({
            'id': dashboard_id,
            'message': 'Dashboard created successfully'
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating dashboard: {e}", exc_info=True)
        return jsonify({'error': 'Failed to create dashboard'}), 500

@dashboard_api_bp.route('/dashboards/<int:dashboard_id>', methods=['PUT'])
def update_dashboard(dashboard_id):
    """Update an existing dashboard"""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if dashboard exists
        cursor.execute("SELECT id FROM Dashboard WHERE id = ?", (dashboard_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Dashboard not found'}), 404
        
        # If name is being updated, check for duplicates
        if 'name' in data:
            cursor.execute("SELECT id FROM Dashboard WHERE name = ? AND id != ?", (data['name'], dashboard_id))
            if cursor.fetchone():
                return jsonify({'error': 'A dashboard with this name already exists'}), 400
        
        # If setting as default, clear other defaults
        if data.get('is_default', False):
            cursor.execute("UPDATE Dashboard SET is_default = 0")
        
        # Build update query dynamically
        update_fields = []
        params = []
        
        if 'name' in data:
            update_fields.append('name = ?')
            params.append(data['name'])
        
        if 'description' in data:
            update_fields.append('description = ?')
            params.append(data['description'])
        
        if 'is_default' in data:
            update_fields.append('is_default = ?')
            params.append(1 if data['is_default'] else 0)
        
        if 'layout_config' in data:
            update_fields.append('layout_config = ?')
            params.append(json.dumps(data['layout_config']))
        
        update_fields.append('updated_at = CURRENT_TIMESTAMP')
        params.append(dashboard_id)
        
        query = f"UPDATE Dashboard SET {', '.join(update_fields)} WHERE id = ?"
        cursor.execute(query, params)
        
        conn.commit()
        
        logger.info(f"Updated dashboard ID: {dashboard_id}")
        
        return jsonify({'message': 'Dashboard updated successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error updating dashboard: {e}", exc_info=True)
        return jsonify({'error': 'Failed to update dashboard'}), 500

@dashboard_api_bp.route('/dashboards/<int:dashboard_id>', methods=['DELETE'])
def delete_dashboard(dashboard_id):
    """Delete a dashboard"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM Dashboard WHERE id = ?", (dashboard_id,))
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'Dashboard not found'}), 404
        
        conn.commit()
        
        logger.info(f"Deleted dashboard ID: {dashboard_id}")
        
        return jsonify({'message': 'Dashboard deleted successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error deleting dashboard: {e}", exc_info=True)
        return jsonify({'error': 'Failed to delete dashboard'}), 500

@dashboard_api_bp.route('/dashboards/<int:dashboard_id>/set_default', methods=['POST'])
def set_default_dashboard(dashboard_id):
    """Set a dashboard as the default"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if dashboard exists
        cursor.execute("SELECT id FROM Dashboard WHERE id = ?", (dashboard_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Dashboard not found'}), 404
        
        # Clear all defaults first
        cursor.execute("UPDATE Dashboard SET is_default = 0")
        
        # Set this dashboard as default
        cursor.execute("UPDATE Dashboard SET is_default = 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (dashboard_id,))
        
        conn.commit()
        
        return jsonify({'message': 'Default dashboard updated successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error setting default dashboard: {e}", exc_info=True)
        return jsonify({'error': 'Failed to set default dashboard'}), 500

# ============================================================================
# Widget Management Endpoints
# ============================================================================

@dashboard_api_bp.route('/dashboards/<int:dashboard_id>/widgets', methods=['POST'])
def create_widget(dashboard_id):
    """Create a new widget on a dashboard"""
    try:
        data = request.json
        if not data or 'widget_type' not in data or 'title' not in data:
            return jsonify({'error': 'Widget type and title are required'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if dashboard exists
        cursor.execute("SELECT id FROM Dashboard WHERE id = ?", (dashboard_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Dashboard not found'}), 404
        
        config = json.dumps(data.get('config', {}))
        
        cursor.execute("""
            INSERT INTO DashboardWidget (
                dashboard_id, widget_type, title, position_x, position_y,
                width, height, config, data_source_type, data_source_id, refresh_interval
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            dashboard_id,
            data['widget_type'],
            data['title'],
            data.get('position_x', 0),
            data.get('position_y', 0),
            data.get('width', 4),
            data.get('height', 2),
            config,
            data.get('data_source_type'),
            data.get('data_source_id'),
            data.get('refresh_interval', 300)
        ))
        
        conn.commit()
        widget_id = cursor.lastrowid
        
        logger.info(f"Created widget: {data['title']} on dashboard {dashboard_id}")
        
        return jsonify({
            'id': widget_id,
            'message': 'Widget created successfully'
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating widget: {e}", exc_info=True)
        return jsonify({'error': 'Failed to create widget'}), 500

@dashboard_api_bp.route('/widgets/<int:widget_id>', methods=['PUT'])
def update_widget(widget_id):
    """Update an existing widget"""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if widget exists
        cursor.execute("SELECT id FROM DashboardWidget WHERE id = ?", (widget_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Widget not found'}), 404
        
        # Build update query dynamically
        update_fields = []
        params = []
        
        for field in ['widget_type', 'title', 'position_x', 'position_y', 'width', 'height',
                      'data_source_type', 'data_source_id', 'refresh_interval']:
            if field in data:
                update_fields.append(f'{field} = ?')
                params.append(data[field])
        
        if 'config' in data:
            update_fields.append('config = ?')
            params.append(json.dumps(data['config']))
        
        update_fields.append('updated_at = CURRENT_TIMESTAMP')
        params.append(widget_id)
        
        query = f"UPDATE DashboardWidget SET {', '.join(update_fields)} WHERE id = ?"
        cursor.execute(query, params)
        
        conn.commit()
        
        logger.info(f"Updated widget ID: {widget_id}")
        
        return jsonify({'message': 'Widget updated successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error updating widget: {e}", exc_info=True)
        return jsonify({'error': 'Failed to update widget'}), 500

@dashboard_api_bp.route('/widgets/<int:widget_id>', methods=['DELETE'])
def delete_widget(widget_id):
    """Delete a widget"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM DashboardWidget WHERE id = ?", (widget_id,))
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'Widget not found'}), 404
        
        conn.commit()
        
        logger.info(f"Deleted widget ID: {widget_id}")
        
        return jsonify({'message': 'Widget deleted successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error deleting widget: {e}", exc_info=True)
        return jsonify({'error': 'Failed to delete widget'}), 500

# ============================================================================
# Widget Data Endpoints
# ============================================================================

@dashboard_api_bp.route('/widgets/<int:widget_id>/data', methods=['GET'])
def get_widget_data(widget_id):
    """Get data for a specific widget"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get widget configuration
        cursor.execute("""
            SELECT id, widget_type, config, data_source_type, data_source_id
            FROM DashboardWidget
            WHERE id = ?
        """, (widget_id,))
        
        widget_row = cursor.fetchone()
        if not widget_row:
            return jsonify({'error': 'Widget not found'}), 404
        
        widget = dict(widget_row)
        
        # Get widget data using DashboardService
        data = DashboardService.get_widget_data(widget)
        
        return jsonify(data), 200
        
    except Exception as e:
        logger.error(f"Error getting widget data: {e}", exc_info=True)
        return jsonify({'error': 'Failed to get widget data'}), 500

@dashboard_api_bp.route('/dashboards/<int:dashboard_id>/data', methods=['GET'])
def get_dashboard_data(dashboard_id):
    """Get data for all widgets on a dashboard"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get all widgets for this dashboard
        cursor.execute("""
            SELECT id, widget_type, title, config, data_source_type, data_source_id
            FROM DashboardWidget
            WHERE dashboard_id = ?
        """, (dashboard_id,))
        
        widgets = cursor.fetchall()
        
        widget_data = {}
        for widget_row in widgets:
            widget = dict(widget_row)
            widget_id = widget['id']
            
            try:
                data = DashboardService.get_widget_data(widget)
                widget_data[widget_id] = {
                    'title': widget['title'],
                    'widget_type': widget['widget_type'],
                    'data': data
                }
            except Exception as e:
                logger.error(f"Error getting data for widget {widget_id}: {e}")
                widget_data[widget_id] = {
                    'title': widget['title'],
                    'widget_type': widget['widget_type'],
                    'error': str(e)
                }
        
        return jsonify(widget_data), 200
        
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}", exc_info=True)
        return jsonify({'error': 'Failed to get dashboard data'}), 500

# ============================================================================
# Utility Endpoints
# ============================================================================

@dashboard_api_bp.route('/dashboard_sources', methods=['GET'])
def get_dashboard_sources():
    """Get available data sources for widgets"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get saved searches
        cursor.execute("SELECT id, name FROM SavedSearch ORDER BY name")
        saved_searches = [{'id': row['id'], 'name': row['name']} for row in cursor.fetchall()]
        
        # Get entry types
        cursor.execute("SELECT id, singular_label, plural_label FROM EntryType ORDER BY singular_label")
        entry_types = [{'id': row['id'], 'label': row['plural_label']} for row in cursor.fetchall()]
        
        # Get available sensor types
        cursor.execute("SELECT DISTINCT sensor_type FROM SharedSensorData ORDER BY sensor_type")
        sensor_types = [row['sensor_type'] for row in cursor.fetchall()]
        
        # Fallback to legacy sensor data if no shared data
        if not sensor_types:
            cursor.execute("SELECT DISTINCT sensor_type FROM SensorData ORDER BY sensor_type")
            sensor_types = [row['sensor_type'] for row in cursor.fetchall()]
        
        return jsonify({
            'saved_searches': saved_searches,
            'entry_types': entry_types,
            'sensor_types': sensor_types
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting dashboard sources: {e}", exc_info=True)
        return jsonify({'error': 'Failed to get dashboard sources'}), 500
