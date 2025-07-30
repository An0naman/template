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
    # get_system_parameters is now a global in jinja_env, so no direct import needed here,
    # but we will call it from get_db or directly if needed within the function.
    # Accessing it via current_app.jinja_env.globals.get('get_system_parameters')
    # or ensuring it's loaded into app context. For simplicity, we'll re-import
    # it from db.py for use within Python, and it will be available for templates.
    from ..db import get_system_parameters # Import locally for function use

    params = get_system_parameters()
    conn = get_db()
    cursor = conn.cursor()

    view_all = request.args.get('view', 'primary') # Default to 'primary' view

    if view_all == 'all':
        cursor.execute('''
            SELECT
                e.id, e.title, e.description,
                et.singular_label AS entry_type_label,
                et.name AS entry_type_name,
                e.created_at
            FROM Entry e
            JOIN EntryType et ON e.entry_type_id = et.id
            ORDER BY e.created_at DESC
        ''')
        entries = cursor.fetchall()
    else: # view_all == 'primary'
        cursor.execute('''
            SELECT
                e.id, e.title, e.description,
                et.singular_label AS entry_type_label,
                et.name AS entry_type_name,
                e.created_at
            FROM Entry e
            JOIN EntryType et ON e.entry_type_id = et.id
            WHERE et.is_primary = 1
            ORDER BY e.created_at DESC
        ''')
        entries = cursor.fetchall()

    cursor.execute("SELECT id, name, singular_label, plural_label, is_primary FROM EntryType ORDER BY singular_label")
    entry_types = cursor.fetchall()

    return render_template('index.html',
                           project_name=params.get('project_name'),
                           entries=entries,
                           entry_singular_label=params.get('entry_singular_label'),
                           entry_plural_label=params.get('entry_plural_label'),
                           all_entry_types=entry_types,
                           current_view=view_all)

@main_bp.route('/entry/<int:entry_id>')
def entry_detail_page(entry_id):
    from ..db import get_system_parameters # Import locally for function use

    params = get_system_parameters()
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT
            e.id, e.title, e.description, e.entry_type_id,
            et.singular_label AS entry_type_label,
            et.name AS entry_type_name,
            et.note_types, et.has_sensors, e.created_at
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
        'created_at': entry['created_at']
    }

    return render_template('entry_detail.html',
                           project_name=params.get('project_name'),
                           entry=entry_data,
                           entry_singular_label=params.get('entry_singular_label'),
                           entry_plural_label=params.get('entry_plural_label'))