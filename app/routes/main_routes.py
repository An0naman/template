# template_app/app/routes/main_routes.py
from flask import Blueprint, render_template, request, g, current_app, redirect, url_for
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
    # Redirect to dashboard as the default page
    return redirect(url_for('main.dashboard'))

@main_bp.route('/entries')
def entries():
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
        result_limit = get_user_preference('default_result_limit', '10000')
    
    # Save filters if requested
    if save_filters:
        set_user_preference('default_view_type', view_type)
        set_user_preference('default_entry_type_filter', entry_type_filter)
        set_user_preference('default_status_filter', status_filter)
        set_user_preference('default_result_limit', result_limit)
    
    # Convert result_limit to integer, with fallback
    # For the entries list page, we load all entries since filtering is done client-side
    # If you have thousands of entries, consider implementing server-side pagination
    try:
        result_limit_int = int(result_limit) if result_limit else 10000
        result_limit_int = max(1, min(result_limit_int, 10000))  # Limit between 1 and 10000
    except (ValueError, TypeError):
        result_limit_int = 10000
    
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
        'result_limit': params.get('default_result_limit', '10000')
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
def entry_detail_v2(entry_id):
    """Entry detail page using v2 template with dynamic layout (default view)"""
    from ..db import get_system_parameters
    from ..services.entry_layout_service import EntryLayoutService
    
    params = get_system_parameters()
    conn = get_db()
    cursor = conn.cursor()
    
    # Get entry data
    cursor.execute('''
        SELECT
            e.id, e.title, e.description, e.entry_type_id, e.intended_end_date, 
            e.actual_end_date, e.status,
            et.singular_label AS entry_type_label,
            et.name AS entry_type_name,
            et.note_types, et.has_sensors, et.enabled_sensor_types, et.show_labels_section, 
            et.show_end_dates, e.created_at, e.commenced_at,
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
        'created_at': entry['created_at'],
        'commenced_at': entry['commenced_at']
    }
    
    # Get layout configuration
    layout_service = EntryLayoutService()
    layout = layout_service.get_layout_for_entry_type(entry_data.get('entry_type_id'))
    
    # Initialize section configuration and rows
    section_config = {}
    section_rows = []
    section_order = []
    
    if layout and layout.get('sections'):
        # Build section_config dictionary
        for section in layout['sections']:
            section_type = section['section_type']
            section_config[section_type] = {
                'visible': section.get('is_visible', True),
                'order': section.get('display_order', 999),
                'title': section.get('title', ''),
                'collapsible': section.get('is_collapsible', False),
                'collapsed': section.get('default_collapsed', False),
                'width': section.get('width', 12),
                'height': section.get('height', 3),
                'max_height': section.get('max_height'),
                'x': section.get('position_x', 0),  # Fixed: use position_x from DB
                'y': section.get('position_y', 0)   # Fixed: use position_y from DB
            }
        
        # Create ordered list of visible sections
        visible_sections = [s for s in layout['sections'] if s.get('is_visible', True)]
        
        # Group sections by Y coordinate (row position in the grid)
        # Sort by Y first, then by X within each row
        visible_sections.sort(key=lambda x: (x.get('position_y', 0), x.get('position_x', 0)))
        
        # Group into rows based on Y coordinate
        from itertools import groupby
        for y_pos, sections_in_row in groupby(visible_sections, key=lambda x: x.get('position_y', 0)):
            row_sections = [s['section_type'] for s in sections_in_row]
            if row_sections:
                section_rows.append(row_sections)
        
        # Build section_order from the sorted visible sections
        # Changed to pass full section objects to support multiple instances of same type
        section_order = visible_sections
    
    # Get relationship data for the relationships section
    relationships_data = {}
    
    # Fetch outgoing relationships (where this entry is the source)
    # Use CASE to select the correct label based on current entry's type
    cursor.execute('''
        SELECT
            er.id AS relationship_id,
            er.target_entry_id AS related_entry_id,
            e_to.title AS related_entry_title,
            e_to.status AS related_entry_status,
            COALESCE(es_to.color, '#6c757d') AS related_entry_status_color,
            et_to.id AS related_entry_type_id,
            et_to.singular_label AS related_entry_type_label,
            rd.id AS definition_id,
            rd.name AS definition_name,
            CASE 
                WHEN rd.entry_type_id_from = ? THEN rd.label_from_side
                ELSE rd.label_to_side
            END AS relationship_type,
            er.quantity,
            er.unit
        FROM EntryRelationship er
        JOIN RelationshipDefinition rd ON er.relationship_type = rd.id
        JOIN Entry e_to ON er.target_entry_id = e_to.id
        JOIN EntryType et_to ON e_to.entry_type_id = et_to.id
        LEFT JOIN EntryState es_to ON es_to.entry_type_id = e_to.entry_type_id AND es_to.name = e_to.status
        WHERE er.source_entry_id = ?
        ORDER BY rd.name, e_to.title
    ''', (entry_data['entry_type_id'], entry_id))
    
    outgoing_relationships = []
    for row in cursor.fetchall():
        outgoing_relationships.append({
            'id': row['relationship_id'],
            'related_entry_id': row['related_entry_id'],
            'related_entry_title': row['related_entry_title'],
            'related_entry_status': row['related_entry_status'],
            'related_entry_status_color': row['related_entry_status_color'],
            'related_entry_type': {
                'id': row['related_entry_type_id'],
                'label': row['related_entry_type_label'],
                'icon': 'fas fa-link',  # Default icon
                'color': '#6c757d'  # Default color (Bootstrap secondary)
            },
            'relationship_type': row['relationship_type'],
            'definition_name': row['definition_name'],
            'quantity': row['quantity'],
            'unit': row['unit']
        })
    
    # Fetch incoming relationships (where this entry is the target)
    # Use CASE to select the correct label based on current entry's type
    cursor.execute('''
        SELECT
            er.id AS relationship_id,
            er.source_entry_id AS related_entry_id,
            e_from.title AS related_entry_title,
            e_from.status AS related_entry_status,
            COALESCE(es_from.color, '#6c757d') AS related_entry_status_color,
            et_from.id AS related_entry_type_id,
            et_from.singular_label AS related_entry_type_label,
            rd.id AS definition_id,
            rd.name AS definition_name,
            CASE 
                WHEN rd.entry_type_id_to = ? THEN rd.label_to_side
                ELSE rd.label_from_side
            END AS relationship_type,
            er.quantity,
            er.unit
        FROM EntryRelationship er
        JOIN RelationshipDefinition rd ON er.relationship_type = rd.id
        JOIN Entry e_from ON er.source_entry_id = e_from.id
        JOIN EntryType et_from ON e_from.entry_type_id = et_from.id
        LEFT JOIN EntryState es_from ON es_from.entry_type_id = e_from.entry_type_id AND es_from.name = e_from.status
        WHERE er.target_entry_id = ?
        ORDER BY rd.name, e_from.title
    ''', (entry_data['entry_type_id'], entry_id))
    
    incoming_relationships = []
    for row in cursor.fetchall():
        incoming_relationships.append({
            'id': row['relationship_id'],
            'related_entry_id': row['related_entry_id'],
            'related_entry_title': row['related_entry_title'],
            'related_entry_status': row['related_entry_status'],
            'related_entry_status_color': row['related_entry_status_color'],
            'related_entry_type': {
                'id': row['related_entry_type_id'],
                'label': row['related_entry_type_label'],
                'icon': 'fas fa-link',  # Default icon
                'color': '#6c757d'  # Default color (Bootstrap secondary)
            },
            'relationship_type': row['relationship_type'],
            'definition_name': row['definition_name'],
            'quantity': row['quantity'],
            'unit': row['unit'],
            'is_incoming': True
        })
    
    # Group outgoing relationships by type
    grouped_outgoing = {}
    for rel in outgoing_relationships:
        rel_type = rel['relationship_type']
        if rel_type not in grouped_outgoing:
            grouped_outgoing[rel_type] = []
        grouped_outgoing[rel_type].append(rel)
    
    # Group incoming relationships by type
    grouped_incoming = {}
    for rel in incoming_relationships:
        rel_type = rel['relationship_type']
        if rel_type not in grouped_incoming:
            grouped_incoming[rel_type] = []
        grouped_incoming[rel_type].append(rel)
    
    relationships_data = {
        'outgoing': outgoing_relationships,
        'incoming': incoming_relationships,
        'grouped_outgoing': grouped_outgoing,
        'grouped_incoming': grouped_incoming,
        'outgoing_count': len(outgoing_relationships),
        'incoming_count': len(incoming_relationships),
        'total_count': len(outgoing_relationships) + len(incoming_relationships)
    }
    
    # Debug logging
    print(f"DEBUG V2 Entry {entry_id} - section_rows: {section_rows}")
    print(f"DEBUG V2 Entry {entry_id} - section_config: {section_config}")
    print(f"DEBUG V2 Entry {entry_id} - relationships: {relationships_data['total_count']} total")

    # Extract tabs and sections by tab
    tabs = layout.get('tabs', []) if layout else []
    sections_by_tab = layout.get('sections_by_tab', {}) if layout else {}
    
    # Create response with cache-busting headers
    from flask import make_response
    response = make_response(render_template('entry_detail_v2.html',
                           project_name=params.get('project_name'),
                           entry=entry_data,
                           section_config=section_config,
                           section_order=section_order,
                           section_rows=section_rows,
                           tabs=tabs,
                           sections_by_tab=sections_by_tab,
                           relationships=relationships_data,
                           allowed_file_types=params.get('allowed_file_types', 
                               'txt,pdf,png,jpg,jpeg,gif,webp,svg,doc,docx,xls,xlsx,ppt,pptx,mp4,avi,mov,wmv,flv,webm,mkv,mp3,wav,flac,aac,ogg,zip,rar,7z,tar,gz'),
                           max_file_size=params.get('max_file_size', '50')))
    
    # Add cache control headers to force browser to reload
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    return response

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

@main_bp.route('/dashboard')
def dashboard():
    """Dashboard route for configurable analytics dashboard"""
    from ..db import get_system_parameters
    from ..api.theme_api import generate_theme_css, get_current_theme_settings
    
    params = get_system_parameters()
    theme_settings = get_current_theme_settings()
    theme_css = generate_theme_css(theme_settings)
    
    return render_template('dashboard.html',
                          project_name=params.get('project_name'),
                          theme_settings=theme_settings,
                          theme_css=theme_css)

@main_bp.route('/entry-layout-builder/<int:entry_type_id>')
def entry_layout_builder(entry_type_id):
    """Entry Layout Builder route for configuring entry type layouts"""
    from ..db import get_system_parameters
    from ..api.theme_api import generate_theme_css, get_current_theme_settings
    
    params = get_system_parameters()
    theme_settings = get_current_theme_settings()
    theme_css = generate_theme_css(theme_settings)
    
    # Get entry type information
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, name, singular_label, plural_label, description,
               has_sensors, show_labels_section, show_end_dates
        FROM EntryType
        WHERE id = ?
    """, (entry_type_id,))
    
    entry_type = cursor.fetchone()
    
    if not entry_type:
        return render_template('404.html'), 404
    
    entry_type_dict = {
        'id': entry_type['id'],
        'name': entry_type['name'],
        'singular_label': entry_type['singular_label'],
        'plural_label': entry_type['plural_label'],
        'description': entry_type['description'],
        'has_sensors': bool(entry_type['has_sensors']),
        'show_labels_section': bool(entry_type['show_labels_section']),
        'show_end_dates': bool(entry_type['show_end_dates'])
    }
    
    return render_template('entry_layout_builder.html',
                          entry_type_id=entry_type_id,
                          entry_type=entry_type_dict,
                          project_name=params.get('project_name'),
                          theme_settings=theme_settings,
                          theme_css=theme_css)

@main_bp.route('/kanban')
def kanban_list():
    """Kanban boards list route - redirects to default board if one exists"""
    from ..db import get_system_parameters
    from ..api.theme_api import generate_theme_css, get_current_theme_settings
    
    params = get_system_parameters()
    theme_settings = get_current_theme_settings()
    theme_css = generate_theme_css(theme_settings)
    
    # Check if user explicitly wants to see the list
    show_list = request.args.get('list', 'false').lower() == 'true'
    
    # If not explicitly requesting list, check if there's a default board
    if not show_list:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id FROM KanbanBoard 
            WHERE is_default = 1 
            ORDER BY created_at DESC 
            LIMIT 1
        """)
        default_board = cursor.fetchone()
        
        # If a default board exists, redirect to it
        if default_board:
            return redirect(url_for('main.kanban_board', board_id=default_board['id']))
    
    return render_template('kanban_list.html',
                          project_name=params.get('project_name'),
                          theme_settings=theme_settings,
                          theme_css=theme_css)

@main_bp.route('/kanban/<int:board_id>')
def kanban_board(board_id):
    """Kanban board detail view route"""
    from ..db import get_system_parameters
    from ..api.theme_api import generate_theme_css, get_current_theme_settings
    
    params = get_system_parameters()
    theme_settings = get_current_theme_settings()
    theme_css = generate_theme_css(theme_settings)
    
    # Get board information
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT kb.id, kb.name, kb.description, kb.entry_type_id,
               et.singular_label AS entry_type_label,
               et.plural_label AS entry_type_plural
        FROM KanbanBoard kb
        JOIN EntryType et ON kb.entry_type_id = et.id
        WHERE kb.id = ?
    """, (board_id,))
    
    board = cursor.fetchone()
    
    if not board:
        return render_template('404.html'), 404
    
    board_dict = {
        'id': board['id'],
        'name': board['name'],
        'description': board['description'],
        'entry_type_id': board['entry_type_id'],
        'entry_type_label': board['entry_type_label'],
        'entry_type_plural': board['entry_type_plural']
    }
    
    return render_template('kanban_board.html',
                          board_id=board_id,
                          board=board_dict,
                          project_name=params.get('project_name'),
                          theme_settings=theme_settings,
                          theme_css=theme_css)

@main_bp.route('/sensor-master-control')
def sensor_master_control():
    """Sensor Master Control management page"""
    from ..db import get_system_parameters
    from ..api.theme_api import generate_theme_css, get_current_theme_settings
    
    params = get_system_parameters()
    theme_settings = get_current_theme_settings()
    theme_css = generate_theme_css(theme_settings)
    
    return render_template('sensor_master_control.html',
                          project_name=params.get('project_name'),
                          theme_settings=theme_settings,
                          theme_css=theme_css)

@main_bp.route('/sensor-plotter')
def sensor_plotter():
    """Render the sensor serial plotter page"""
    return render_template('sensor_plotter.html')
