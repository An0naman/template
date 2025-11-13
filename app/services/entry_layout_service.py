"""
Entry Layout Service

Provides business logic for managing entry type layouts and sections.
Similar to DashboardService but for entry detail page configurations.
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from flask import g
import sqlite3

logger = logging.getLogger(__name__)


def get_db():
    """Get database connection"""
    if 'db' not in g:
        from flask import current_app
        db_path = current_app.config['DATABASE_PATH']
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
    return g.db


class EntryLayoutService:
    """Service for managing entry type layouts"""
    
    # Default section configurations - ONLY showing sections visible in layout builder
    DEFAULT_SECTIONS = {
        'header': {
            'title': 'Entry Details',
            'section_type': 'header',
            'position_x': 0,
            'position_y': 0,  # Row 0
            'width': 12,
            'height': 3,
            'is_visible': 1,
            'is_collapsible': 0,
            'default_collapsed': 0,
            'display_order': 1,
            'config': {
                'show_dates': True,
                'show_status': True,
                'show_description': True
            }
        },
        'ai_assistant': {
            'title': 'AI Assistant',
            'section_type': 'ai_assistant',
            'position_x': 0,
            'position_y': 1,  # Row 1
            'width': 12,
            'height': 4,
            'is_visible': 1,
            'is_collapsible': 1,
            'default_collapsed': 0,
            'display_order': 2,
            'config': {}
        },
        'sensors': {
            'title': 'Sensor Data',
            'section_type': 'sensors',
            'position_x': 0,
            'position_y': 2,  # Row 2, left side
            'width': 7,
            'height': 5,
            'is_visible': 1,
            'is_collapsible': 1,
            'default_collapsed': 0,
            'display_order': 3,
            'config': {
                'default_chart_type': 'line',
                'default_time_range': '7d'
            }
        },
        'notes': {
            'title': 'Notes',
            'section_type': 'notes',
            'position_x': 7,
            'position_y': 2,  # Row 2, right side
            'width': 5,
            'height': 5,
            'is_visible': 1,
            'is_collapsible': 1,
            'default_collapsed': 0,
            'display_order': 4,
            'config': {
                'default_note_type': 'General',
                'show_note_relationships': True
            }
        },
        # ALL other sections hidden by default
        'relationships': {
            'title': 'Relationships',
            'section_type': 'relationships',
            'position_x': 0,
            'position_y': 100,
            'width': 12,
            'height': 4,
            'is_visible': 0,
            'is_collapsible': 1,
            'default_collapsed': 0,
            'display_order': 100,
            'config': {}
        },
        'reminders': {
            'title': 'Reminders',
            'section_type': 'reminders',
            'position_x': 0,
            'position_y': 102,
            'width': 12,
            'height': 3,
            'is_visible': 0,
            'is_collapsible': 1,
            'default_collapsed': 0,
            'display_order': 102,
            'config': {}
        },
        'attachments': {
            'title': 'Attachments',
            'section_type': 'attachments',
            'position_x': 0,
            'position_y': 103,
            'width': 6,
            'height': 3,
            'is_visible': 0,
            'is_collapsible': 1,
            'default_collapsed': 0,
            'display_order': 103,
            'config': {}
        },
        'form_fields': {
            'title': 'Custom Fields',
            'section_type': 'form_fields',
            'position_x': 0,
            'position_y': 104,
            'width': 6,
            'height': 3,
            'is_visible': 0,
            'is_collapsible': 1,
            'default_collapsed': 0,
            'display_order': 104,
            'config': {}
        },
        'qr_code': {
            'title': 'QR Code',
            'section_type': 'qr_code',
            'position_x': 0,
            'position_y': 105,
            'width': 4,
            'height': 3,
            'is_visible': 0,
            'is_collapsible': 1,
            'default_collapsed': 1,
            'display_order': 105,
            'config': {}
        },
        'label_printing': {
            'title': 'Label Printing',
            'section_type': 'label_printing',
            'position_x': 0,
            'position_y': 106,
            'width': 12,
            'height': 6,
            'is_visible': 0,
            'is_collapsible': 1,
            'default_collapsed': 0,
            'display_order': 106,
            'config': {
                'default_printer': 'niimbot_b1',
                'default_font_size': 'medium',
                'default_density': 3,
                'include_qr_default': True,
                'default_copies': 1
            }
        },
        'relationship_opportunities': {
            'title': 'Shared Relationships',
            'section_type': 'relationship_opportunities',
            'position_x': 0,
            'position_y': 107,
            'width': 12,
            'height': 3,
            'is_visible': 0,
            'is_collapsible': 1,
            'default_collapsed': 1,
            'display_order': 107,
            'config': {}
        },
        'timeline': {
            'title': 'Progress Timeline',
            'section_type': 'timeline',
            'position_x': 0,
            'position_y': 108,
            'width': 12,
            'height': 3,
            'is_visible': 0,
            'is_collapsible': 1,
            'default_collapsed': 0,
            'display_order': 108,
            'config': {}
        },
        'drawio': {
            'title': 'Draw.io Diagram',
            'section_type': 'drawio',
            'position_x': 0,
            'position_y': 109,
            'width': 12,
            'height': 6,
            'is_visible': 0,
            'is_collapsible': 1,
            'default_collapsed': 0,
            'display_order': 109,
            'config': {
                'theme': 'auto',
                'toolbar': True,
                'save_automatically': True
            }
        }
    }
    
    @staticmethod
    def get_layout_for_entry_type(entry_type_id: int) -> Optional[Dict[str, Any]]:
        """
        Get the complete layout configuration for an entry type.
        
        Args:
            entry_type_id: The ID of the entry type
            
        Returns:
            Dictionary containing layout and sections, or None if not found
        """
        try:
            conn = get_db()
            cursor = conn.cursor()
            
            # Get layout
            cursor.execute("""
                SELECT id, entry_type_id, layout_config, created_at, updated_at
                FROM EntryTypeLayout
                WHERE entry_type_id = ?
            """, (entry_type_id,))
            
            layout_row = cursor.fetchone()
            
            if not layout_row:
                # No layout exists, create default one
                logger.info(f"No layout found for entry type {entry_type_id}, creating default")
                return EntryLayoutService.create_default_layout(entry_type_id)
            
            # Get tabs
            tabs = EntryLayoutService.get_tabs_for_layout(layout_row['id'])
            
            # Get sections organized by tab
            sections_by_tab = EntryLayoutService.get_sections_by_tab(layout_row['id'])
            
            # Also get flat list for backward compatibility
            cursor.execute("""
                SELECT id, layout_id, section_type, title, position_x, position_y,
                       width, height, is_visible, is_collapsible, default_collapsed,
                       config, display_order, tab_id, tab_order, created_at, updated_at
                FROM EntryLayoutSection
                WHERE layout_id = ?
                ORDER BY tab_order, position_y, position_x
            """, (layout_row['id'],))
            
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
                    'tab_id': row['tab_id'] or 'main',
                    'tab_order': row['tab_order'],
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                })
            
            return {
                'id': layout_row['id'],
                'entry_type_id': layout_row['entry_type_id'],
                'layout_config': json.loads(layout_row['layout_config']),
                'tabs': tabs,
                'sections': sections,
                'sections_by_tab': sections_by_tab,
                'created_at': layout_row['created_at'],
                'updated_at': layout_row['updated_at']
            }
            
        except Exception as e:
            logger.error(f"Error getting layout for entry type {entry_type_id}: {e}")
            return None
    
    @staticmethod
    def create_default_layout(entry_type_id: int) -> Dict[str, Any]:
        """
        Create a default layout for an entry type.
        
        Args:
            entry_type_id: The ID of the entry type
            
        Returns:
            The created layout configuration
        """
        try:
            conn = get_db()
            cursor = conn.cursor()
            
            # Get entry type settings
            cursor.execute("""
                SELECT has_sensors, show_labels_section, show_end_dates
                FROM EntryType
                WHERE id = ?
            """, (entry_type_id,))
            
            entry_type = cursor.fetchone()
            if not entry_type:
                raise ValueError(f"Entry type {entry_type_id} not found")
            
            # Create layout
            layout_config = json.dumps({'cols': 12, 'rowHeight': 80})
            
            cursor.execute("""
                INSERT INTO EntryTypeLayout (entry_type_id, layout_config)
                VALUES (?, ?)
            """, (entry_type_id, layout_config))
            
            layout_id = cursor.lastrowid
            
            # Create default 'main' tab
            cursor.execute("""
                INSERT INTO EntryLayoutTab (
                    layout_id, tab_id, tab_label, tab_icon, display_order, is_visible
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (layout_id, 'main', 'Overview', 'fa-home', 0, 1))
            
            # Determine which sections to include
            sections_to_add = ['header', 'notes', 'relationships', 'attachments']
            
            if entry_type['show_labels_section']:
                sections_to_add.append('label_printing')
            
            if entry_type['has_sensors']:
                sections_to_add.append('sensors')
            
            sections_to_add.extend([
                'reminders', 'ai_assistant', 'form_fields',
                'qr_code', 'relationship_opportunities', 'timeline', 'drawio'
            ])
            
            # Create sections
            for section_key in sections_to_add:
                if section_key in EntryLayoutService.DEFAULT_SECTIONS:
                    section_data = EntryLayoutService.DEFAULT_SECTIONS[section_key]
                    
                    is_visible = section_data['is_visible']
                    if section_key == 'label_printing' and not entry_type['show_labels_section']:
                        is_visible = 0
                    elif section_key == 'sensors' and not entry_type['has_sensors']:
                        is_visible = 0
                    
                    cursor.execute("""
                        INSERT INTO EntryLayoutSection (
                            layout_id, section_type, title, position_x, position_y,
                            width, height, is_visible, is_collapsible, default_collapsed,
                            config, display_order, tab_id, tab_order
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        layout_id,
                        section_data['section_type'],
                        section_data['title'],
                        section_data['position_x'],
                        section_data['position_y'],
                        section_data['width'],
                        section_data['height'],
                        is_visible,
                        section_data['is_collapsible'],
                        section_data['default_collapsed'],
                        json.dumps(section_data['config']),
                        section_data['display_order'],
                        'main',  # Default to 'main' tab
                        section_data['display_order']  # Use display_order as tab_order
                    ))
            
            conn.commit()
            
            logger.info(f"Created default layout for entry type {entry_type_id}")
            
            # Return the created layout
            return EntryLayoutService.get_layout_for_entry_type(entry_type_id)
            
        except Exception as e:
            logger.error(f"Error creating default layout for entry type {entry_type_id}: {e}")
            if conn:
                conn.rollback()
            raise
    
    @staticmethod
    def update_section_positions(layout_id: int, sections_data: List[Dict]) -> bool:
        """
        Update positions of multiple sections at once.
        
        Args:
            layout_id: The layout ID
            sections_data: List of section updates with id, position_x, position_y, width, height
            
        Returns:
            True if successful
        """
        try:
            conn = get_db()
            cursor = conn.cursor()
            
            for section in sections_data:
                cursor.execute("""
                    UPDATE EntryLayoutSection
                    SET position_x = ?, position_y = ?, width = ?, height = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND layout_id = ?
                """, (
                    section.get('position_x', 0),
                    section.get('position_y', 0),
                    section.get('width', 12),
                    section.get('height', 2),
                    section['id'],
                    layout_id
                ))
            
            # Update layout timestamp
            cursor.execute("""
                UPDATE EntryTypeLayout
                SET updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (layout_id,))
            
            conn.commit()
            
            logger.info(f"Updated {len(sections_data)} section positions for layout {layout_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating section positions: {e}")
            if conn:
                conn.rollback()
            return False
    
    @staticmethod
    def update_section(section_id: int, updates: Dict[str, Any]) -> bool:
        """
        Update a specific section's properties.
        
        Args:
            section_id: The section ID
            updates: Dictionary of fields to update
            
        Returns:
            True if successful
        """
        try:
            conn = get_db()
            cursor = conn.cursor()
            
            # Build UPDATE query dynamically
            allowed_fields = [
                'title', 'position_x', 'position_y', 'width', 'height',
                'is_visible', 'is_collapsible', 'default_collapsed', 'config', 'display_order',
                'tab_id', 'tab_order'
            ]
            
            set_clauses = []
            values = []
            
            for field, value in updates.items():
                if field in allowed_fields:
                    set_clauses.append(f"{field} = ?")
                    if field == 'config' and isinstance(value, dict):
                        values.append(json.dumps(value))
                    else:
                        values.append(value)
            
            if not set_clauses:
                return False
            
            set_clauses.append("updated_at = CURRENT_TIMESTAMP")
            values.append(section_id)
            
            query = f"UPDATE EntryLayoutSection SET {', '.join(set_clauses)} WHERE id = ?"
            
            cursor.execute(query, values)
            conn.commit()
            
            logger.info(f"Updated section {section_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating section {section_id}: {e}")
            if conn:
                conn.rollback()
            return False
    
    @staticmethod
    def toggle_section_visibility(section_id: int, is_visible: bool) -> bool:
        """
        Toggle a section's visibility.
        
        Args:
            section_id: The section ID
            is_visible: New visibility state
            
        Returns:
            True if successful
        """
        return EntryLayoutService.update_section(section_id, {'is_visible': 1 if is_visible else 0})
    
    @staticmethod
    def add_section(layout_id: int, section_data: Dict[str, Any]) -> Optional[int]:
        """
        Add a new section to a layout.
        
        Args:
            layout_id: The layout ID
            section_data: Section configuration
            
        Returns:
            The new section ID or None
        """
        try:
            conn = get_db()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO EntryLayoutSection (
                    layout_id, section_type, title, position_x, position_y,
                    width, height, is_visible, is_collapsible, default_collapsed,
                    config, display_order, tab_id, tab_order
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                layout_id,
                section_data['section_type'],
                section_data.get('title', ''),
                section_data.get('position_x', 0),
                section_data.get('position_y', 0),
                section_data.get('width', 12),
                section_data.get('height', 2),
                section_data.get('is_visible', 1),
                section_data.get('is_collapsible', 1),
                section_data.get('default_collapsed', 0),
                json.dumps(section_data.get('config', {})),
                section_data.get('display_order', 0),
                section_data.get('tab_id', 'main'),  # Default to 'main' tab
                section_data.get('tab_order', 0)
            ))
            
            conn.commit()
            section_id = cursor.lastrowid
            
            logger.info(f"Added section {section_id} to layout {layout_id}")
            return section_id
            
        except Exception as e:
            logger.error(f"Error adding section: {e}")
            if conn:
                conn.rollback()
            return None
    
    @staticmethod
    def delete_section(section_id: int) -> bool:
        """
        Delete a section.
        
        Args:
            section_id: The section ID
            
        Returns:
            True if successful
        """
        try:
            conn = get_db()
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM EntryLayoutSection WHERE id = ?", (section_id,))
            conn.commit()
            
            logger.info(f"Deleted section {section_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting section {section_id}: {e}")
            if conn:
                conn.rollback()
            return False
    
    @staticmethod
    def reset_to_default_layout(entry_type_id: int) -> bool:
        """
        Reset an entry type's layout to default configuration.
        
        Args:
            entry_type_id: The entry type ID
            
        Returns:
            True if successful
        """
        try:
            conn = get_db()
            cursor = conn.cursor()
            
            # Get existing layout
            cursor.execute(
                "SELECT id FROM EntryTypeLayout WHERE entry_type_id = ?",
                (entry_type_id,)
            )
            
            layout_row = cursor.fetchone()
            
            if layout_row:
                # Delete existing sections
                cursor.execute(
                    "DELETE FROM EntryLayoutSection WHERE layout_id = ?",
                    (layout_row['id'],)
                )
                
                # Delete layout
                cursor.execute(
                    "DELETE FROM EntryTypeLayout WHERE id = ?",
                    (layout_row['id'],)
                )
            
            conn.commit()
            
            # Create new default layout
            EntryLayoutService.create_default_layout(entry_type_id)
            
            logger.info(f"Reset layout for entry type {entry_type_id} to default")
            return True
            
        except Exception as e:
            logger.error(f"Error resetting layout for entry type {entry_type_id}: {e}")
            if conn:
                conn.rollback()
            return False
    
    @staticmethod
    def get_available_section_types() -> List[Dict[str, Any]]:
        """
        Get list of all available section types with their default configurations.
        
        Returns:
            List of section type configurations
        """
        return [
            {
                'section_type': key,
                'default_title': config['title'],
                'default_width': config['width'],
                'default_height': config['height'],
                'is_collapsible': config['is_collapsible'],
                'default_config': config['config']
            }
            for key, config in EntryLayoutService.DEFAULT_SECTIONS.items()
        ]
    
    # ============================================================================
    # Tab Management Methods
    # ============================================================================
    
    @staticmethod
    def get_tabs_for_layout(layout_id: int) -> List[Dict[str, Any]]:
        """
        Get all tabs for a layout.
        
        Args:
            layout_id: The layout ID
            
        Returns:
            List of tab configurations
        """
        try:
            conn = get_db()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, layout_id, tab_id, tab_label, tab_icon, 
                       display_order, is_visible, created_at, updated_at
                FROM EntryLayoutTab
                WHERE layout_id = ?
                ORDER BY display_order, id
            """, (layout_id,))
            
            tabs = []
            for row in cursor.fetchall():
                tabs.append({
                    'id': row['id'],
                    'layout_id': row['layout_id'],
                    'tab_id': row['tab_id'],
                    'tab_label': row['tab_label'],
                    'tab_icon': row['tab_icon'],
                    'display_order': row['display_order'],
                    'is_visible': bool(row['is_visible']),
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                })
            
            return tabs
            
        except Exception as e:
            logger.error(f"Error getting tabs for layout {layout_id}: {e}")
            return []
    
    @staticmethod
    def create_tab(layout_id: int, tab_data: Dict[str, Any]) -> Optional[int]:
        """
        Create a new tab for a layout.
        
        Args:
            layout_id: The layout ID
            tab_data: Tab configuration (tab_id, tab_label, tab_icon, display_order)
            
        Returns:
            The new tab ID or None
        """
        try:
            conn = get_db()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO EntryLayoutTab (
                    layout_id, tab_id, tab_label, tab_icon, display_order, is_visible
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                layout_id,
                tab_data['tab_id'],
                tab_data['tab_label'],
                tab_data.get('tab_icon', 'fa-folder'),
                tab_data.get('display_order', 0),
                tab_data.get('is_visible', 1)
            ))
            
            tab_id = cursor.lastrowid
            conn.commit()
            
            logger.info(f"Created tab {tab_id} for layout {layout_id}")
            return tab_id
            
        except Exception as e:
            logger.error(f"Error creating tab for layout {layout_id}: {e}")
            if conn:
                conn.rollback()
            return None
    
    @staticmethod
    def update_tab(tab_id: int, updates: Dict[str, Any]) -> bool:
        """
        Update a tab's properties.
        
        Args:
            tab_id: The tab ID
            updates: Dictionary of fields to update
            
        Returns:
            True if successful
        """
        try:
            conn = get_db()
            cursor = conn.cursor()
            
            # Build update query dynamically
            allowed_fields = ['tab_label', 'tab_icon', 'display_order', 'is_visible']
            set_clauses = []
            values = []
            
            for field, value in updates.items():
                if field in allowed_fields:
                    set_clauses.append(f"{field} = ?")
                    values.append(value)
            
            if not set_clauses:
                return False
            
            set_clauses.append("updated_at = CURRENT_TIMESTAMP")
            values.append(tab_id)
            
            query = f"UPDATE EntryLayoutTab SET {', '.join(set_clauses)} WHERE id = ?"
            
            cursor.execute(query, values)
            conn.commit()
            
            logger.info(f"Updated tab {tab_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating tab {tab_id}: {e}")
            if conn:
                conn.rollback()
            return False
    
    @staticmethod
    def delete_tab(tab_id: int) -> bool:
        """
        Delete a tab. Sections in this tab will be moved to 'main' tab.
        
        Args:
            tab_id: The tab ID
            
        Returns:
            True if successful
        """
        try:
            conn = get_db()
            cursor = conn.cursor()
            
            # Get the tab's tab_id (string identifier)
            cursor.execute("SELECT tab_id, layout_id FROM EntryLayoutTab WHERE id = ?", (tab_id,))
            tab_row = cursor.fetchone()
            
            if not tab_row:
                return False
            
            tab_identifier = tab_row['tab_id']
            layout_id = tab_row['layout_id']
            
            # Don't allow deleting the 'main' tab
            if tab_identifier == 'main':
                logger.warning("Cannot delete the 'main' tab")
                return False
            
            # Move sections to 'main' tab
            cursor.execute("""
                UPDATE EntryLayoutSection 
                SET tab_id = 'main'
                WHERE layout_id = (SELECT layout_id FROM EntryLayoutTab WHERE id = ?)
                AND tab_id = ?
            """, (tab_id, tab_identifier))
            
            # Delete the tab
            cursor.execute("DELETE FROM EntryLayoutTab WHERE id = ?", (tab_id,))
            
            conn.commit()
            
            logger.info(f"Deleted tab {tab_id}, moved sections to 'main' tab")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting tab {tab_id}: {e}")
            if conn:
                conn.rollback()
            return False
    
    @staticmethod
    def get_sections_by_tab(layout_id: int) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all sections organized by tab for a layout.
        
        Args:
            layout_id: The layout ID
            
        Returns:
            Dictionary with tab_id as keys and lists of sections as values
        """
        try:
            conn = get_db()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, layout_id, section_type, title, position_x, position_y,
                       width, height, is_visible, is_collapsible, default_collapsed,
                       config, display_order, tab_id, tab_order, created_at, updated_at
                FROM EntryLayoutSection
                WHERE layout_id = ?
                ORDER BY tab_id, tab_order, position_y, position_x
            """, (layout_id,))
            
            sections_by_tab = {}
            for row in cursor.fetchall():
                tab_id = row['tab_id'] or 'main'
                
                section = {
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
                    'tab_id': tab_id,
                    'tab_order': row['tab_order'],
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                }
                
                if tab_id not in sections_by_tab:
                    sections_by_tab[tab_id] = []
                
                sections_by_tab[tab_id].append(section)
            
            return sections_by_tab
            
        except Exception as e:
            logger.error(f"Error getting sections by tab for layout {layout_id}: {e}")
            return {}
