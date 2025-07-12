# template_app/app/routes/maintenance_routes.py
from flask import Blueprint, render_template, g, current_app
import sqlite3

# Define a Blueprint for maintenance routes
maintenance_bp = Blueprint('maintenance', __name__, template_folder='../templates')

def get_db():
    if 'db' not in g:
        db_path = current_app.config['DATABASE_PATH']
        g.db = sqlite3.connect(db_path)
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
    cursor.execute("SELECT id, name, singular_label, plural_label, description, note_types, is_primary FROM EntryType ORDER BY singular_label")
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