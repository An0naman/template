# template_app/app/routes/main_routes.py
from flask import Blueprint, render_template, request, g, current_app
import sqlite3

# Define a Blueprint for main routes
main_bp = Blueprint('main', __name__, template_folder='../templates')

def get_db():
    if 'db' not in g:
        db_path = current_app.config['DATABASE_PATH']
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
    return g.db

@main_bp.route('/')
def index():
    from ..db import get_system_parameters, get_user_preference, set_user_preference # Import locally for function use
    from ..api.theme_api import generate_theme_css, get_current_theme_settings

    params = get_system_parameters()
    conn = get_db()
    cursor = conn.cursor()

    # Get filter parameters from query string or use saved preferences
    view_type = request.args.get('view_type')
    entry_type_filter = request.args.get('entry_type')
    status_filter = request.args.get('status')
    result_limit = request.args.get('result_limit')
    save_filters = request.args.get('save_filters') == 'true'
    
    # If no filters provided, load from saved preferences
    if view_type is None:
        view_type = get_user_preference('default_view_type', 'all')  # Changed default from 'primary' to 'all'
    if entry_type_filter is None:
        entry_type_filter = get_user_preference('default_entry_type_filter', '')
    if status_filter is None:
        status_filter = get_user_preference('default_status_filter', 'all')  # Changed from 'active' to 'all' for frontend filtering
    if result_limit is None:
        result_limit = get_user_preference('default_result_limit', '50')
    
    # Save filters if requested
    if save_filters:
        set_user_preference('default_view_type', view_type)
        set_user_preference('default_entry_type_filter', entry_type_filter)
        set_user_preference('default_status_filter', status_filter)
        set_user_preference('default_result_limit', result_limit)
    
    # Convert result_limit to integer, with fallback
    try:
        result_limit_int = int(result_limit) if result_limit else 50
        result_limit_int = max(1, min(result_limit_int, 1000))  # Limit between 1 and 1000
    except (ValueError, TypeError):
        result_limit_int = 50
    
    # Build the query based on filters
    query_parts = []
    params_list = []
    
    base_query = '''
        SELECT
            e.id, e.title, e.description,
            e.entry_type_id,
            et.singular_label AS entry_type_label,
            et.name AS entry_type_name,
            e.created_at, e.status,
            COALESCE(es.category, 'active') AS status_category,
            COALESCE(es.color, '#28a745') AS status_color
        FROM Entry e
        JOIN EntryType et ON e.entry_type_id = et.id
        LEFT JOIN EntryState es ON es.entry_type_id = e.entry_type_id AND es.name = e.status
    '''
    
    # Add WHERE conditions
    conditions = []
    
    # For the main index view, don't filter by status in backend - let frontend handle it
    # Status filtering is now handled by JavaScript live filtering
    
    # View type filter
    if view_type == 'primary':
        conditions.append("et.is_primary = 1")
    elif view_type == 'type' and entry_type_filter:
        conditions.append("et.id = ?")
        params_list.append(entry_type_filter)
    
    # Combine conditions
    if conditions:
        query_parts.append("WHERE " + " AND ".join(conditions))
    
    query_parts.append("ORDER BY e.created_at DESC")
    query_parts.append(f"LIMIT {result_limit_int}")
    
    final_query = base_query + " " + " ".join(query_parts)
    
    cursor.execute(final_query, params_list)
    entries = cursor.fetchall()

    # Get all entry types for the filter dropdown
    cursor.execute("SELECT id, name, singular_label, plural_label, is_primary FROM EntryType ORDER BY singular_label")
    entry_types = cursor.fetchall()

    # Get search defaults
    search_defaults = {
        'search_term': params.get('default_search_term', ''),
        'type_filter': params.get('default_type_filter', ''),
        'status_filter': params.get('default_status_filter', ''),
        'date_range': params.get('default_date_range', ''),
        'sort_by': params.get('default_sort_by', 'created_desc'),
        'content_display': params.get('default_content_display', ''),
        'result_limit': params.get('default_result_limit', '50')
    }

    return render_template('index.html',
                           project_name=params.get('project_name'),
                           project_subtitle=params.get('project_subtitle'),
                           entries=entries,
                           entry_singular_label=params.get('entry_singular_label'),
                           entry_plural_label=params.get('entry_plural_label'),
                           all_entry_types=entry_types,
                           current_view_type=view_type,
                           current_entry_type=entry_type_filter,
                           current_status=status_filter,
                           current_result_limit=result_limit,
                           search_defaults=search_defaults,
                           theme_css=generate_theme_css(),
                           theme_settings=get_current_theme_settings())

@main_bp.route('/entry/<int:entry_id>')
def entry_detail_page(entry_id):
    from ..db import get_system_parameters # Import locally for function use
    from ..api.theme_api import generate_theme_css, get_current_theme_settings

    params = get_system_parameters()
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT
            e.id, e.title, e.description, e.entry_type_id, e.intended_end_date, 
            e.actual_end_date, e.status,
            et.singular_label AS entry_type_label,
            et.name AS entry_type_name,
            et.note_types, et.has_sensors, et.enabled_sensor_types, et.show_labels_section, 
            et.show_end_dates, e.created_at,
            COALESCE(es.category, 'active') AS status_category,
            COALESCE(es.color, '#28a745') AS status_color
        FROM Entry e
        JOIN EntryType et ON e.entry_type_id = et.id
        LEFT JOIN EntryState es ON es.entry_type_id = e.entry_type_id AND es.name = e.status
        WHERE e.id = ?
    ''', (entry_id,))
    entry = cursor.fetchone()

    if entry is None:
        return render_template('404.html'), 404

    entry_data = {
        'id': entry['id'],
        'title': entry['title'],
        'description': entry['description'],
        'entry_type_id': entry['entry_type_id'],
        'entry_type_label': entry['entry_type_label'],
        'entry_type_name': entry['entry_type_name'],
        'note_types': entry['note_types'],
        'has_sensors': bool(entry['has_sensors']) if entry['has_sensors'] is not None else False,
        'enabled_sensor_types': entry['enabled_sensor_types'] or '',
        'show_labels_section': bool(entry['show_labels_section']) if entry['show_labels_section'] is not None else True,
        'show_end_dates': bool(entry['show_end_dates']) if entry['show_end_dates'] is not None else False,
        'intended_end_date': entry['intended_end_date'] if 'intended_end_date' in entry.keys() else None,
        'actual_end_date': entry['actual_end_date'] if 'actual_end_date' in entry.keys() else None,
        'status': entry['status'] if 'status' in entry.keys() else 'Active',
        'status_category': entry['status_category'] if 'status_category' in entry.keys() else 'active',
        'status_color': entry['status_color'] if 'status_color' in entry.keys() else '#28a745',
        'created_at': entry['created_at']
    }

    return render_template('entry_detail.html',
                           project_name=params.get('project_name'),
                           entry=entry_data,
                           entry_singular_label=params.get('entry_singular_label'),
                           entry_plural_label=params.get('entry_plural_label'),
                           allowed_file_types=params.get('allowed_file_types', 
                               'txt,pdf,png,jpg,jpeg,gif,webp,svg,doc,docx,xls,xlsx,ppt,pptx,mp4,avi,mov,wmv,flv,webm,mkv,mp3,wav,flac,aac,ogg,zip,rar,7z,tar,gz'),
                           max_file_size=params.get('max_file_size', '50'),
                           theme_css=generate_theme_css(),
                           theme_settings=get_current_theme_settings())

@main_bp.route('/settings')
def settings():
    from ..db import get_system_parameters
    params = get_system_parameters()
    
    return render_template('settings.html',
                          project_name=params.get('project_name'),
                          params=params)

@main_bp.route('/manage_ntfy')
def manage_ntfy():
    """ntfy push notification management page"""
    from ..db import get_system_parameters
    params = get_system_parameters()
    
    return render_template('manage_ntfy.html',
                          project_name=params.get('project_name'),
                          config=params)

@main_bp.route('/sql_ide')
def sql_ide():
    """SQL IDE route for database management"""
    from ..db import get_system_parameters
    params = get_system_parameters()
    
    return render_template('simple_sql_ide.html',
                          project_name=params.get('project_name'))