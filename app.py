# app.py

import sqlite3
from flask import Flask, render_template, request, jsonify, g, redirect, url_for
import os
import json
from datetime import datetime
import logging # Import logging module

# Configure logging to a file
# Ensure the 'logs' directory exists in your project root
log_dir = 'logs'
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(filename=os.path.join(log_dir, 'app_errors.log'), level=logging.ERROR,
                    format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')


# Assuming db.py is in the same directory and contains init_db and get_connection
from db import init_db, get_connection

# Corrected Flask app initialization to point to 'app/templates' and 'app/static'
# This assumes app.py is in the project root, and templates/static are in a subdirectory named 'app'.
app = Flask(__name__, template_folder='app/templates', static_folder='app/static')
app.config['DATABASE'] = 'template.db' # Path to your SQLite database file (matches db.py)
app.secret_key = 'your_super_secret_key_please_change_this_for_security' # Added for session management (flash messages, etc.)

# Add file handler to Flask's app logger
file_handler = logging.FileHandler(os.path.join(log_dir, 'flask_info.log'))
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO) # Set default level for Flask's logger (e.g., for info messages)


# --- Database Connection Management ---
def get_db():
    if 'db' not in g:
        g.db = get_connection() # Use the get_connection from db.py
        g.db.row_factory = sqlite3.Row # Allows accessing columns by name, crucial for dict-like access
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

# --- Helper Functions ---
def get_system_parameters():
    """
    Retrieves system parameters from the database.
    If no parameters exist, it initializes default ones.
    """
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT parameter_name, parameter_value FROM SystemParameters")
    params_list = cursor.fetchall() # Fetch as list of rows

    params = {}
    for row in params_list:
        params[row['parameter_name']] = row['parameter_value']

    if not params:
        # Initialize default parameters if none exist (this path should be less frequent now)
        app.logger.info("Initializing default system parameters.")
        params = {
            'project_name': 'My Awesome Project',
            'entry_singular_label': 'Entry',
            'entry_plural_label': 'Entries'
        }
        for name, value in params.items():
            try:
                cursor.execute("INSERT INTO SystemParameters (parameter_name, parameter_value) VALUES (?, ?)", (name, value))
                conn.commit()
            except sqlite3.IntegrityError:
                # Parameter already exists (e.g., if another process initializes simultaneously)
                app.logger.warning(f"System parameter '{name}' already exists during default initialization attempt.")
                pass
            except Exception as e:
                app.logger.error(f"Error initializing system parameter {name}: {e}", exc_info=True)
                conn.rollback() # Rollback if insert fails

    return params

def _serialize_entry(entry):
    """Helper to serialize entry rows into dictionaries."""
    if entry is None:
        return None
    return {
        "id": entry['id'],
        "title": entry['title'],
        "description": entry['description'],
        "entry_type_label": entry['entry_type_label'],
        "entry_type_name": entry['entry_type_name'],
        "created_at": entry['created_at']
    }

def _serialize_note(note):
    """Helper to serialize note rows into dictionaries."""
    if note is None:
        return None
    return {
        "id": note['id'],
        "entry_id": note['entry_id'],
        "note_title": note['note_title'],
        "note_text": note['note_text'],
        "note_type": note['type'], # Ensure this matches your DB column name for note type
        "created_at": note['created_at'],
        "image_paths": json.loads(note['image_paths']) if note['image_paths'] else []
    }

# --- Routes ---

@app.route('/')
def index():
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

@app.route('/entry/<int:entry_id>')
def entry_detail_page(entry_id):
    params = get_system_parameters()
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT
            e.id, e.title, e.description, e.entry_type_id,
            et.singular_label AS entry_type_label,
            et.name AS entry_type_name,
            et.note_types, e.created_at
        FROM Entry e
        JOIN EntryType et ON e.entry_type_id = et.id
        WHERE e.id = ?
    ''', (entry_id,))
    entry = cursor.fetchone()

    if entry is None:
        return render_template('404.html'), 404 # Ensure you have a 404.html template

    entry_data = {
        'id': entry['id'],
        'title': entry['title'],
        'description': entry['description'],
        'entry_type_id': entry['entry_type_id'], # Added entry_type_id for JS to fetch definitions
        'entry_type_label': entry['entry_type_label'],
        'entry_type_name': entry['entry_type_name'],
        'note_types': entry['note_types'],
        'created_at': entry['created_at']
    }

    return render_template('entry_detail.html',
                           project_name=params.get('project_name'),
                           entry=entry_data,
                           entry_singular_label=params.get('entry_singular_label'),
                           entry_plural_label=params.get('entry_plural_label'))

# --- Maintenance Module Routes ---
@app.route('/maintenance')
def maintenance_module_page():
    params = get_system_parameters()
    return render_template('maintenance_module.html',
                           project_name=params.get('project_name'),
                           entry_singular_label=params.get('entry_singular_label'),
                           entry_plural_label=params.get('entry_plural_label'))

@app.route('/manage_entry_types')
def manage_entry_types_page():
    params = get_system_parameters()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, singular_label, plural_label, description, note_types, is_primary FROM EntryType ORDER BY singular_label")
    entry_types = cursor.fetchall()
    return render_template('manage_entry_types.html',
                           project_name=params.get('project_name'),
                           entry_types=[dict(row) for row in entry_types], # Convert to list of dicts for easier Jinja access
                           entry_singular_label=params.get('entry_singular_label'),
                           entry_plural_label=params.get('entry_plural_label'))

@app.route('/manage_relationships')
def manage_relationships_page():
    params = get_system_parameters()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, singular_label, plural_label FROM EntryType ORDER BY singular_label")
    entry_types = cursor.fetchall() # For dropdowns in the form
    return render_template('relationship_definitions.html', # This is the new template name
                           project_name=params.get('project_name'),
                           entry_types=[dict(row) for row in entry_types],
                           entry_singular_label=params.get('entry_singular_label'),
                           entry_plural_label=params.get('entry_plural_label'))

# --- API Endpoints: Entries ---
@app.route('/api/entries', methods=['POST'])
def add_entry():
    data = request.json
    title = data.get('title')
    description = data.get('description')
    entry_type_id = data.get('entry_type_id')

    if not title or not entry_type_id:
        return jsonify({'error': 'Title and Entry Type are required.'}), 400

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO Entry (title, description, entry_type_id, created_at) VALUES (?, ?, ?, ?)",
            (title, description, entry_type_id, datetime.now().isoformat())
        )
        conn.commit()
        return jsonify({'message': 'Entry added successfully!', 'redirect': url_for('entry_detail_page', entry_id=cursor.lastrowid)}), 201
    except Exception as e:
        app.logger.error(f"Error adding entry: {e}", exc_info=True)
        conn.rollback() # Ensure rollback on error
        return jsonify({'error': 'An internal error occurred.'}), 500

@app.route('/api/entries/<int:entry_id>', methods=['PATCH'])
def update_entry(entry_id):
    data = request.json
    conn = get_db()
    cursor = conn.cursor()

    set_clauses = []
    params = []

    if 'title' in data:
        set_clauses.append("title = ?")
        params.append(data['title'])
    if 'description' in data:
        set_clauses.append("description = ?")
        params.append(data['description'])
    if 'entry_type_id' in data:
        set_clauses.append("entry_type_id = ?")
        params.append(data['entry_type_id'])

    if not set_clauses:
        return jsonify({'message': 'No fields provided for update.'}), 200

    params.append(entry_id)
    query = f"UPDATE Entry SET {', '.join(set_clauses)} WHERE id = ?"

    try:
        cursor.execute(query, tuple(params))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({'error': 'Entry not found or no changes made.'}), 404
        return jsonify({'message': 'Entry updated successfully!'}), 200
    except Exception as e:
        app.logger.error(f"Error updating entry {entry_id}: {e}", exc_info=True)
        conn.rollback()
        return jsonify({'error': 'An internal error occurred.'}), 500

@app.route('/api/entries/<int:entry_id>', methods=['DELETE'])
def delete_entry(entry_id):
    conn = get_db()
    cursor = conn.cursor()
    try:
        # Delete related notes
        cursor.execute("DELETE FROM Note WHERE entry_id = ?", (entry_id,))
        # Delete related entry relationships (from either side)
        cursor.execute("DELETE FROM EntryRelationship WHERE entry_id_from = ? OR entry_id_to = ?", (entry_id, entry_id))
        # Finally, delete the entry
        cursor.execute("DELETE FROM Entry WHERE id = ?", (entry_id,))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({'error': 'Entry not found.'}), 404
        return jsonify({'message': 'Entry and its related data deleted successfully!'}), 200
    except Exception as e:
        app.logger.error(f"Error deleting entry {entry_id}: {e}", exc_info=True)
        conn.rollback()
        return jsonify({'error': 'An internal error occurred.'}), 500

# --- API Endpoints: Entry Types ---
@app.route('/api/entry_types', methods=['GET'])
def get_entry_types_api(): # Renamed to avoid clash with manage_entry_types_page's internal use
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, singular_label, plural_label, description, note_types, is_primary FROM EntryType ORDER BY singular_label")
    entry_types_rows = cursor.fetchall()
    entry_types_list = []
    for row in entry_types_rows:
        entry_types_list.append(dict(row))
    return jsonify(entry_types_list)

@app.route('/api/entry_types', methods=['POST'])
def add_entry_type():
    data = request.json
    name = data.get('name')
    singular_label = data.get('singular_label')
    plural_label = data.get('plural_label')
    description = data.get('description')
    note_types = data.get('note_types', 'General')
    is_primary = int(data.get('is_primary', 0))

    if not all([name, singular_label, plural_label]):
        return jsonify({'error': 'Name, singular label, and plural label are required.'}), 400

    conn = get_db()
    cursor = conn.cursor()

    try:
        if is_primary:
            cursor.execute("UPDATE EntryType SET is_primary = 0 WHERE is_primary = 1")

        cursor.execute(
            "INSERT INTO EntryType (name, singular_label, plural_label, description, note_types, is_primary) VALUES (?, ?, ?, ?, ?, ?)",
            (name, singular_label, plural_label, description, note_types, is_primary)
        )
        conn.commit()
        return jsonify({'message': 'Entry type added successfully!', 'id': cursor.lastrowid}), 201
    except sqlite3.IntegrityError:
        conn.rollback()
        return jsonify({'error': f'Entry type with name "{name}" already exists.'}), 409
    except Exception as e:
        app.logger.error(f"Error adding entry type: {e}", exc_info=True)
        conn.rollback()
        return jsonify({'error': 'An internal error occurred.'}), 500

@app.route('/api/entry_types/<int:entry_type_id>', methods=['PATCH'])
def update_entry_type(entry_type_id):
    data = request.json
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM EntryType WHERE id = ?", (entry_type_id,))
    existing_type = cursor.fetchone()
    if not existing_type:
        return jsonify({'error': 'Entry type not found.'}), 404

    set_clauses = []
    params = []

    if 'name' in data:
        set_clauses.append("name = ?")
        params.append(data['name'])
    if 'singular_label' in data:
        set_clauses.append("singular_label = ?")
        params.append(data['singular_label'])
    if 'plural_label' in data:
        set_clauses.append("plural_label = ?")
        params.append(data['plural_label'])
    if 'description' in data:
        set_clauses.append("description = ?")
        params.append(data['description'])
    if 'note_types' in data:
        set_clauses.append("note_types = ?")
        params.append(data['note_types'])

    if 'is_primary' in data:
        is_primary = int(data['is_primary'])
        if is_primary:
            # If this type is being set as primary, unset others
            cursor.execute("UPDATE EntryType SET is_primary = 0 WHERE is_primary = 1 AND id != ?", (entry_type_id,))
        set_clauses.append("is_primary = ?")
        params.append(is_primary)

    if not set_clauses:
        return jsonify({'message': 'No fields provided for update.'}), 200

    params.append(entry_type_id)
    query = f"UPDATE EntryType SET {', '.join(set_clauses)} WHERE id = ?"

    try:
        cursor.execute(query, tuple(params))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({'error': 'Entry type not found or no changes made.'}), 404
        return jsonify({'message': 'Entry type updated successfully!'}), 200
    except sqlite3.IntegrityError:
        conn.rollback()
        return jsonify({'error': 'A relationship definition with that name already exists.'}), 409
    except Exception as e:
        app.logger.error(f"Error updating entry type {entry_type_id}: {e}", exc_info=True)
        conn.rollback()
        return jsonify({'error': 'An internal error occurred.'}), 500

@app.route('/api/entry_types/<int:entry_type_id>', methods=['DELETE'])
def delete_entry_type(entry_type_id):
    conn = get_db()
    cursor = conn.cursor()

    try:
        # Check for dependencies in 'Entry' table
        cursor.execute("SELECT COUNT(*) FROM Entry WHERE entry_type_id = ?", (entry_type_id,))
        entry_count = cursor.fetchone()[0]
        if entry_count > 0:
            return jsonify({'error': f'Cannot delete entry type. {entry_count} entries are linked to it. Please delete linked entries first.'}), 409

        # Check for dependencies in 'RelationshipDefinition' table
        cursor.execute("SELECT COUNT(*) FROM RelationshipDefinition WHERE entry_type_id_from = ? OR entry_type_id_to = ?", (entry_type_id, entry_type_id))
        rel_def_count = cursor.fetchone()[0]
        if rel_def_count > 0:
            return jsonify({'error': f'Cannot delete entry type. {rel_def_count} relationship definitions are linked to it. Please delete linked relationship definitions first.'}), 409

        cursor.execute("DELETE FROM EntryType WHERE id = ?", (entry_type_id,))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({'error': 'Entry type not found.'}), 404
        return jsonify({'message': 'Entry type deleted successfully!'}), 200
    except Exception as e:
        app.logger.error(f"Error deleting entry type {entry_type_id}: {e}", exc_info=True)
        conn.rollback()
        return jsonify({'error': 'An internal error occurred.'}), 500

# --- API Endpoints: Notes ---
@app.route('/api/entries/<int:entry_id>/notes', methods=['POST'])
def add_note_to_entry(entry_id):
    data = request.json
    note_title = data.get('note_title')
    note_text = data.get('note_text')
    note_type = data.get('note_type', 'General')

    if not note_text:
        return jsonify({'message': 'Note content cannot be empty!'}), 400

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO Note (entry_id, note_title, note_text, type, created_at, image_paths) VALUES (?, ?, ?, ?, ?, ?)",
            (entry_id, note_title, note_text, note_type, datetime.now().isoformat(), json.dumps([])) # image_paths always starts as empty list
        )
        conn.commit()
        return jsonify({'message': 'Note added successfully!', 'note_id': cursor.lastrowid}), 201
    except sqlite3.IntegrityError:
        # This occurs if entry_id doesn't exist due to FOREIGN KEY constraint
        conn.rollback()
        return jsonify({'message': 'Entry not found for adding note.'}), 404
    except Exception as e:
        app.logger.error(f"Error adding note to entry {entry_id}: {e}", exc_info=True)
        conn.rollback()
        return jsonify({'message': 'An internal error occurred.'}), 500

@app.route('/api/entries/<int:entry_id>/notes', methods=['GET'])
def get_notes_for_entry(entry_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, entry_id, note_title, note_text, type, created_at, image_paths FROM Note WHERE entry_id = ? ORDER BY created_at DESC", (entry_id,))
    notes = cursor.fetchall()
    return jsonify([_serialize_note(note) for note in notes])

@app.route('/api/notes/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM Note WHERE id = ?", (note_id,))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({'error': 'Note not found.'}), 404
        return jsonify({'message': 'Note deleted successfully!'}), 200
    except Exception as e:
        app.logger.error(f"Error deleting note {note_id}: {e}", exc_info=True)
        conn.rollback()
        return jsonify({'error': 'An internal error occurred.'}), 500

# --- API Endpoints: System Parameters ---
@app.route('/api/system_parameters', methods=['GET'])
def api_get_system_parameters():
    return jsonify(get_system_parameters())

@app.route('/api/system_parameters', methods=['PATCH'])
def api_update_system_parameters():
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    updated_count = 0
    try:
        for param_name, param_value in data.items():
            if param_name in ['project_name', 'entry_singular_label', 'entry_plural_label']:
                cursor.execute(
                    "UPDATE SystemParameters SET parameter_value = ? WHERE parameter_name = ?",
                    (param_value, param_name)
                )
                if cursor.rowcount > 0:
                    updated_count += 1
                else:
                    # If parameter doesn't exist, insert it
                    cursor.execute(
                        "INSERT INTO SystemParameters (parameter_name, parameter_value) VALUES (?, ?)",
                        (param_name, param_value)
                    )
                    updated_count += 1
        conn.commit()
        return jsonify({'message': f'{updated_count} parameters updated successfully!'}), 200
    except Exception as e:
        app.logger.error(f"Error updating system parameters: {e}", exc_info=True)
        conn.rollback()
        return jsonify({'error': 'An internal error occurred.'}), 500

# --- API Endpoints: Relationship Definitions ---
@app.route('/api/relationship_definitions', methods=['GET'])
def api_get_relationship_definitions():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT
            rd.id, rd.name, rd.description,
            rd.entry_type_id_from, et_from.singular_label AS entry_type_from_label,
            rd.entry_type_id_to, et_to.singular_label AS entry_type_to_label,
            rd.cardinality_from, rd.cardinality_to,
            rd.label_from_side, rd.label_to_side,
            rd.allow_quantity_unit, rd.is_active
        FROM RelationshipDefinition rd
        JOIN EntryType et_from ON rd.entry_type_id_from = et_from.id
        JOIN EntryType et_to ON rd.entry_type_id_to = et_to.id
        ORDER BY rd.name
    ''')
    definitions_rows = cursor.fetchall()
    definitions_list = [dict(row) for row in definitions_rows] # Convert rows to dictionaries
    return jsonify(definitions_list)

@app.route('/api/relationship_definitions', methods=['POST'])
def api_create_relationship_definition():
    data = request.get_json()
    name = data.get('name')
    description = data.get('description')
    entry_type_id_from = data.get('entry_type_id_from')
    entry_type_id_to = data.get('entry_type_id_to')
    cardinality_from = data.get('cardinality_from')
    cardinality_to = data.get('cardinality_to')
    label_from_side = data.get('label_from_side')
    label_to_side = data.get('label_to_side')
    allow_quantity_unit = data.get('allow_quantity_unit', False)
    is_active = data.get('is_active', True)

    if not all([name, entry_type_id_from, entry_type_id_to, cardinality_from, cardinality_to, label_from_side, label_to_side]):
        return jsonify({"error": "Missing required fields for relationship definition."}), 400

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO RelationshipDefinition (
                name, description, entry_type_id_from, entry_type_id_to,
                cardinality_from, cardinality_to, label_from_side, label_to_side,
                allow_quantity_unit, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            name, description, entry_type_id_from, entry_type_id_to,
            cardinality_from, cardinality_to, label_from_side, label_to_side,
            int(allow_quantity_unit), int(is_active)
        ))
        conn.commit()
        return jsonify({"message": f'Relationship Definition "{name}" created successfully!', 'id': cursor.lastrowid}), 201
    except sqlite3.IntegrityError as e:
        conn.rollback()
        return jsonify({"error": f'A relationship definition with the name "{name}" already exists or a data integrity issue occurred: {e}'}), 409
    except Exception as e:
        conn.rollback()
        app.logger.error(f"Error creating relationship definition: {e}", exc_info=True)
        return jsonify({"error": f'An error occurred: {e}'}), 500

@app.route('/api/relationship_definitions/<int:definition_id>', methods=['PATCH'])
def api_update_relationship_definition(definition_id):
    data = request.get_json()
    conn = get_db()
    cursor = conn.cursor()

    try:
        set_clauses = []
        update_values = []
        for key, value in data.items():
            if key in [
                'name', 'description', 'entry_type_id_from', 'entry_type_id_to',
                'cardinality_from', 'cardinality_to', 'label_from_side', 'label_to_side',
                'allow_quantity_unit', 'is_active'
            ]:
                set_clauses.append(f"{key} = ?")
                if key in ['allow_quantity_unit', 'is_active']:
                    update_values.append(int(value))
                else:
                    update_values.append(value)

        if not set_clauses:
            return jsonify({"error": "No valid fields provided for update."}), 400

        update_values.append(definition_id)
        cursor.execute(
            f"UPDATE RelationshipDefinition SET {', '.join(set_clauses)} WHERE id = ?",
            tuple(update_values)
        )
        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Relationship Definition not found."}), 404
        return jsonify({"message": "Relationship Definition updated successfully!"}), 200
    except sqlite3.IntegrityError:
        conn.rollback()
        return jsonify({'error': 'A relationship definition with that name already exists.'}), 409
    except Exception as e:
        conn.rollback()
        app.logger.error(f"Error updating relationship definition {definition_id}: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/relationship_definitions/<int:definition_id>', methods=['DELETE'])
def api_delete_relationship_definition(definition_id):
    conn = get_db()
    cursor = conn.cursor()
    try:
        # Check if any 'EntryRelationship' entries are linked to this definition
        cursor.execute("SELECT COUNT(*) FROM EntryRelationship WHERE definition_id = ?", (definition_id,))
        linked_relationships_count = cursor.fetchone()[0]
        if linked_relationships_count > 0:
            return jsonify({"error": f"Cannot delete relationship definition. {linked_relationships_count} existing entry relationships use this definition. Please delete them first."}), 409

        cursor.execute("DELETE FROM RelationshipDefinition WHERE id = ?", (definition_id,))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({"error": "Relationship Definition not found."}), 404
        return jsonify({"message": "Relationship Definition deleted successfully!"}), 200
    except Exception as e:
        conn.rollback()
        app.logger.error(f"Error deleting relationship definition {definition_id}: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

# --- API Endpoints: Entry Relationships (the actual links between entries) ---
# In app.py
@app.route('/api/entries/<int:entry_id>/relationships', methods=['GET'])
def get_entry_relationships(entry_id):
    conn = get_db()
    cursor = conn.cursor()

    # Fetch relationships where current entry is the 'from' side
    cursor.execute('''
        SELECT
            er.id AS relationship_id,
            er.target_entry_id AS related_entry_id, -- CHANGED FROM entry_id_to
            e_to.title AS related_entry_title,
            rd.label_from_side,
            rd.label_to_side,
            rd.allow_quantity_unit,
            er.quantity,
            er.unit,
            rd.id AS definition_id,
            rd.name AS definition_name,
            rd.cardinality_from,
            rd.cardinality_to
        FROM EntryRelationship er
        JOIN RelationshipDefinition rd ON er.relationship_type = rd.id
        JOIN Entry e_to ON er.target_entry_id = e_to.id -- CHANGED FROM entry_id_to
        WHERE er.source_entry_id = ?
    ''', (entry_id,))
    from_relationships = cursor.fetchall()

    # Fetch relationships where current entry is the 'to' side
    cursor.execute('''
        SELECT
            er.id AS relationship_id,
            er.source_entry_id AS related_entry_id, -- CHANGED FROM entry_id_from
            e_from.title AS related_entry_title,
            rd.label_to_side AS label_from_side, -- The label when viewing from the 'to' side's perspective
            rd.label_from_side AS label_to_side,
            rd.allow_quantity_unit,
            er.quantity,
            er.unit,
            rd.id AS definition_id,
            rd.name AS definition_name,
            rd.cardinality_from,
            rd.cardinality_to
        FROM EntryRelationship er
        JOIN RelationshipDefinition rd ON er.relationship_type = rd.id
        JOIN Entry e_from ON er.source_entry_id = e_from.id -- CHANGED FROM entry_id_from
        WHERE er.target_entry_id = ?
    ''', (entry_id,))
    to_relationships = cursor.fetchall()

    # Combine and format results
    related_entries_data = []

    # Process 'from' relationships
    for row in from_relationships:
        related_entries_data.append({
            'relationship_id': row['relationship_id'],
            'related_entry_id': row['related_entry_id'],
            'related_entry_title': row['related_entry_title'],
            'relationship_label': row['label_from_side'],
            'opposite_relationship_label': row['label_to_side'],
            'allow_quantity_unit': bool(row['allow_quantity_unit']),
            'quantity': row['quantity'],
            'unit': row['unit'],
            'definition_id': row['definition_id'],
            'definition_name': row['definition_name'],
            'cardinality_from': row['cardinality_from'],
            'cardinality_to': row['cardinality_to'],
            'is_inverse': False # Indicates this is a 'from' relationship for the current entry
        })

    # Process 'to' relationships (inverse perspective)
    for row in to_relationships:
        related_entries_data.append({
            'relationship_id': row['relationship_id'],
            'related_entry_id': row['related_entry_id'],
            'related_entry_title': row['related_entry_title'],
            'relationship_label': row['label_from_side'], # label_to_side from definition, but acts as label_from_side for this view
            'opposite_relationship_label': row['label_to_side'], # label_from_side from definition, but acts as label_to_side for this view
            'allow_quantity_unit': bool(row['allow_quantity_unit']),
            'quantity': row['quantity'],
            'unit': row['unit'],
            'definition_id': row['definition_id'],
            'definition_name': row['definition_name'],
            'cardinality_from': row['cardinality_from'], # Original cardinality_from for the definition
            'cardinality_to': row['cardinality_to'], # Original cardinality_to for the definition
            'is_inverse': True # Indicates this is an inverse ('to' side) relationship for the current entry
        })

    return jsonify(related_entries_data)
@app.route('/api/entries/<int:entry_id>/relationships', methods=['POST'])
def add_entry_relationship(entry_id):
    data = request.get_json()
    definition_id = data.get('definition_id')
    related_entry_id = data.get('related_entry_id')
    quantity = data.get('quantity')
    unit = data.get('unit')

    if not all([definition_id, related_entry_id]):
        return jsonify({"error": "Missing relationship definition ID or related entry ID."}), 400

    conn = get_db()
    cursor = conn.cursor()
    try:
        # Check if the relationship definition allows quantity/unit
        cursor.execute("SELECT allow_quantity_unit FROM RelationshipDefinition WHERE id = ?", (definition_id,))
        rel_def = cursor.fetchone()
        if not rel_def:
            return jsonify({"error": "Relationship definition not found."}), 404

        if not rel_def['allow_quantity_unit']:
            quantity = None
            unit = None

        # Check for duplicate relationship (same from, to, and definition)
        cursor.execute(
            "SELECT COUNT(*) FROM EntryRelationship WHERE entry_id_from = ? AND entry_id_to = ? AND definition_id = ?",
            (entry_id, related_entry_id, definition_id)
        )
        if cursor.fetchone()[0] > 0:
            return jsonify({"error": "This specific relationship already exists."}), 409

        cursor.execute(
            "INSERT INTO EntryRelationship (entry_id_from, entry_id_to, definition_id, quantity, unit) VALUES (?, ?, ?, ?, ?)",
            (entry_id, related_entry_id, definition_id, quantity, unit)
        )
        conn.commit()
        return jsonify({"message": "Relationship added successfully!", "relationship_id": cursor.lastrowid}), 201
    except sqlite3.IntegrityError as e:
        conn.rollback()
        # More specific integrity error handling
        if "FOREIGN KEY constraint failed" in str(e):
            return jsonify({"error": "Invalid entry or relationship definition ID."}), 400
        return jsonify({"error": f'An integrity error occurred: {e}'}), 409
    except Exception as e:
        conn.rollback()
        app.logger.error(f"Error adding entry relationship: {e}", exc_info=True)
        return jsonify({"error": f'An internal error occurred: {e}'}), 500

@app.route('/api/relationships/<int:relationship_id>', methods=['DELETE'])
def delete_entry_relationship(relationship_id):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM EntryRelationship WHERE id = ?", (relationship_id,))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({"error": "Relationship not found."}), 404
        return jsonify({"message": "Relationship deleted successfully."}), 200
    except Exception as e:
        conn.rollback()
        app.logger.error(f"Error deleting relationship {relationship_id}: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/search_entries', methods=['GET'])
def search_entries():
    query = request.args.get('q', '').strip()
    entry_type_id = request.args.get('entry_type_id', type=int) # New parameter for filtering
    conn = get_db()
    cursor = conn.cursor()
    results = []

    search_query = "%" + query + "%"
    sql = '''
        SELECT e.id, e.title, et.singular_label AS entry_type_label
        FROM Entry e
        JOIN EntryType et ON e.entry_type_id = et.id
        WHERE e.title LIKE ? OR e.description LIKE ?
    '''
    params = [search_query, search_query]

    if entry_type_id:
        sql += " AND e.entry_type_id = ?"
        params.append(entry_type_id)

    sql += " LIMIT 10" # Limit results for performance

    cursor.execute(sql, tuple(params))
    rows = cursor.fetchall()
    for row in rows:
        results.append({
            'id': row['id'],
            'title': row['title'],
            'entry_type_label': row['entry_type_label']
        })
    return jsonify(results)


# --- Initial Database Setup (for development) ---
if __name__ == '__main__':
    # This block is for direct execution of app.py for development/testing without run.py
    # In a production or Docker setup, a separate entrypoint (like run.py) typically handles this.
    with app.app_context():
        init_db() # Call init_db to set up the database
    app.run(debug=True, host='0.0.0.0', port=5001)