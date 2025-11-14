# template_app/app/services/dashboard_service.py
"""
Dashboard Service
Provides data aggregation and analysis for dashboard widgets
"""

import logging
import sqlite3
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from flask import current_app

logger = logging.getLogger(__name__)

class DashboardService:
    """Service for aggregating dashboard data from various sources"""
    
    @staticmethod
    def get_db():
        """Get database connection"""
        db_path = current_app.config['DATABASE_PATH']
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def get_saved_search_entries(search_id: int) -> Dict[str, Any]:
        """
        Get entries matching a saved search
        
        Args:
            search_id: ID of the saved search
            
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
                    
                    # Apply result limit
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
                
                # Result limit
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
    def get_state_distribution(search_id: Optional[int] = None, entry_type_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get distribution of entry states
        
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
                # Get entries from saved search, then aggregate states
                search_data = DashboardService.get_saved_search_entries(search_id)
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
    def generate_ai_summary(search_id: int, widget_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate AI summary for a saved search
        
        Args:
            search_id: ID of the saved search
            widget_config: Optional widget configuration containing custom_prompt
            
        Returns:
            Dict with AI-generated summary
        """
        try:
            from app.services.ai_service import get_ai_service
            
            ai_service = get_ai_service()
            if not ai_service.is_available():
                return {
                    'summary': 'AI service is not configured. Please configure Gemini API key in system settings.',
                    'available': False
                }
            
            # Get entries from saved search
            search_data = DashboardService.get_saved_search_entries(search_id)
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
            response = ai_service.model.generate_content(prompt)
            summary = response.text.strip() if response and response.text else "Unable to generate summary"
            
            return {
                'summary': summary,
                'available': True,
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
            
            elif widget_type == 'pie_chart':
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
                
                # Get entry IDs from saved search if specified
                if data_source_id:
                    search_data = DashboardService.get_saved_search_entries(data_source_id)
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
                return DashboardService.generate_ai_summary(data_source_id, config)
            
            elif widget_type == 'stat_card':
                if data_source_type == 'saved_search':
                    search_data = DashboardService.get_saved_search_entries(data_source_id)
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
            
            return {'error': 'Unsupported widget type or data source'}
            
        except Exception as e:
            logger.error(f"Error getting widget data: {e}", exc_info=True)
            return {'error': str(e)}
