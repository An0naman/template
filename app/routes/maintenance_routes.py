# template_app/app/routes/maintenance_routes.py
from flask import Blueprint, render_template, g, current_app
import sqlite3

# Define a Blueprint for maintenance routes
maintenance_bp = Blueprint('maintenance', __name__, template_folder='../templates')

def get_db():
    if 'db' not in g:
        from ..db import get_connection
        g.db = get_connection()
        g.db.row_factory = sqlite3.Row
    return g.db

@maintenance_bp.route('/maintenance')
def maintenance_module_page():
    from ..db import get_system_parameters
    params = get_system_parameters()
    return render_template('maintenance_module.html',
                           project_name=params.get('project_name'),
                           entry_singular_label=params.get('entry_singular_label'),
                           entry_plural_label=params.get('entry_plural_label'))

@maintenance_bp.route('/manage_entry_types')
def manage_entry_types_page():
    from ..db import get_system_parameters
    params = get_system_parameters()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, singular_label, plural_label, description, note_types, is_primary, has_sensors, show_labels_section, show_end_dates, enabled_sensor_types FROM EntryType ORDER BY singular_label")
    entry_types = cursor.fetchall()
    return render_template('manage_entry_types.html',
                           project_name=params.get('project_name'),
                           entry_types=[dict(row) for row in entry_types],
                           entry_singular_label=params.get('entry_singular_label'),
                           entry_plural_label=params.get('entry_plural_label'))

@maintenance_bp.route('/manage_relationships')
def manage_relationships_page():
    from ..db import get_system_parameters
    params = get_system_parameters()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, singular_label, plural_label FROM EntryType ORDER BY singular_label")
    entry_types = cursor.fetchall()
    return render_template('relationship_definitions.html',
                           project_name=params.get('project_name'),
                           entry_types=[dict(row) for row in entry_types],
                           entry_singular_label=params.get('entry_singular_label'),
                           entry_plural_label=params.get('entry_plural_label'))

@maintenance_bp.route('/manage_sensor_types')
def manage_sensor_types_page():
    from ..db import get_system_parameters
    params = get_system_parameters()
    return render_template('manage_sensor_types.html',
                           project_name=params.get('project_name'),
                           entry_singular_label=params.get('entry_singular_label'),
                           entry_plural_label=params.get('entry_plural_label'),
                           sensor_types=params.get('sensor_types', 'Temperature,Humidity,Pressure'))

@maintenance_bp.route('/manage_sensors')
def manage_sensors_page():
    from ..db import get_system_parameters
    from flask import url_for
    params = get_system_parameters()
    return render_template('manage_sensors.html',
                           project_name=params.get('project_name'),
                           entry_singular_label=params.get('entry_singular_label'),
                           entry_plural_label=params.get('entry_plural_label'),
                           manage_sensor_types_url=url_for('maintenance.manage_sensor_types_page'))

@maintenance_bp.route('/manage_sensor_alarms')
def manage_sensor_alarms_page():
    from ..db import get_system_parameters
    params = get_system_parameters()
    conn = get_db()
    cursor = conn.cursor()
    
    # Get entry types for dropdown
    cursor.execute("SELECT id, singular_label FROM EntryType ORDER BY singular_label")
    entry_types = cursor.fetchall()
    
    # Get all entries for dropdown
    cursor.execute("SELECT id, title FROM Entry ORDER BY title")
    entries = cursor.fetchall()
    
    return render_template('manage_sensor_alarms.html',
                           project_name=params.get('project_name'),
                           entry_singular_label=params.get('entry_singular_label'),
                           entry_plural_label=params.get('entry_plural_label'),
                           entry_types=[dict(row) for row in entry_types],
                           entries=[dict(row) for row in entries],
                           sensor_types=[t.strip() for t in params.get('sensor_types', '').split(',') if t.strip()])

@maintenance_bp.route('/manage_note_types')
def manage_note_types_page():
    from ..db import get_system_parameters
    params = get_system_parameters()
    return render_template('manage_note_types.html',
                           project_name=params.get('project_name'),
                           entry_singular_label=params.get('entry_singular_label'),
                           entry_plural_label=params.get('entry_plural_label'))

@maintenance_bp.route('/manage_file_settings')
def manage_file_settings_page():
    from ..db import get_system_parameters
    params = get_system_parameters()
    return render_template('manage_file_settings.html',
                           project_name=params.get('project_name'),
                           entry_singular_label=params.get('entry_singular_label'),
                           entry_plural_label=params.get('entry_plural_label'),
                           allowed_file_types=params.get('allowed_file_types', ''),
                           max_file_size=params.get('max_file_size', '50'))

@maintenance_bp.route('/manage_theme_settings')
def manage_theme_settings_page():
    from ..db import get_system_parameters
    from ..api.theme_api import get_current_theme_settings
    
    params = get_system_parameters()
    theme_settings = get_current_theme_settings()
    
    return render_template('manage_theme_settings.html',
                           project_name=params.get('project_name'),
                           entry_singular_label=params.get('entry_singular_label'),
                           entry_plural_label=params.get('entry_plural_label'),
                           **theme_settings)

@maintenance_bp.route('/manage_devices')
def manage_devices_page():
    from ..db import get_system_parameters
    params = get_system_parameters()
    return render_template('manage_devices.html',
                           project_name=params.get('project_name'),
                           entry_singular_label=params.get('entry_singular_label'),
                           entry_plural_label=params.get('entry_plural_label'))

@maintenance_bp.route('/sql_ide')
def sql_ide_page():
    from ..db import get_system_parameters
    params = get_system_parameters()
    return render_template('sql_ide.html',
                           project_name=params.get('project_name'),
                           entry_singular_label=params.get('entry_singular_label'),
                           entry_plural_label=params.get('entry_plural_label'))