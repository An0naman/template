# template_app/app/services/dashboard_service.py
"""
Dashboard Service
Provides data aggregation and analysis for dashboard widgets
"""

import logging
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from flask import current_app
from app.db import get_connection

logger = logging.getLogger(__name__)


def _coerce_datetime(value):
    """Accept either ISO strings or native datetime objects from the DB layer."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value.replace('Z', '+00:00'))
    raise TypeError(f"Unsupported datetime value type: {type(value).__name__}")


def _serialize_datetime(value):
    """Return ISO string for JSON-friendly widget payloads."""
    dt = _coerce_datetime(value)
    return dt.isoformat() if dt else None

class DashboardService:
    """Service for aggregating dashboard data from various sources"""
    
    @staticmethod
    def get_db():
        """Get database connection"""
        return get_connection()

    @staticmethod
    def get_saved_search_entries(search_id: int, ignore_limit: bool = False) -> Dict[str, Any]:
        """
        Get entries matching a saved search
        
        Args:
            search_id: ID of the saved search
            ignore_limit: If True, return all matching entries regardless of result_limit setting
                         (useful for dashboard widgets that need complete data for aggregations)
            
        Returns:
            Dict with entries and metadata
        """
        try:
            conn = DashboardService.get_db()
            cursor = conn.cursor()
            
            # Get the saved search parameters
            cursor.execute("""
                SELECT * FROM SavedSearch WHERE id = ?
            """, (search_id,))
            
            search = cursor.fetchone()
            if not search:
                return {'error': 'Saved search not found', 'entries': []}
            
            # Check if this is a SQL mode search with custom SQL query
            use_sql_mode = 'use_sql_mode' in search.keys() and search['use_sql_mode']
            custom_sql_query = search['custom_sql_query'].strip() if 'custom_sql_query' in search.keys() and search['custom_sql_query'] else ''
            
            if use_sql_mode and custom_sql_query:
                # Execute custom SQL query to get entry IDs
                logger.info(f"Saved search {search_id} using custom SQL mode")
                try:
                    # Check if it's a full query or a WHERE clause fragment
                    if 'SELECT' in custom_sql_query.upper():
                        # Full query - execute as-is
                        cursor.execute(custom_sql_query)
                        id_rows = cursor.fetchall()
                        entry_ids = [row[0] if isinstance(row, tuple) else row['id'] for row in id_rows]
                    else:
                        # WHERE clause fragment - build query
                        id_query = f"""
                            SELECT DISTINCT e.id 
                            FROM Entry e
                            LEFT JOIN EntryType et ON e.entry_type_id = et.id
                            LEFT JOIN EntryRelationship er_from ON e.id = er_from.source_entry_id
                            LEFT JOIN EntryRelationship er_to ON e.id = er_to.target_entry_id
                            WHERE ({custom_sql_query})
                        """
                        cursor.execute(id_query)
                        id_rows = cursor.fetchall()
                        entry_ids = [row[0] for row in id_rows]
                    
                    logger.info(f"Custom SQL query returned {len(entry_ids)} entry IDs")
                    
                    if not entry_ids:
                        return {
                            'search_name': search['name'],
                            'entries': [],
                            'total_count': 0
                        }
                    
                    # Now fetch full entry details for these IDs
                    placeholders = ','.join(['?' for _ in entry_ids])
                    detail_query = f"""
                        SELECT e.*, et.singular_label as entry_type_label 
                        FROM Entry e 
                        JOIN EntryType et ON e.entry_type_id = et.id 
                        WHERE e.id IN ({placeholders})
                    """
                    
                    # Apply sorting
                    sort_by = search['sort_by'] or 'created_desc'
                    if sort_by == 'created_desc':
                        detail_query += " ORDER BY e.created_at DESC"
                    elif sort_by == 'created_asc':
                        detail_query += " ORDER BY e.created_at ASC"
                    elif sort_by == 'title_asc':
                        detail_query += " ORDER BY e.title ASC"
                    elif sort_by == 'title_desc':
                        detail_query += " ORDER BY e.title DESC"
                    
                    # Apply result limit (unless ignore_limit is True)
                    if not ignore_limit:
                        limit = int(search['result_limit'] or 50)
                        detail_query += f" LIMIT {limit}"
                    
                    cursor.execute(detail_query, entry_ids)
                    rows = cursor.fetchall()
                    
                except Exception as sql_error:
                    logger.error(f"Error executing custom SQL query: {sql_error}", exc_info=True)
                    return {'error': f'SQL query error: {str(sql_error)}', 'entries': []}
            else:
                # Standard filter-based search
                # Build the query based on search parameters
                query = "SELECT e.*, et.singular_label as entry_type_label FROM Entry e JOIN EntryType et ON e.entry_type_id = et.id WHERE 1=1"
                params = []
                
                # Apply filters
                if search['search_term']:
                    query += " AND (e.title LIKE ? OR e.description LIKE ?)"
                    search_term = f"%{search['search_term']}%"
                    params.extend([search_term, search_term])
                
                if search['type_filter']:
                    query += " AND e.entry_type_id = ?"
                    params.append(int(search['type_filter']))
                
                # Specific states filter (comma-separated list of states)
                # sqlite3.Row objects don't have .get(), check for key existence
                if 'specific_states' in search.keys() and search['specific_states']:
                    states = [s.strip() for s in search['specific_states'].split(',') if s.strip()]
                    if states:
                        # Use case-insensitive comparison for state names
                        state_conditions = ' OR '.join(['LOWER(e.status) = LOWER(?)' for _ in states])
                        query += f" AND ({state_conditions})"
                        params.extend(states)
                elif search['status_filter']:
                    # Only apply status_filter if specific_states is not set
                    # status_filter is a category (active/inactive), not a state name
                    # Need to join with EntryState to filter by category
                    query += " AND EXISTS (SELECT 1 FROM EntryState es WHERE es.entry_type_id = e.entry_type_id AND LOWER(es.name) = LOWER(e.status) AND es.category = ?)"
                    params.append(search['status_filter'])
                
                # Date range filter
                if search['date_range']:
                    now = datetime.now()
                    if search['date_range'] == 'today':
                        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
                        query += " AND e.created_at >= ?"
                        params.append(start_date.isoformat())
                    elif search['date_range'] == 'week':
                        start_date = now - timedelta(days=7)
                        query += " AND e.created_at >= ?"
                        params.append(start_date.isoformat())
                    elif search['date_range'] == 'month':
                        start_date = now - timedelta(days=30)
                        query += " AND e.created_at >= ?"
                        params.append(start_date.isoformat())
                
                # Sorting
                sort_by = search['sort_by'] or 'created_desc'
                if sort_by == 'created_desc':
                    query += " ORDER BY e.created_at DESC"
                elif sort_by == 'created_asc':
                    query += " ORDER BY e.created_at ASC"
                elif sort_by == 'title_asc':
                    query += " ORDER BY e.title ASC"
                elif sort_by == 'title_desc':
                    query += " ORDER BY e.title DESC"
                
                # Result limit (unless ignore_limit is True)
                if not ignore_limit:
                    limit = int(search['result_limit'] or 50)
                    query += f" LIMIT {limit}"
                
                # Debug logging
                logger.info(f"Saved search {search_id} query: {query}")
                logger.info(f"Saved search {search_id} params: {params}")
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
            
            entries = []
            for row in rows:
                entries.append({
                    'id': row['id'],
                    'title': row['title'],
                    'description': row['description'],
                    'status': row['status'],
                    'entry_type_label': row['entry_type_label'],
                    'created_at': row['created_at'],
                    'intended_end_date': row['intended_end_date'],
                    'actual_end_date': row['actual_end_date']
                })
            
            conn.close()
            
            return {
                'search_name': search['name'],
                'entries': entries,
                'total_count': len(entries)
            }
            
        except Exception as e:
            logger.error(f"Error getting saved search entries: {e}", exc_info=True)
            return {'error': str(e), 'entries': []}

    @staticmethod
    def get_timeline_distribution(search_id: int, date_field: str, grouping: str = 'month') -> Dict[str, Any]:
        """
        Get distribution of entries over time
        
        Args:
            search_id: Saved search to filter by
            date_field: Which date field to use ('created_date' or 'end_date')
            grouping: How to group dates ('day', 'week', 'month', 'quarter', 'year')
            
        Returns:
            Dict with timeline distribution data
        """
        try:
            conn = DashboardService.get_db()
            cursor = conn.cursor()
            
            # Get entries from saved search (ignore limit for accurate timeline data)
            search_data = DashboardService.get_saved_search_entries(search_id, ignore_limit=True)
            entries = search_data['entries']
            
            if not entries:
                return {'categories': [], 'total': 0, 'attribute': date_field, 'attribute_label': f'{date_field.replace("_", " ").title()} Timeline'}
            
            from datetime import datetime
            from collections import defaultdict
            
            timeline_data = defaultdict(int)
            
            # Choose the date field
            field_key = 'created_at' if date_field == 'created_date' else 'actual_end_date' if date_field == 'end_date' else 'created_at'
            
            for entry in entries:
                date_str = entry.get(field_key)
                if not date_str:
                    continue
                    
                try:
                    date_obj = datetime.fromisoformat(date_str.replace('+00:00', '').replace('Z', ''))
                    
                    # Group by the specified period
                    if grouping == 'day':
                        key = date_obj.strftime('%Y-%m-%d')
                    elif grouping == 'week':
                        # ISO week format
                        key = f"{date_obj.year}-W{date_obj.isocalendar()[1]:02d}"
                    elif grouping == 'month':
                        key = date_obj.strftime('%Y-%m')
                    elif grouping == 'quarter':
                        quarter = (date_obj.month - 1) // 3 + 1
                        key = f"{date_obj.year}-Q{quarter}"
                    elif grouping == 'year':
                        key = str(date_obj.year)
                    else:
                        key = date_obj.strftime('%Y-%m')
                    
                    timeline_data[key] += 1
                except:
                    pass
            
            # Sort the timeline data
            sorted_keys = sorted(timeline_data.keys())
            categories = []
            total = 0
            
            for key in sorted_keys:
                count = timeline_data[key]
                total += count
                categories.append({
                    'name': key,
                    'count': count,
                    'color': None  # Will be generated or use single color
                })
            
            conn.close()
            
            return {
                'categories': categories,
                'total': total,
                'attribute': date_field,
                'attribute_label': f'{date_field.replace("_", " ").title()} ({grouping.title()})',
                'is_timeline': True
            }
            
        except Exception as e:
            logger.error(f"Error getting timeline distribution: {e}", exc_info=True)
            return {'error': str(e), 'categories': [], 'total': 0}
    
    @staticmethod
    def get_attribute_distribution(search_id: int, attribute: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Get distribution of entries by a specific attribute
        
        Args:
            search_id: Saved search to filter by
            attribute: Attribute to aggregate by ('status', 'entry_type', 'date_timeline')
            config: Optional configuration (e.g., date_field and timeline_grouping for date_timeline)
            
        Returns:
            Dict with category distribution data
        """
        # Handle timeline-based attributes
        if attribute == 'date_timeline':
            date_field = config.get('date_field', 'created_date') if config else 'created_date'
            grouping = config.get('timeline_grouping', 'month') if config else 'month'
            return DashboardService.get_timeline_distribution(search_id, date_field, grouping)
        
        # Legacy support for old chart widgets with created_date or end_date attributes
        if attribute in ['created_date', 'end_date']:
            grouping = config.get('timeline_grouping', 'month') if config else 'month'
            return DashboardService.get_timeline_distribution(search_id, attribute, grouping)
        
        try:
            conn = DashboardService.get_db()
            cursor = conn.cursor()
            
            # Get entries from saved search (ignore limit for accurate timeline data)
            search_data = DashboardService.get_saved_search_entries(search_id, ignore_limit=True)
            entry_ids = [e['id'] for e in search_data['entries']]
            
            if not entry_ids:
                return {'categories': [], 'total': 0, 'attribute': date_field, 'attribute_label': f'{date_field.replace("_", " ").title()} Timeline'}
            
            placeholders = ','.join(['?' for _ in entry_ids])
            
            # Build query based on attribute
            if attribute == 'status':
                query = f"""
                    SELECT e.status, es.name, es.color, COUNT(*) as count
                    FROM Entry e
                    LEFT JOIN EntryState es ON e.status = es.name AND e.entry_type_id = es.entry_type_id
                    WHERE e.id IN ({placeholders})
                    GROUP BY e.status, es.name, es.color
                    ORDER BY count DESC
                """
                cursor.execute(query, entry_ids)
                rows = cursor.fetchall()
                
                categories = []
                total = 0
                for row in rows:
                    count = row['count']
                    total += count
                    categories.append({
                        'name': row['name'] or row['status'] or 'Unknown',
                        'count': count,
                        'color': row['color'] or '#6c757d'
                    })
                    
            elif attribute == 'entry_type':
                query = f"""
                    SELECT et.singular_label as name, COUNT(*) as count
                    FROM Entry e
                    JOIN EntryType et ON e.entry_type_id = et.id
                    WHERE e.id IN ({placeholders})
                    GROUP BY et.id, et.singular_label
                    ORDER BY count DESC
                """
                cursor.execute(query, entry_ids)
                rows = cursor.fetchall()
                
                categories = []
                total = 0
                for row in rows:
                    count = row['count']
                    total += count
                    categories.append({
                        'name': row['name'] or 'Unknown',
                        'count': count,
                        'color': None  # Will be generated by frontend
                    })

            elif attribute == 'custom_column':
                custom_column_id = config.get('custom_column_id') if config else None
                if not custom_column_id:
                    conn.close()
                    return {'error': 'No custom column selected', 'categories': [], 'total': 0}

                # Fetch column label for axis label
                cursor.execute('SELECT label FROM CustomColumn WHERE id = ?', (custom_column_id,))
                col_row = cursor.fetchone()
                col_label = col_row['label'] if col_row else 'Custom Column'

                # Count occurrences of each distinct value across the entry set
                cursor.execute(
                    f'SELECT value, COUNT(*) as count FROM CustomColumnValue '
                    f'WHERE entry_id IN ({placeholders}) AND custom_column_id = ? AND value IS NOT NULL AND value != "" '
                    f'GROUP BY value ORDER BY count DESC',
                    entry_ids + [custom_column_id]
                )
                rows = cursor.fetchall()

                palette = ['#4bc0c0','#ff6384','#36a2eb','#ffce56','#9966ff','#ff9f40','#c9cbcf']
                categories = []
                total = 0
                for i, row in enumerate(rows):
                    count = row['count']
                    total += count
                    categories.append({
                        'name': row['value'],
                        'count': count,
                        'color': palette[i % len(palette)]
                    })

                conn.close()
                return {
                    'categories': categories,
                    'total': total,
                    'attribute': attribute,
                    'attribute_label': col_label
                }
            else:
                conn.close()
                return {'error': f'Unsupported attribute: {attribute}', 'categories': [], 'total': 0}
            
            conn.close()
            
            return {
                'categories': categories,
                'total': total,
                'attribute': attribute,
                'attribute_label': attribute.replace('_', ' ').title()
            }
            
        except Exception as e:
            logger.error(f"Error getting attribute distribution: {e}", exc_info=True)
            return {'error': str(e), 'categories': [], 'total': 0}

    @staticmethod
    def get_state_distribution(search_id: Optional[int] = None, entry_type_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get distribution of entry states (legacy method for backward compatibility)
        
        Args:
            search_id: Optional saved search to filter by
            entry_type_id: Optional entry type to filter by
            
        Returns:
            Dict with state distribution data
        """
        try:
            conn = DashboardService.get_db()
            cursor = conn.cursor()
            
            # Build query
            if search_id:
                # Get entries from saved search, then aggregate states (ignore limit for accurate distribution)
                search_data = DashboardService.get_saved_search_entries(search_id, ignore_limit=True)
                entry_ids = [e['id'] for e in search_data['entries']]
                
                if not entry_ids:
                    return {'states': [], 'total': 0}
                
                placeholders = ','.join(['?' for _ in entry_ids])
                query = f"""
                    SELECT e.status, es.name, es.color, COUNT(*) as count
                    FROM Entry e
                    LEFT JOIN EntryState es ON e.status = es.name AND e.entry_type_id = es.entry_type_id
                    WHERE e.id IN ({placeholders})
                    GROUP BY e.status, es.name, es.color
                    ORDER BY count DESC
                """
                cursor.execute(query, entry_ids)
            elif entry_type_id:
                query = """
                    SELECT e.status, es.name, es.color, COUNT(*) as count
                    FROM Entry e
                    LEFT JOIN EntryState es ON e.status = es.name AND e.entry_type_id = es.entry_type_id
                    WHERE e.entry_type_id = ?
                    GROUP BY e.status, es.name, es.color
                    ORDER BY count DESC
                """
                cursor.execute(query, (entry_type_id,))
            else:
                query = """
                    SELECT e.status, es.name, es.color, COUNT(*) as count
                    FROM Entry e
                    LEFT JOIN EntryState es ON e.status = es.name AND e.entry_type_id = es.entry_type_id
                    GROUP BY e.status, es.name, es.color
                    ORDER BY count DESC
                """
                cursor.execute(query)
            
            rows = cursor.fetchall()
            
            states = []
            total = 0
            for row in rows:
                count = row['count']
                total += count
                states.append({
                    'name': row['name'] or row['status'] or 'Unknown',
                    'count': count,
                    'color': row['color'] or '#6c757d'
                })
            
            conn.close()
            
            return {
                'states': states,
                'total': total
            }
            
        except Exception as e:
            logger.error(f"Error getting state distribution: {e}", exc_info=True)
            return {'error': str(e), 'states': [], 'total': 0}

    @staticmethod
    def get_sensor_data_trends(entry_ids: List[int], sensor_type: str, time_range: str = '7d') -> Dict[str, Any]:
        """
        Get sensor data trends for specified entries
        
        Args:
            entry_ids: List of entry IDs to get sensor data for
            sensor_type: Type of sensor to retrieve
            time_range: Time range (1d, 7d, 30d, 90d, all)
            
        Returns:
            Dict with sensor data time series
        """
        try:
            conn = DashboardService.get_db()
            cursor = conn.cursor()
            
            if not entry_ids:
                return {'data_points': [], 'sensor_type': sensor_type}
            
            # Calculate time filter
            now = datetime.now(timezone.utc)
            time_filter = None
            
            if time_range == '1d':
                time_filter = (now - timedelta(days=1)).isoformat()
            elif time_range == '7d':
                time_filter = (now - timedelta(days=7)).isoformat()
            elif time_range == '30d':
                time_filter = (now - timedelta(days=30)).isoformat()
            elif time_range == '90d':
                time_filter = (now - timedelta(days=90)).isoformat()
            
            # Query sensor data (supporting both legacy and shared sensor data)
            placeholders = ','.join(['?' for _ in entry_ids])
            rows = []
            
            # Try SensorDataEntryRanges first (for range-based sensor data)
            query = f"""
                SELECT ssd.sensor_type, ssd.value, ssd.recorded_at, sder.entry_id
                FROM SharedSensorData ssd
                JOIN SensorDataEntryRanges sder ON 
                    ssd.sensor_type = sder.sensor_type 
                    AND ssd.id BETWEEN sder.start_sensor_id AND sder.end_sensor_id
                WHERE sder.entry_id IN ({placeholders})
                AND ssd.sensor_type = ?
            """
            params = entry_ids + [sensor_type]
            
            if time_filter:
                query += " AND ssd.recorded_at >= ?"
                params.append(time_filter)
            
            query += " ORDER BY ssd.recorded_at ASC"
            
            logger.info(f"Sensor data query (ranges) for entries {entry_ids}, sensor {sensor_type}: {query}")
            logger.info(f"Sensor data params: {params}")
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            logger.info(f"Sensor data ranges returned {len(rows)} rows")
            
            # If no range data, try direct links (SensorDataEntryLinks)
            if not rows:
                query = f"""
                    SELECT ssd.sensor_type, ssd.value, ssd.recorded_at, sdel.entry_id
                    FROM SharedSensorData ssd
                    JOIN SensorDataEntryLinks sdel ON ssd.id = sdel.shared_sensor_data_id
                    WHERE sdel.entry_id IN ({placeholders})
                    AND ssd.sensor_type = ?
                """
                params = entry_ids + [sensor_type]
                
                if time_filter:
                    query += " AND ssd.recorded_at >= ?"
                    params.append(time_filter)
                
                query += " ORDER BY ssd.recorded_at ASC"
                
                logger.info(f"Sensor data query (links): {query}")
                cursor.execute(query, params)
                rows = cursor.fetchall()
                logger.info(f"Sensor data links returned {len(rows)} rows")
            
            # If no shared data, try legacy sensor data
            if not rows:
                query = f"""
                    SELECT sensor_type, value, recorded_at, entry_id
                    FROM SensorData
                    WHERE entry_id IN ({placeholders})
                    AND sensor_type = ?
                """
                params = entry_ids + [sensor_type]
                
                if time_filter:
                    query += " AND recorded_at >= ?"
                    params.append(time_filter)
                
                query += " ORDER BY recorded_at ASC"
                
                logger.info(f"Sensor data query (legacy): {query}")
                cursor.execute(query, params)
                rows = cursor.fetchall()
                logger.info(f"Sensor data legacy returned {len(rows)} rows")
            
            data_points = []
            for row in rows:
                try:
                    # Try to extract numeric value
                    value_str = row['value']
                    # Remove common units
                    import re
                    numeric_value = re.sub(r'[^\d.-]', '', value_str)
                    if numeric_value:
                        numeric_value = float(numeric_value)
                    else:
                        numeric_value = None
                    
                    data_points.append({
                        'timestamp': row['recorded_at'],
                        'value': numeric_value,
                        'value_str': value_str,
                        'entry_id': row['entry_id']
                    })
                except (ValueError, TypeError):
                    # Skip non-numeric values
                    pass
            
            conn.close()
            
            return {
                'data_points': data_points,
                'sensor_type': sensor_type,
                'count': len(data_points)
            }
            
        except Exception as e:
            logger.error(f"Error getting sensor data trends: {e}", exc_info=True)
            return {'error': str(e), 'data_points': [], 'sensor_type': sensor_type}

    @staticmethod
    def generate_ai_summary(search_id: int, widget_config: Dict[str, Any] = None, widget_id: int = None, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Generate AI summary for a saved search (with daily caching)
        
        Args:
            search_id: ID of the saved search
            widget_config: Optional widget configuration containing custom_prompt
            widget_id: Widget ID for caching purposes
            force_refresh: If True, bypass cache and regenerate
            
        Returns:
            Dict with AI-generated summary
        """
        try:
            from app.services.ai_service import get_ai_service
            from datetime import date
            import hashlib
            
            ai_service = get_ai_service()
            if not ai_service.is_available():
                return {
                    'summary': 'AI service is not configured. Please configure Gemini API key in system settings.',
                    'available': False
                }
            
            # Check for force refresh in config
            if widget_config and widget_config.get('_force_refresh'):
                force_refresh = True
                widget_config = {k: v for k, v in widget_config.items() if k != '_force_refresh'}
            
            # Generate config hash to detect changes
            config_str = json.dumps(widget_config or {}, sort_keys=True)
            config_hash = hashlib.md5(config_str.encode()).hexdigest()
            today = date.today().isoformat()
            
            # Check cache if we have a widget_id and not forcing refresh
            if widget_id and not force_refresh:
                conn = DashboardService.get_db()
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT summary_text, config_hash
                    FROM AISummaryCache
                    WHERE widget_id = ? AND generated_date = ?
                    ORDER BY created_at DESC
                    LIMIT 1
                """, (widget_id, today))
                
                cached = cursor.fetchone()
                if cached and cached['config_hash'] == config_hash:
                    logger.info(f"Widget ID {widget_id} - Using cached AI summary from {today}")
                    conn.close()
                    return {
                        'summary': cached['summary_text'],
                        'available': True,
                        'cached': True,
                        'generated_date': today
                    }
                
                conn.close()
            
            # Get entries from saved search (ignore limit for comprehensive AI summary)
            search_data = DashboardService.get_saved_search_entries(search_id, ignore_limit=True)
            entries = search_data.get('entries', [])
            
            if not entries:
                return {
                    'summary': 'No entries found for this search.',
                    'available': True
                }
            
            # Get state distribution
            state_data = DashboardService.get_state_distribution(search_id)
            
            # Collect sensor data summary
            conn = DashboardService.get_db()
            cursor = conn.cursor()
            
            entry_ids = [e['id'] for e in entries]
            placeholders = ','.join(['?' for _ in entry_ids])
            
            # Get recent sensor data from the current SensorData table
            cursor.execute(f"""
                SELECT sensor_type, value, recorded_at, entry_id
                FROM SensorData
                WHERE entry_id IN ({placeholders})
                ORDER BY recorded_at DESC
                LIMIT 100
            """, entry_ids)
            
            sensor_rows = cursor.fetchall()
            sensor_summary = {}
            for row in sensor_rows:
                sensor_type = row['sensor_type']
                if sensor_type not in sensor_summary:
                    sensor_summary[sensor_type] = []
                sensor_summary[sensor_type].append({
                    'value': row['value'],
                    'recorded_at': row['recorded_at']
                })
            
            # Get recent notes
            cursor.execute(f"""
                SELECT note_text, type, created_at, entry_id
                FROM Note
                WHERE entry_id IN ({placeholders})
                ORDER BY created_at DESC
                LIMIT 20
            """, entry_ids)
            
            note_rows = cursor.fetchall()
            notes_summary = [{'text': row['note_text'][:200], 'type': row['type']} for row in note_rows]
            
            conn.close()
            
            # Calculate time-based insights
            from datetime import datetime
            now = datetime.now()
            entry_ages = []
            for entry in entries:
                try:
                    created = datetime.fromisoformat(entry['created_at'].replace('+00:00', ''))
                    age_days = (now - created).days
                    entry_ages.append({'title': entry['title'], 'age_days': age_days, 'status': entry['status']})
                except:
                    pass
            
            # Analyze sensor data for trends
            def extract_numeric_value(value_str):
                """Extract numeric value from sensor data, stripping units"""
                if not value_str:
                    return None
                import re
                # Extract first number (int or float) from the string
                match = re.search(r'-?\d+\.?\d*', str(value_str))
                if match:
                    try:
                        return float(match.group())
                    except:
                        return None
                return None
            
            sensor_insights = {}
            for sensor_type, readings in sensor_summary.items():
                if readings:
                    # Extract numeric values, filtering out non-numeric data
                    values = []
                    for r in readings:
                        val = extract_numeric_value(r['value'])
                        if val is not None:
                            values.append(val)
                    
                    if values:
                        sensor_insights[sensor_type] = {
                            'avg': round(sum(values) / len(values), 2),
                            'min': round(min(values), 2),
                            'max': round(max(values), 2),
                            'count': len(values),
                            'unit': sensor_type  # Can enhance this to extract actual unit
                        }
            
            # Build context for AI
            context = {
                'search_name': search_data.get('search_name', 'Unknown'),
                'total_entries': len(entries),
                'entries_sample': entries[:10],  # First 10 entries
                'state_distribution': state_data.get('states', []),
                'sensor_types': list(sensor_summary.keys()),
                'sensor_insights': sensor_insights,
                'entry_ages': sorted(entry_ages, key=lambda x: x['age_days'], reverse=True)[:10],
                'recent_notes': notes_summary
            }
            
            # Prepare formatted data for prompt
            age_data = [{'title': e['title'], 'status': e['status'], 'age_days': e['age_days']} 
                       for e in context['entry_ages'][:10]] if context['entry_ages'] else []
            
            entry_samples = [{'title': e['title'], 'status': e['status'], 'description': e.get('description', '')[:100]} 
                           for e in context['entries_sample'][:5]]
            
            note_samples = [{'type': n['type'], 'preview': n['text'][:100]} 
                          for n in context['recent_notes'][:5]] if context['recent_notes'] else []
            
            # Get configurable prompt from database
            from app.db import get_system_parameters
            params = get_system_parameters()
            prompt_template = params.get('prompt_summary', 
                'You are analyzing a project management dashboard. Provide an insightful, actionable summary.\n\n'
                '**Dataset Overview:**\n- Collection: "{search_name}"\n- Total Items: {total_entries}\n'
                '- Entry Type: {entry_type}\n\n**Current State Breakdown:**\n{state_distribution}\n\n'
                '**Age Analysis (Top 10 Oldest):**\n{age_data}\n\n**Recent Entries (Sample):**\n{entry_samples}\n\n'
                '**Sensor Monitoring:**\n{sensor_insights}\n\n**Recent Activity Notes:**\n{note_samples}\n\n'
                '**Please provide a well-structured summary with:**\n\n1. **📊 Overview & Status**\n'
                '2. **⏱️ Timeline Insights**\n3. **🔬 Sensor Analysis**\n4. **⚠️ Action Items**\n'
                '5. **✅ Progress Highlights**\n\nFormat using markdown with emojis for readability.')
            
            # Format the prompt with actual data
            prompt = prompt_template.format(
                search_name=context['search_name'],
                total_entries=context['total_entries'],
                entry_type=entries[0]['entry_type_label'] if entries else 'Unknown',
                state_distribution=json.dumps(context['state_distribution'], indent=2),
                age_data=json.dumps(age_data, indent=2) if age_data else 'No age data',
                entry_samples=json.dumps(entry_samples, indent=2),
                sensor_insights=json.dumps(context['sensor_insights'], indent=2) if context['sensor_insights'] else 'No sensor data available',
                note_samples=json.dumps(note_samples, indent=2) if note_samples else 'No recent notes'
            )
            
            # Amalgamate widget-specific custom prompt if provided
            if widget_config and widget_config.get('custom_prompt'):
                custom_prompt = widget_config['custom_prompt'].strip()
                # Get base prompt for additional context
                base_prompt = params.get('gemini_base_prompt', 
                    'You are a helpful assistant for a project management application.')
                
                # Combine: base context + main prompt + custom instructions
                prompt = f"""{base_prompt}

{prompt}

**Additional Widget-Specific Instructions:**
{custom_prompt}

Please incorporate these specific instructions into your analysis and summary."""

            # Use the model's generate_content method
            logger.info(f"Widget ID {widget_id} - Generating new AI summary for {today}")
            response = ai_service.model.generate_content(prompt)
            summary = response.text.strip() if response and response.text else "Unable to generate summary"
            
            # Cache the summary if we have a widget_id
            if widget_id:
                try:
                    conn = DashboardService.get_db()
                    cursor = conn.cursor()
                    
                    # Delete old cache entries for this widget (keep only today's)
                    cursor.execute("""
                        DELETE FROM AISummaryCache
                        WHERE widget_id = ? AND generated_date != ?
                    """, (widget_id, today))
                    
                    # Insert new cache entry
                    cursor.execute("""
                        INSERT OR REPLACE INTO AISummaryCache
                        (widget_id, search_id, summary_text, generated_date, config_hash)
                        VALUES (?, ?, ?, ?, ?)
                    """, (widget_id, search_id, summary, today, config_hash))
                    
                    conn.commit()
                    conn.close()
                    logger.info(f"Widget ID {widget_id} - Cached AI summary for {today}")
                except Exception as cache_error:
                    logger.error(f"Error caching AI summary: {cache_error}")
            
            return {
                'summary': summary,
                'available': True,
                'cached': False,
                'generated_date': today,
                'context': {
                    'total_entries': context['total_entries'],
                    'states': len(context['state_distribution'])
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating AI summary: {e}", exc_info=True)
            return {
                'summary': f'Error generating summary: {str(e)}',
                'available': False,
                'error': str(e)
            }
    
    @staticmethod
    def get_git_commits(repo_id: int, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get commits from a Git repository
        
        Args:
            repo_id: ID of the Git repository
            config: Widget configuration with commit_limit
            
        Returns:
            Dict with commits list
        """
        try:
            from app.db import get_connection
            conn = get_connection()
            cursor = conn.cursor()
            
            limit = config.get('commit_limit', 10)
            
            # Always sync on page load to get latest commits from remote
            logger.info(f"Syncing latest commits for repo {repo_id}")
            try:
                from app.services.git_service import get_git_service
                
                # Get git token from system parameters
                cursor.execute('''
                    SELECT parameter_value 
                    FROM SystemParameters 
                    WHERE parameter_name = 'git_token'
                ''')
                token_row = cursor.fetchone()
                git_token = token_row['parameter_value'] if token_row else None
                
                if not git_token:
                    logger.warning("No git_token found in system parameters")
                    return {
                        'success': False,
                        'error': 'Repository not synced. Please configure Git token in System Parameters.',
                        'commits': []
                    }
                
                git_service = get_git_service()
                
                # Clone/update repository first (pulls latest from remote)
                try:
                    git_service.clone_or_open_repository(repo_id, token=git_token)
                except Exception as clone_error:
                    logger.error(f"Failed to clone/open repository: {clone_error}")
                    return {
                        'success': False,
                        'error': f'Failed to access repository: {str(clone_error)}',
                        'commits': []
                    }
                
                # Now sync commits to database
                try:
                    sync_result = git_service.sync_commits(repo_id, limit=max(limit, 100))
                    logger.info(f"Sync completed: {sync_result}")
                except Exception as sync_inner_error:
                    logger.warning(f"Sync failed for repo {repo_id}: {sync_inner_error}, continuing with existing data")
            except Exception as sync_error:
                logger.warning(f"Failed to access repository for repo {repo_id}: {sync_error}, continuing with existing data")
            
            # Get commits for this repository with entry association info and repo settings
            cursor.execute('''
                SELECT c.*, r.name as repo_name, r.entry_type_id as default_entry_type_id,
                       r.allowed_statuses as repo_allowed_statuses,
                       e.id as entry_id, e.title as entry_title, et.singular_label as entry_type_label
                FROM GitCommit c
                JOIN GitRepository r ON c.repository_id = r.id
                LEFT JOIN Entry e ON c.entry_id = e.id
                LEFT JOIN EntryType et ON e.entry_type_id = et.id
                WHERE c.repository_id = ?
                ORDER BY c.commit_date DESC
                LIMIT ?
            ''', (repo_id, limit))
            
            commits = []
            for row in cursor.fetchall():
                commit_data = {
                    'id': row['id'],
                    'commit_hash': row['commit_hash'],
                    'author': row['author'],
                    'message': row['message'],
                    'commit_date': _serialize_datetime(row['commit_date']),
                    'branch': row['branch'],
                    'default_entry_type_id': row['default_entry_type_id'],
                    'repo_allowed_statuses': row['repo_allowed_statuses']
                }
                
                # Add entry association info if linked
                if row['entry_id']:
                    commit_data['entry'] = {
                        'id': row['entry_id'],
                        'title': row['entry_title'],
                        'type_label': row['entry_type_label']
                    }
                else:
                    commit_data['entry'] = None
                
                commits.append(commit_data)
            
            return {
                'success': True,
                'commits': commits,
                'total': len(commits)
            }
            
        except Exception as e:
            logger.error(f"Error getting git commits for repo {repo_id}: {e}")
            return {'error': str(e)}
    
    @staticmethod
    def get_git_commits_timeline(repo_id: int, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get commit timeline data for a Git repository
        
        Args:
            repo_id: ID of the Git repository
            config: Widget configuration with grouping and time_range
            
        Returns:
            Dict with timeline data
        """
        try:
            conn = DashboardService.get_db()
            cursor = conn.cursor()
            
            # Get repository info
            cursor.execute('SELECT name FROM GitRepository WHERE id = ?', (repo_id,))
            repo_row = cursor.fetchone()
            if not repo_row:
                return {'error': 'Repository not found'}
            
            repo_name = repo_row['name']
            
            # Always sync on page load to get latest commits from remote
            logger.info(f"Syncing latest commits for chart widget, repo {repo_id}")
            try:
                from app.services.git_service import get_git_service
                
                # Get git token from system parameters
                cursor.execute('''
                    SELECT parameter_value 
                    FROM SystemParameters 
                    WHERE parameter_name = 'git_token'
                ''')
                token_row = cursor.fetchone()
                git_token = token_row['parameter_value'] if token_row else None
                
                if git_token:
                    git_service = get_git_service()
                    
                    # Clone/update repository (pulls latest from remote)
                    try:
                        git_service.clone_or_open_repository(repo_id, token=git_token)
                        # Sync commits to database
                        sync_result = git_service.sync_commits(repo_id, limit=100)
                        logger.info(f"Chart widget sync completed: {sync_result}")
                    except Exception as sync_error:
                        logger.warning(f"Chart widget sync failed for repo {repo_id}: {sync_error}")
                        # Continue anyway with existing data
                else:
                    logger.warning("No git_token found, using existing commit data")
            except Exception as e:
                logger.warning(f"Chart widget sync error: {e}, using existing data")
            
            # Get configuration
            grouping = config.get('grouping', 'week')  # day, week, month
            time_range = config.get('time_range', 30)  # days to look back
            
            # Calculate the date threshold
            from datetime import datetime, timedelta
            threshold_date = datetime.now() - timedelta(days=time_range)
            threshold_str = threshold_date.strftime('%Y-%m-%d %H:%M:%S')
            
            # Get commits within the time range
            cursor.execute('''
                SELECT commit_date
                FROM GitCommit
                WHERE repository_id = ? AND commit_date >= ?
                ORDER BY commit_date ASC
            ''', (repo_id, threshold_str))
            
            commits = cursor.fetchall()
            
            if not commits:
                return {
                    'success': True,
                    'repository_name': repo_name,
                    'timeline': [],
                    'grouping': grouping,
                    'time_range': time_range
                }
            
            # Group commits by time period
            from collections import defaultdict
            timeline_data = defaultdict(int)
            
            for row in commits:
                commit_date = _coerce_datetime(row['commit_date'])
                
                if grouping == 'day':
                    period_key = commit_date.strftime('%Y-%m-%d')
                    period_label = commit_date.strftime('%b %d')
                elif grouping == 'week':
                    # Get the Monday of the week
                    week_start = commit_date - timedelta(days=commit_date.weekday())
                    period_key = week_start.strftime('%Y-%m-%d')
                    period_label = week_start.strftime('%b %d')
                elif grouping == 'month':
                    period_key = commit_date.strftime('%Y-%m')
                    period_label = commit_date.strftime('%b %Y')
                else:
                    period_key = commit_date.strftime('%Y-%m-%d')
                    period_label = commit_date.strftime('%b %d')
                
                timeline_data[period_key] = timeline_data[period_key] + 1
            
            # Convert to list and sort
            timeline = []
            for period_key in sorted(timeline_data.keys()):
                # Recreate the label from the key
                if grouping == 'day':
                    dt = datetime.strptime(period_key, '%Y-%m-%d')
                    period_label = dt.strftime('%b %d')
                elif grouping == 'week':
                    dt = datetime.strptime(period_key, '%Y-%m-%d')
                    period_label = dt.strftime('%b %d')
                elif grouping == 'month':
                    dt = datetime.strptime(period_key, '%Y-%m')
                    period_label = dt.strftime('%b %Y')
                else:
                    dt = datetime.strptime(period_key, '%Y-%m-%d')
                    period_label = dt.strftime('%b %d')
                
                timeline.append({
                    'period': period_label,
                    'period_key': period_key,
                    'count': timeline_data[period_key]
                })
            
            return {
                'success': True,
                'repository_name': repo_name,
                'timeline': timeline,
                'total_commits': sum(timeline_data.values()),
                'grouping': grouping,
                'time_range': time_range
            }
            
        except Exception as e:
            logger.error(f"Error getting git commits timeline for repo {repo_id}: {e}")
            return {'error': str(e)}

    @staticmethod
    def get_entry_data_trends(
        metric_ids: List[int],
        entry_ids: List[int],
        time_range: str = '30d',
        x_axis_type: str = 'recorded_at',
        x_axis_field: str = 'commenced_at',
    ) -> Dict[str, Any]:
        """
        Return multi-series chart data from EntryDataPoint for the given metrics
        and entry scope.  Response shape matches the /api/entry-metrics/chart-data
        endpoint so the same JS renderer handles both.
        """
        try:
            conn = DashboardService.get_db()
            cursor = conn.cursor()

            if not metric_ids:
                return {'series': [], 'x_axis_type': x_axis_type, 'x_axis_label': 'Time'}

            ph_m = ','.join('?' * len(metric_ids))
            cursor.execute(
                f'SELECT * FROM EntryMetric WHERE id IN ({ph_m}) ORDER BY display_order ASC, label ASC',
                metric_ids,
            )
            metrics = {r['id']: r for r in cursor.fetchall()}

            # If no explicit entry scope, use all entries with data for these metrics
            if not entry_ids:
                cursor.execute(
                    f'SELECT DISTINCT entry_id FROM EntryDataPoint WHERE metric_id IN ({ph_m})',
                    metric_ids,
                )
                entry_ids = [r['entry_id'] for r in cursor.fetchall()]

            if not entry_ids:
                return {'series': [], 'x_axis_type': x_axis_type, 'x_axis_label': 'Time'}

            ph_e = ','.join('?' * len(entry_ids))

            # Time filter (only for recorded_at mode)
            tf = None
            if x_axis_type == 'recorded_at' and time_range != 'all':
                days_map = {'1d': 1, '7d': 7, '30d': 30, '90d': 90, '365d': 365}
                days = days_map.get(time_range)
                if days:
                    tf = (datetime.now(timezone.utc) - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')

            VALID_FIELDS = {'commenced_at', 'created_at', 'intended_end_date', 'actual_end_date'}

            series = []
            for mid in metric_ids:
                metric = metrics.get(mid)
                if not metric:
                    continue

                if x_axis_type == 'recorded_at':
                    q = f'''
                        SELECT edp.entry_id, edp.value, edp.recorded_at, edp.notes,
                               e.title AS entry_title
                        FROM EntryDataPoint edp
                        JOIN Entry e ON e.id = edp.entry_id
                        WHERE edp.metric_id = ? AND edp.entry_id IN ({ph_e})
                    '''
                    params = [mid] + entry_ids
                    if tf:
                        q += ' AND edp.recorded_at >= ?'
                        params.append(tf)
                    q += ' ORDER BY edp.recorded_at ASC'
                    cursor.execute(q, params)
                    rows = cursor.fetchall()
                    data_points = [
                        {'x': r['recorded_at'], 'y': r['value'],
                         'entry_id': r['entry_id'], 'entry_title': r['entry_title'],
                         'notes': r['notes']}
                        for r in rows
                    ]

                elif x_axis_type == 'entry_field' and x_axis_field in VALID_FIELDS:
                    q = f'''
                        SELECT edp.entry_id, AVG(edp.value) AS value,
                               e.{x_axis_field} AS x_value,
                               e.title AS entry_title
                        FROM EntryDataPoint edp
                        JOIN Entry e ON e.id = edp.entry_id
                        WHERE edp.metric_id = ? AND edp.entry_id IN ({ph_e})
                          AND e.{x_axis_field} IS NOT NULL
                        GROUP BY edp.entry_id
                        ORDER BY e.{x_axis_field} ASC
                    '''
                    cursor.execute(q, [mid] + entry_ids)
                    rows = cursor.fetchall()
                    data_points = [
                        {'x': r['x_value'], 'y': round(r['value'], 4),
                         'entry_id': r['entry_id'], 'entry_title': r['entry_title'],
                         'notes': None}
                        for r in rows
                    ]
                else:
                    data_points = []

                unit = metric['unit'] or ''
                series.append({
                    'metric_id': mid,
                    'label': metric['label'] + (f' ({unit})' if unit else ''),
                    'unit': unit,
                    'color': metric['color'] or '#4bc0c0',
                    'data_points': data_points,
                })

            x_label_map = {
                'recorded_at': 'Time',
                'entry_field': {
                    'commenced_at': 'Start Date',
                    'created_at': 'Created Date',
                    'intended_end_date': 'Intended End Date',
                    'actual_end_date': 'Actual End Date',
                }.get(x_axis_field, 'Date'),
            }

            return {
                'series': series,
                'x_axis_type': x_axis_type,
                'x_axis_label': x_label_map.get(x_axis_type, 'X'),
            }

        except Exception as e:
            logger.error(f"Error getting entry data trends: {e}", exc_info=True)
            return {'error': str(e), 'series': []}

    @staticmethod
    def get_widget_data(widget: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get data for a specific widget based on its configuration
        
        Args:
            widget: Widget configuration dict or sqlite3.Row object
            
        Returns:
            Dict with widget data
        """
        # Handle both dict and sqlite3.Row objects
        widget_type = widget['widget_type']
        data_source_type = widget['data_source_type']
        data_source_id = widget['data_source_id']
        config = json.loads(widget['config'] if widget['config'] else '{}')
        
        try:
            if widget_type == 'list' and data_source_type == 'saved_search':
                result = DashboardService.get_saved_search_entries(data_source_id)
                logger.info(f"Widget ID {widget.get('id')} - Saved search {data_source_id} returned: {len(result.get('entries', []))} entries")
                logger.info(f"Widget ID {widget.get('id')} - Full result keys: {result.keys()}")
                if result.get('entries'):
                    logger.info(f"Widget ID {widget.get('id')} - First entry sample: {result['entries'][0]}")
                return result
            
            elif widget_type == 'chart':
                # New flexible chart widget type
                if data_source_type == 'saved_search' and data_source_id:
                    chart_attribute = config.get('chart_attribute', 'status')
                    result = DashboardService.get_attribute_distribution(data_source_id, chart_attribute, config)
                    logger.info(f"Widget ID {widget.get('id')} - Chart returned {len(result.get('categories', []))} categories for attribute '{chart_attribute}'")
                    return result
                else:
                    return {'error': 'Invalid chart configuration - saved search required'}
            
            elif widget_type == 'pie_chart':
                # Legacy support for pie_chart widget type
                if data_source_type == 'entry_states':
                    if data_source_id:
                        return DashboardService.get_state_distribution(search_id=data_source_id)
                    else:
                        entry_type_id = config.get('entry_type_id')
                        return DashboardService.get_state_distribution(entry_type_id=entry_type_id)
                elif data_source_type == 'saved_search' and data_source_id:
                    # Support pie chart from saved search - show state distribution of those entries
                    return DashboardService.get_state_distribution(search_id=data_source_id)
                else:
                    return {'error': 'Invalid pie chart configuration'}
            
            elif widget_type == 'line_chart' and data_source_type == 'sensor_data':
                sensor_type = config.get('sensor_type')
                time_range = config.get('time_range', '7d')
                
                # Validate sensor_type is configured
                if not sensor_type:
                    logger.error(f"Widget ID {widget.get('id')} - Line chart missing sensor_type in config")
                    return {'error': 'Sensor type not configured', 'data_points': [], 'sensor_type': 'Unknown'}
                
                # Get entry IDs from saved search if specified (ignore limit for complete sensor data)
                if data_source_id:
                    search_data = DashboardService.get_saved_search_entries(data_source_id, ignore_limit=True)
                    if 'error' in search_data:
                        logger.error(f"Widget ID {widget.get('id')} - Error loading saved search {data_source_id}: {search_data['error']}")
                        return {'error': f"Saved search not found (ID: {data_source_id})", 'data_points': [], 'sensor_type': sensor_type}
                    entry_ids = [e['id'] for e in search_data.get('entries', [])]
                    logger.info(f"Widget ID {widget.get('id')} - Line chart will query {len(entry_ids)} entries for sensor type '{sensor_type}'")
                else:
                    entry_ids = config.get('entry_ids', [])
                    logger.info(f"Widget ID {widget.get('id')} - Line chart using {len(entry_ids)} entry IDs from config")
                
                result = DashboardService.get_sensor_data_trends(entry_ids, sensor_type, time_range)
                logger.info(f"Widget ID {widget.get('id')} - Sensor data returned {result.get('count', 0)} data points")
                return result
            
            elif widget_type == 'ai_summary' and data_source_type == 'saved_search':
                widget_id = widget.get('id')
                logger.info(f"Widget ID {widget_id} - Generating AI summary for search {data_source_id}")
                result = DashboardService.generate_ai_summary(data_source_id, config, widget_id=widget_id)
                logger.info(f"Widget ID {widget_id} - AI summary result: available={result.get('available')}, cached={result.get('cached')}, has_summary={bool(result.get('summary'))}, error={result.get('error')}")
                return result
            
            elif widget_type == 'stat_card':
                if data_source_type == 'saved_search':
                    search_data = DashboardService.get_saved_search_entries(data_source_id, ignore_limit=True)
                    return {
                        'value': search_data.get('total_count', 0),
                        'label': config.get('label', 'Total Entries')
                    }
                elif data_source_type == 'entry_states':
                    state_data = DashboardService.get_state_distribution(data_source_id)
                    return {
                        'value': state_data.get('total', 0),
                        'label': config.get('label', 'Total Entries')
                    }
            
            elif widget_type == 'git_commits' and data_source_type == 'git_repository':
                # Get commits from Git integration
                return DashboardService.get_git_commits(data_source_id, config)
            
            elif widget_type == 'git_commits_chart' and data_source_type == 'git_repository':
                # Get commit timeline data for Git chart
                return DashboardService.get_git_commits_timeline(data_source_id, config)

            elif widget_type in ('line_chart', 'entry_data_chart') and data_source_type == 'entry_data':
                metric_ids = config.get('metric_ids', [])
                time_range = config.get('time_range', '30d')
                x_axis_type = config.get('x_axis_type', 'recorded_at')
                x_axis_field = config.get('x_axis_field', 'commenced_at')

                if not metric_ids:
                    return {'error': 'No metrics configured', 'series': []}

                entry_ids = []
                if data_source_id:
                    search_data = DashboardService.get_saved_search_entries(data_source_id, ignore_limit=True)
                    entry_ids = [e['id'] for e in search_data.get('entries', [])]

                return DashboardService.get_entry_data_trends(
                    metric_ids=metric_ids,
                    entry_ids=entry_ids,
                    time_range=time_range,
                    x_axis_type=x_axis_type,
                    x_axis_field=x_axis_field,
                )

            elif widget_type == 'entry_data_chart' and data_source_type == 'entry_relationship':
                # Resolve related entry IDs from the pivot entry's relationships
                time_range = config.get('time_range', '30d')
                x_axis_type = config.get('x_axis_type', 'recorded_at')
                x_axis_field = config.get('x_axis_field', 'commenced_at')
                rel_def_id = config.get('relationship_definition_id')
                pivot_entry_id = data_source_id  # data_source_id holds the pivot entry
                data_mode = config.get('data_mode', 'metrics')

                if not pivot_entry_id:
                    return {'error': 'No pivot entry configured', 'series': []}

                from ..db import get_connection
                conn = get_connection()
                try:
                    cursor = conn.cursor()
                    if rel_def_id:
                        cursor.execute('''
                            SELECT source_entry_id, target_entry_id
                            FROM EntryRelationship
                            WHERE relationship_type = ?
                              AND (source_entry_id = ? OR target_entry_id = ?)
                        ''', (rel_def_id, pivot_entry_id, pivot_entry_id))
                    else:
                        cursor.execute('''
                            SELECT source_entry_id, target_entry_id
                            FROM EntryRelationship
                            WHERE source_entry_id = ? OR target_entry_id = ?
                        ''', (pivot_entry_id, pivot_entry_id))
                    rows = cursor.fetchall()
                    entry_ids = list({
                        r['target_entry_id'] if r['source_entry_id'] == pivot_entry_id else r['source_entry_id']
                        for r in rows
                    })

                    if not entry_ids:
                        return {'series': [], 'x_axis_type': x_axis_type, 'x_axis_label': 'Entry'}

                    if data_mode == 'columns':
                        column_ids = config.get('column_ids', [])
                        if not column_ids:
                            return {'error': 'No columns configured', 'series': []}

                        _ALLOWED_FIELDS = {'commenced_at', 'created_at', 'intended_end_date', 'actual_end_date'}
                        if x_axis_field not in _ALLOWED_FIELDS:
                            x_axis_field = 'commenced_at'
                        effective_x = x_axis_type if x_axis_type in ('entry_name', 'entry_field') else 'entry_name'

                        ep = ','.join(['?'] * len(entry_ids))
                        cp = ','.join(['?'] * len(column_ids))

                        cursor.execute(
                            f'SELECT id, title, commenced_at, created_at, intended_end_date, actual_end_date '
                            f'FROM Entry WHERE id IN ({ep})',
                            entry_ids,
                        )
                        entry_rows = {r['id']: r for r in cursor.fetchall()}

                        cursor.execute(f'SELECT id, label, unit FROM CustomColumn WHERE id IN ({cp})', column_ids)
                        col_meta = {r['id']: r for r in cursor.fetchall()}

                        cursor.execute(
                            f'SELECT entry_id, custom_column_id, value FROM CustomColumnValue '
                            f'WHERE entry_id IN ({ep}) AND custom_column_id IN ({cp})',
                            entry_ids + column_ids,
                        )
                        value_map = {}
                        for r in cursor.fetchall():
                            value_map.setdefault(r['entry_id'], {})[r['custom_column_id']] = r['value']

                        def _x_val(er):
                            if effective_x == 'entry_field':
                                v = er[x_axis_field]
                                return str(v)[:10] if v else er['title']
                            return er['title']

                        def _sort_key(eid):
                            er = entry_rows.get(eid)
                            if not er:
                                return ''
                            if effective_x == 'entry_field':
                                return str(er[x_axis_field] or '')
                            return er['title'] or ''

                        sorted_ids = sorted([e for e in entry_ids if e in entry_rows], key=_sort_key)
                        palette = ['#4bc0c0', '#ff6384', '#36a2eb', '#ffce56', '#9966ff', '#ff9f40', '#c9cbcf']
                        series = []
                        for i, col_id in enumerate(column_ids):
                            meta = col_meta.get(col_id, {})
                            pts = []
                            for eid in sorted_ids:
                                raw = value_map.get(eid, {}).get(col_id)
                                if raw is None:
                                    continue
                                try:
                                    y = float(raw)
                                except (ValueError, TypeError):
                                    continue
                                pts.append({'x': _x_val(entry_rows[eid]), 'y': y, 'entry_id': eid})
                            series.append({
                                'label': meta.get('label', f'Column {col_id}'),
                                'column_id': col_id,
                                'unit': meta.get('unit') or '',
                                'color': palette[i % len(palette)],
                                'data_points': pts,
                            })

                        x_label = 'Entry' if effective_x == 'entry_name' else x_axis_field.replace('_', ' ').title()
                        return {'series': series, 'x_axis_type': 'category', 'x_axis_label': x_label}

                finally:
                    conn.close()

                metric_ids = config.get('metric_ids', [])
                if not metric_ids:
                    return {'error': 'No metrics configured', 'series': []}

                return DashboardService.get_entry_data_trends(
                    metric_ids=metric_ids,
                    entry_ids=entry_ids,
                    time_range=time_range,
                    x_axis_type=x_axis_type,
                    x_axis_field=x_axis_field,
                )

            return {'error': 'Unsupported widget type or data source'}
            
        except Exception as e:
            logger.error(f"Error getting widget data: {e}", exc_info=True)
            return {'error': str(e)}
