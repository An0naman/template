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
    from ..db import get_system_parameters # Import locally for function use
    from ..api.theme_api import generate_theme_css, get_current_theme_settings

    params = get_system_parameters()
    conn = get_db()
    cursor = conn.cursor()

    # Get filter parameters
    view_type = request.args.get('view_type', 'primary')  # 'primary', 'all', 'type'
    entry_type_filter = request.args.get('entry_type', '')
    status_filter = request.args.get('status', 'active')  # Default to active only
    
    # Build the query based on filters
    query_parts = []
    params_list = []
    
    base_query = '''
        SELECT
            e.id, e.title, e.description,
            et.singular_label AS entry_type_label,
            et.name AS entry_type_name,
            e.created_at, e.status
        FROM Entry e
        JOIN EntryType et ON e.entry_type_id = et.id
    '''
    
    # Add WHERE conditions
    conditions = []
    
    # Status filter (default to active)
    if status_filter == 'active':
        conditions.append("(e.status = 'active' OR e.status IS NULL)")
    elif status_filter == 'inactive':
        conditions.append("e.status = 'inactive'")
    # 'all' status means no status filter
    
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
    
    final_query = base_query + " " + " ".join(query_parts)
    
    cursor.execute(final_query, params_list)
    entries = cursor.fetchall()

    # Get all entry types for the filter dropdown
    cursor.execute("SELECT id, name, singular_label, plural_label, is_primary FROM EntryType ORDER BY singular_label")
    entry_types = cursor.fetchall()

    return render_template('index.html',
                           project_name=params.get('project_name'),
                           entries=entries,
                           entry_singular_label=params.get('entry_singular_label'),
                           entry_plural_label=params.get('entry_plural_label'),
                           all_entry_types=entry_types,
                           current_view_type=view_type,
                           current_entry_type=entry_type_filter,
                           current_status=status_filter,
                           theme_css=generate_theme_css(),
                           theme_settings=get_current_theme_settings())

@main_bp.route('/entry/<int:entry_id>')
def entry_detail_page(entry_id):
    from ..db import get_system_parameters # Import locally for function use
    from ..api.theme_api import generate_theme_css

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
            et.show_end_dates, e.created_at
        FROM Entry e
        JOIN EntryType et ON e.entry_type_id = et.id
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
        'status': entry['status'] if 'status' in entry.keys() else 'active',
        'created_at': entry['created_at']
    }

    return render_template('entry_detail.html',
                           project_name=params.get('project_name'),
                           entry=entry_data,
                           entry_singular_label=params.get('entry_singular_label'),
                           entry_plural_label=params.get('entry_plural_label'),
                           theme_css=generate_theme_css())

@main_bp.route('/settings')
def settings():
    from ..db import get_system_parameters
    params = get_system_parameters()
    
    return render_template('settings.html',
                          project_name=params.get('project_name'),
                          params=params)