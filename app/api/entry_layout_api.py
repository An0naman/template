"""
Entry Layout API

RESTful API endpoints for managing entry type layouts and sections.
"""

import json
import logging
from flask import Blueprint, request, jsonify, g, current_app
import sqlite3

from ..services.entry_layout_service import EntryLayoutService

logger = logging.getLogger(__name__)

entry_layout_api_bp = Blueprint('entry_layout_api', __name__)


def get_db():
    """Get database connection"""
    if 'db' not in g:
        db_path = current_app.config['DATABASE_PATH']
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
    return g.db


# ============================================================================
# Layout Management Endpoints
# ============================================================================

@entry_layout_api_bp.route('/entry-types/<int:entry_type_id>/layout', methods=['GET'])
def get_entry_type_layout(entry_type_id):
    """
    Get the layout configuration for an entry type.
    
    Returns the complete layout with all sections.
    """
    try:
        layout = EntryLayoutService.get_layout_for_entry_type(entry_type_id)
        
        if not layout:
            return jsonify({'error': 'Layout not found'}), 404
        
        return jsonify(layout), 200
        
    except Exception as e:
        logger.error(f"Error getting layout for entry type {entry_type_id}: {e}", exc_info=True)
        return jsonify({'error': 'Failed to get layout'}), 500


@entry_layout_api_bp.route('/entry-types/<int:entry_type_id>/layout', methods=['POST'])
def create_entry_type_layout(entry_type_id):
    """
    Create a new layout for an entry type.
    
    This is typically called automatically when an entry type is created,
    but can be used to recreate a layout if needed.
    """
    try:
        # Check if layout already exists
        existing_layout = EntryLayoutService.get_layout_for_entry_type(entry_type_id)
        
        if existing_layout:
            return jsonify({'error': 'Layout already exists for this entry type'}), 400
        
        # Create default layout
        layout = EntryLayoutService.create_default_layout(entry_type_id)
        
        return jsonify({
            'message': 'Layout created successfully',
            'layout': layout
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating layout for entry type {entry_type_id}: {e}", exc_info=True)
        return jsonify({'error': 'Failed to create layout'}), 500


@entry_layout_api_bp.route('/entry-types/<int:entry_type_id>/layout', methods=['PUT'])
def update_entry_type_layout(entry_type_id):
    """
    Update the layout configuration (not sections, just layout-level settings).
    """
    try:
        data = request.json
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Get layout
        cursor.execute(
            "SELECT id FROM EntryTypeLayout WHERE entry_type_id = ?",
            (entry_type_id,)
        )
        
        layout = cursor.fetchone()
        
        if not layout:
            return jsonify({'error': 'Layout not found'}), 404
        
        # Update layout config if provided
        if 'layout_config' in data:
            layout_config = json.dumps(data['layout_config'])
            
            cursor.execute("""
                UPDATE EntryTypeLayout
                SET layout_config = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (layout_config, layout['id']))
            
            conn.commit()
        
        return jsonify({'message': 'Layout updated successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error updating layout for entry type {entry_type_id}: {e}", exc_info=True)
        return jsonify({'error': 'Failed to update layout'}), 500


@entry_layout_api_bp.route('/entry-types/<int:entry_type_id>/layout/reset', methods=['POST'])
def reset_entry_type_layout(entry_type_id):
    """
    Reset the layout to default configuration.
    """
    try:
        success = EntryLayoutService.reset_to_default_layout(entry_type_id)
        
        if success:
            return jsonify({'message': 'Layout reset to default successfully'}), 200
        else:
            return jsonify({'error': 'Failed to reset layout'}), 500
            
    except Exception as e:
        logger.error(f"Error resetting layout for entry type {entry_type_id}: {e}", exc_info=True)
        return jsonify({'error': 'Failed to reset layout'}), 500


# ============================================================================
# Section Management Endpoints
# ============================================================================

@entry_layout_api_bp.route('/entry-layouts/<int:layout_id>/sections', methods=['GET'])
def get_layout_sections(layout_id):
    """
    Get all sections for a layout.
    """
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, layout_id, section_type, title, position_x, position_y,
                   width, height, is_visible, is_collapsible, default_collapsed,
                   config, display_order, created_at, updated_at
            FROM EntryLayoutSection
            WHERE layout_id = ?
            ORDER BY position_y, position_x
        """, (layout_id,))
        
        sections = []
        for row in cursor.fetchall():
            sections.append({
                'id': row['id'],
                'layout_id': row['layout_id'],
                'section_type': row['section_type'],
                'title': row['title'],
                'position_x': row['position_x'],
                'position_y': row['position_y'],
                'width': row['width'],
                'height': row['height'],
                'is_visible': bool(row['is_visible']),
                'is_collapsible': bool(row['is_collapsible']),
                'default_collapsed': bool(row['default_collapsed']),
                'config': json.loads(row['config'] or '{}'),
                'display_order': row['display_order'],
                'created_at': row['created_at'],
                'updated_at': row['updated_at']
            })
        
        return jsonify(sections), 200
        
    except Exception as e:
        logger.error(f"Error getting sections for layout {layout_id}: {e}", exc_info=True)
        return jsonify({'error': 'Failed to get sections'}), 500


@entry_layout_api_bp.route('/entry-layouts/<int:layout_id>/sections', methods=['POST'])
def add_layout_section(layout_id):
    """
    Add a new section to a layout.
    """
    try:
        data = request.json
        
        if not data or 'section_type' not in data:
            return jsonify({'error': 'section_type is required'}), 400
        
        section_id = EntryLayoutService.add_section(layout_id, data)
        
        if section_id:
            return jsonify({
                'message': 'Section added successfully',
                'section_id': section_id
            }), 201
        else:
            return jsonify({'error': 'Failed to add section'}), 500
            
    except Exception as e:
        logger.error(f"Error adding section to layout {layout_id}: {e}", exc_info=True)
        return jsonify({'error': 'Failed to add section'}), 500


@entry_layout_api_bp.route('/entry-layouts/<int:layout_id>/sections/<int:section_id>', methods=['PUT'])
def update_layout_section(layout_id, section_id):
    """
    Update a specific section.
    """
    try:
        data = request.json
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Verify section belongs to layout
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id FROM EntryLayoutSection WHERE id = ? AND layout_id = ?",
            (section_id, layout_id)
        )
        
        if not cursor.fetchone():
            return jsonify({'error': 'Section not found'}), 404
        
        success = EntryLayoutService.update_section(section_id, data)
        
        if success:
            return jsonify({'message': 'Section updated successfully'}), 200
        else:
            return jsonify({'error': 'Failed to update section'}), 500
            
    except Exception as e:
        logger.error(f"Error updating section {section_id}: {e}", exc_info=True)
        return jsonify({'error': 'Failed to update section'}), 500


@entry_layout_api_bp.route('/entry-layouts/<int:layout_id>/sections/<int:section_id>', methods=['DELETE'])
def delete_layout_section(layout_id, section_id):
    """
    Delete a section.
    """
    try:
        # Verify section belongs to layout
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id FROM EntryLayoutSection WHERE id = ? AND layout_id = ?",
            (section_id, layout_id)
        )
        
        if not cursor.fetchone():
            return jsonify({'error': 'Section not found'}), 404
        
        success = EntryLayoutService.delete_section(section_id)
        
        if success:
            return jsonify({'message': 'Section deleted successfully'}), 200
        else:
            return jsonify({'error': 'Failed to delete section'}), 500
            
    except Exception as e:
        logger.error(f"Error deleting section {section_id}: {e}", exc_info=True)
        return jsonify({'error': 'Failed to delete section'}), 500


@entry_layout_api_bp.route('/entry-layouts/<int:layout_id>/sections/positions', methods=['PATCH'])
def update_section_positions(layout_id):
    """
    Bulk update section positions (used when dragging/resizing in grid).
    
    Expects:
    {
        "sections": [
            {"id": 1, "position_x": 0, "position_y": 0, "width": 12, "height": 2},
            {"id": 2, "position_x": 0, "position_y": 2, "width": 6, "height": 4},
            ...
        ]
    }
    """
    try:
        data = request.json
        
        if not data or 'sections' not in data:
            return jsonify({'error': 'sections array is required'}), 400
        
        sections = data['sections']
        
        if not isinstance(sections, list):
            return jsonify({'error': 'sections must be an array'}), 400
        
        success = EntryLayoutService.update_section_positions(layout_id, sections)
        
        if success:
            return jsonify({
                'message': 'Section positions updated successfully',
                'updated_count': len(sections)
            }), 200
        else:
            return jsonify({'error': 'Failed to update section positions'}), 500
            
    except Exception as e:
        logger.error(f"Error updating section positions for layout {layout_id}: {e}", exc_info=True)
        return jsonify({'error': 'Failed to update section positions'}), 500


# ============================================================================
# Section Types Endpoint
# ============================================================================

@entry_layout_api_bp.route('/entry-layouts/available-sections', methods=['GET'])
def get_available_sections():
    """
    Get list of all available section types with their default configurations.
    Used by the layout builder UI to populate the section palette.
    """
    try:
        sections = EntryLayoutService.get_available_section_types()
        return jsonify(sections), 200
        
    except Exception as e:
        logger.error(f"Error getting available sections: {e}", exc_info=True)
        return jsonify({'error': 'Failed to get available sections'}), 500


# ============================================================================
# Entry Type Information (Helper Endpoint)
# ============================================================================

@entry_layout_api_bp.route('/entry-types/<int:entry_type_id>/info', methods=['GET'])
def get_entry_type_info(entry_type_id):
    """
    Get basic information about an entry type.
    Used by the layout builder to display entry type details.
    """
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, singular_label, plural_label, description,
                   has_sensors, show_labels_section, show_end_dates
            FROM EntryType
            WHERE id = ?
        """, (entry_type_id,))
        
        row = cursor.fetchone()
        
        if not row:
            return jsonify({'error': 'Entry type not found'}), 404
        
        return jsonify({
            'id': row['id'],
            'name': row['name'],
            'singular_label': row['singular_label'],
            'plural_label': row['plural_label'],
            'description': row['description'],
            'has_sensors': bool(row['has_sensors']),
            'show_labels_section': bool(row['show_labels_section']),
            'show_end_dates': bool(row['show_end_dates'])
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting entry type info: {e}", exc_info=True)
        return jsonify({'error': 'Failed to get entry type info'}), 500


# ============================================================================
# Tab Management Endpoints
# ============================================================================

@entry_layout_api_bp.route('/entry-layouts/<int:layout_id>/tabs', methods=['GET'])
def get_layout_tabs(layout_id):
    """
    Get all tabs for a layout.
    """
    try:
        tabs = EntryLayoutService.get_tabs_for_layout(layout_id)
        return jsonify(tabs), 200
        
    except Exception as e:
        logger.error(f"Error getting tabs for layout {layout_id}: {e}", exc_info=True)
        return jsonify({'error': 'Failed to get tabs'}), 500


@entry_layout_api_bp.route('/entry-layouts/<int:layout_id>/tabs', methods=['POST'])
def create_layout_tab(layout_id):
    """
    Create a new tab for a layout.
    
    Expected JSON body:
    {
        "tab_id": "sensors",  // unique identifier
        "tab_label": "Sensor Data",  // display name
        "tab_icon": "fa-thermometer-half",  // FontAwesome icon (optional)
        "display_order": 1  // optional
    }
    """
    try:
        data = request.json
        
        if not data or 'tab_id' not in data or 'tab_label' not in data:
            return jsonify({'error': 'tab_id and tab_label are required'}), 400
        
        tab_id = EntryLayoutService.create_tab(layout_id, data)
        
        if tab_id:
            return jsonify({
                'message': 'Tab created successfully',
                'tab_id': tab_id
            }), 201
        else:
            return jsonify({'error': 'Failed to create tab'}), 500
        
    except Exception as e:
        logger.error(f"Error creating tab for layout {layout_id}: {e}", exc_info=True)
        return jsonify({'error': 'Failed to create tab'}), 500


@entry_layout_api_bp.route('/entry-layout-tabs/<int:tab_id>', methods=['PUT'])
def update_layout_tab(tab_id):
    """
    Update a tab's properties.
    
    Expected JSON body (all fields optional):
    {
        "tab_label": "New Label",
        "tab_icon": "fa-new-icon",
        "display_order": 2,
        "is_visible": true
    }
    """
    try:
        data = request.json
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        success = EntryLayoutService.update_tab(tab_id, data)
        
        if success:
            return jsonify({'message': 'Tab updated successfully'}), 200
        else:
            return jsonify({'error': 'Failed to update tab'}), 500
        
    except Exception as e:
        logger.error(f"Error updating tab {tab_id}: {e}", exc_info=True)
        return jsonify({'error': 'Failed to update tab'}), 500


@entry_layout_api_bp.route('/entry-layout-tabs/<int:tab_id>', methods=['DELETE'])
def delete_layout_tab(tab_id):
    """
    Delete a tab. Sections in this tab will be moved to the 'main' tab.
    Cannot delete the 'main' tab.
    """
    try:
        success = EntryLayoutService.delete_tab(tab_id)
        
        if success:
            return jsonify({'message': 'Tab deleted successfully'}), 200
        else:
            return jsonify({'error': 'Failed to delete tab'}), 500
        
    except Exception as e:
        logger.error(f"Error deleting tab {tab_id}: {e}", exc_info=True)
        return jsonify({'error': 'Failed to delete tab'}), 500


@entry_layout_api_bp.route('/entry-layouts/<int:layout_id>/sections-by-tab', methods=['GET'])
def get_sections_by_tab(layout_id):
    """
    Get all sections organized by tab for a layout.
    
    Returns a dictionary with tab_id as keys and lists of sections as values.
    """
    try:
        sections_by_tab = EntryLayoutService.get_sections_by_tab(layout_id)
        return jsonify(sections_by_tab), 200
        
    except Exception as e:
        logger.error(f"Error getting sections by tab for layout {layout_id}: {e}", exc_info=True)
        return jsonify({'error': 'Failed to get sections by tab'}), 500
