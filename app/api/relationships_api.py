# template_app/app/api/relationships_api.py
from flask import Blueprint, request, jsonify, g, current_app
import sqlite3
import logging
import json
from ..serializers import serialize_relationship_definition, serialize_entry_relationship # Import serializers

# Define a Blueprint for Relationships API
relationships_api_bp = Blueprint('relationships_api', __name__)

# Get a logger for this module
logger = logging.getLogger(__name__)

def get_db():
    if 'db' not in g:
        db_path = current_app.config['DATABASE_PATH']
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
    return g.db

# --- API Endpoints: Relationship Definitions ---
@relationships_api_bp.route('/relationship_definitions', methods=['GET'])
def api_get_relationship_definitions():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT
            rd.id, rd.name, rd.description,
            rd.entry_type_id_from, et_from.singular_label AS entry_type_from_label,
            rd.entry_type_id_to, et_to.singular_label AS entry_type_to_label,
            CASE rd.cardinality_from
                WHEN 'one' THEN 1
                WHEN 'many' THEN -1
                ELSE rd.cardinality_from
            END AS cardinality_from,
            CASE rd.cardinality_to
                WHEN 'one' THEN 1
                WHEN 'many' THEN -1
                ELSE rd.cardinality_to
            END AS cardinality_to,
            rd.label_from_side, rd.label_to_side,
            rd.allow_quantity_unit, rd.is_hierarchical, rd.hierarchy_direction, rd.is_active
        FROM RelationshipDefinition rd
        JOIN EntryType et_from ON rd.entry_type_id_from = et_from.id
        JOIN EntryType et_to ON rd.entry_type_id_to = et_to.id
        ORDER BY rd.name
    ''')
    definitions_rows = cursor.fetchall()
    return jsonify([serialize_relationship_definition(row) for row in definitions_rows])

@relationships_api_bp.route('/relationship_definitions', methods=['POST'])
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
    is_hierarchical = data.get('is_hierarchical', False)
    hierarchy_direction = data.get('hierarchy_direction', 'from_to_child')
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
                allow_quantity_unit, is_hierarchical, hierarchy_direction, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            name, description, entry_type_id_from, entry_type_id_to,
            cardinality_from, cardinality_to, label_from_side, label_to_side,
            int(allow_quantity_unit), int(is_hierarchical), hierarchy_direction, int(is_active)
        ))
        conn.commit()
        return jsonify({"message": f'Relationship Definition "{name}" created successfully!', 'id': cursor.lastrowid}), 201
    except sqlite3.IntegrityError as e:
        conn.rollback()
        # Check for specific unique constraint violation for 'name'
        if "UNIQUE constraint failed: RelationshipDefinition.name" in str(e):
            return jsonify({"error": f'A relationship definition with the name "{name}" already exists.'}), 409
        return jsonify({"error": f'A data integrity issue occurred: {e}'}), 409
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating relationship definition: {e}", exc_info=True)
        return jsonify({"error": f'An error occurred: {e}'}), 500

@relationships_api_bp.route('/relationship_definitions/<int:definition_id>', methods=['PATCH'])
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
                'allow_quantity_unit', 'is_hierarchical', 'hierarchy_direction', 'is_active'
            ]:
                set_clauses.append(f"{key} = ?")
                if key in ['allow_quantity_unit', 'is_hierarchical', 'is_active']:
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
            return jsonify({"error": "Relationship Definition not found or no changes made."}), 404
        return jsonify({"message": "Relationship Definition updated successfully!"}), 200
    except sqlite3.IntegrityError:
        conn.rollback()
        return jsonify({'error': 'A relationship definition with that name already exists.'}), 409
    except Exception as e:
        conn.rollback()
        logger.error(f"Error updating relationship definition {definition_id}: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@relationships_api_bp.route('/relationship_definitions/<int:definition_id>', methods=['DELETE'])
def api_delete_relationship_definition(definition_id):
    conn = get_db()
    cursor = conn.cursor()
    try:
        # Check if any 'EntryRelationship' entries are linked to this definition
        cursor.execute("SELECT COUNT(*) FROM EntryRelationship WHERE relationship_type = ?", (definition_id,))
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
        logger.error(f"Error deleting relationship definition {definition_id}: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

# --- API Endpoints: Entry Relationships (the actual links between entries) ---
@relationships_api_bp.route('/entries/<int:entry_id>/relationships', methods=['GET'])
def get_entry_relationships(entry_id):
    conn = get_db()
    cursor = conn.cursor()

    related_entries_data = []
    
    # Get current entry title
    cursor.execute('SELECT title FROM Entry WHERE id = ?', (entry_id,))
    current_entry = cursor.fetchone()
    current_entry_title = current_entry['title'] if current_entry else str(entry_id)

    # Fetch relationships where current entry is the 'source' side
    cursor.execute('''
        SELECT
            er.id AS relationship_id,
            er.source_entry_id,
            ? AS source_entry_title,
            er.target_entry_id AS related_entry_id,
            e_to.title AS related_entry_title,
            er.target_entry_id,
            e_to.title AS target_entry_title,
            rd.id AS definition_id,
            rd.name AS definition_name,
            rd.label_from_side,
            rd.label_to_side,
            rd.cardinality_from,
            rd.cardinality_to,
            rd.allow_quantity_unit,
            er.quantity,
            er.unit,
            e_to.status AS related_entry_status,
            es.color AS related_entry_status_color,
            es.category AS related_entry_status_category
        FROM EntryRelationship er
        JOIN RelationshipDefinition rd ON er.relationship_type = rd.id
        JOIN Entry e_to ON er.target_entry_id = e_to.id
        LEFT JOIN EntryState es ON e_to.status = es.name AND e_to.entry_type_id = es.entry_type_id
        WHERE er.source_entry_id = ?
        ORDER BY rd.name, e_to.title
    ''', (current_entry_title, entry_id))
    from_relationships = cursor.fetchall()
    related_entries_data.extend([serialize_entry_relationship(row, is_inverse=False) for row in from_relationships])

    # Fetch relationships where current entry is the 'target' side
    cursor.execute('''
        SELECT
            er.id AS relationship_id,
            er.source_entry_id AS related_entry_id,
            e_from.title AS related_entry_title,
            er.source_entry_id,
            e_from.title AS source_entry_title,
            er.target_entry_id,
            ? AS target_entry_title,
            rd.id AS definition_id,
            rd.name AS definition_name,
            rd.label_from_side,
            rd.label_to_side,
            rd.cardinality_from,
            rd.cardinality_to,
            rd.allow_quantity_unit,
            er.quantity,
            er.unit,
            e_from.status AS related_entry_status,
            es.color AS related_entry_status_color,
            es.category AS related_entry_status_category
        FROM EntryRelationship er
        JOIN RelationshipDefinition rd ON er.relationship_type = rd.id
        JOIN Entry e_from ON er.source_entry_id = e_from.id
        LEFT JOIN EntryState es ON e_from.status = es.name AND e_from.entry_type_id = es.entry_type_id
        WHERE er.target_entry_id = ?
        ORDER BY rd.name, e_from.title
    ''', (current_entry_title, entry_id))
    to_relationships = cursor.fetchall()
    related_entries_data.extend([serialize_entry_relationship(row, is_inverse=True) for row in to_relationships])

    return jsonify(related_entries_data)

@relationships_api_bp.route('/entries/<int:entry_id>/relationships', methods=['POST'])
def add_entry_relationship(entry_id):
    data = request.get_json()
    definition_id = data.get('definition_id')
    related_entry_id = data.get('related_entry_id')
    quantity = data.get('quantity')
    unit = data.get('unit')

    # Ensure source_entry_id is the entry_id from the URL
    source_entry_id = entry_id
    target_entry_id = related_entry_id

    if not all([definition_id, target_entry_id]):
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
        else:
            # Convert quantity to float if provided and allowed
            if quantity is not None:
                try:
                    quantity = float(quantity)
                except ValueError:
                    return jsonify({"error": "Quantity must be a valid number."}), 400

        # Prevent self-referencing relationships unless explicitly allowed by design
        if source_entry_id == target_entry_id:
             return jsonify({"error": "Cannot create a relationship to the same entry."}), 400

        # Check for existing relationship in BOTH directions (same source, target, and definition)
        # A relationship between Entry A and Entry B should only exist once, regardless of direction
        cursor.execute(
            """SELECT COUNT(*) FROM EntryRelationship 
               WHERE relationship_type = ? 
               AND ((source_entry_id = ? AND target_entry_id = ?) 
                    OR (source_entry_id = ? AND target_entry_id = ?))""",
            (definition_id, source_entry_id, target_entry_id, target_entry_id, source_entry_id)
        )
        if cursor.fetchone()[0] > 0:
            return jsonify({"error": "This relationship already exists (possibly in the opposite direction)."}), 409

        # Server-side cardinality validation disabled - handled by frontend
        # The frontend already prevents adding relationships when cardinality limits are reached
        # by disabling the "Add New" and "Add Existing" buttons appropriately

        cursor.execute(
            "INSERT INTO EntryRelationship (source_entry_id, target_entry_id, relationship_type, quantity, unit) VALUES (?, ?, ?, ?, ?)",
            (source_entry_id, target_entry_id, definition_id, quantity, unit)
        )
        conn.commit()
        return jsonify({"message": "Relationship added successfully!", "relationship_id": cursor.lastrowid}), 201
    except sqlite3.IntegrityError as e:
        conn.rollback()
        if "FOREIGN KEY constraint failed" in str(e):
            return jsonify({"error": "Invalid source entry, target entry, or relationship definition ID."}), 400
        return jsonify({"error": f'An integrity error occurred: {e}'}), 409
    except Exception as e:
        conn.rollback()
        logger.error(f"Error adding entry relationship: {e}", exc_info=True)
        return jsonify({"error": f'An internal error occurred: {e}'}), 500

@relationships_api_bp.route('/relationships/<int:relationship_id>', methods=['DELETE'])
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
        logger.error(f"Error deleting relationship {relationship_id}: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@relationships_api_bp.route('/entries/<int:entry_id>/relationships/new', methods=['POST'])
def add_new_entry_relationship(entry_id):
    data = request.get_json()
    definition_id = data.get('definition_id')
    new_entry_title = data.get('name', '').strip()  # Frontend sends 'name', we use it as 'title'
    new_entry_description = data.get('description', '').strip()
    quantity = data.get('quantity')
    unit = data.get('unit')

    if not definition_id or not new_entry_title:
        return jsonify({"error": "Missing relationship definition ID or new entry title."}), 400

    conn = get_db()
    cursor = conn.cursor()
    try:
        # Get the relationship definition to find the target entry type
        cursor.execute('''
            SELECT entry_type_id_to, allow_quantity_unit 
            FROM RelationshipDefinition 
            WHERE id = ?
        ''', (definition_id,))
        rel_def = cursor.fetchone()
        
        if not rel_def:
            return jsonify({"error": "Relationship definition not found."}), 404
        
        target_entry_type_id = rel_def['entry_type_id_to']
        allow_quantity_unit = rel_def['allow_quantity_unit']
        
        # Clear quantity/unit if not allowed
        if not allow_quantity_unit:
            quantity = None
            unit = None
        else:
            # Convert quantity to float if provided
            if quantity is not None and quantity != '':
                try:
                    quantity = float(quantity)
                except (ValueError, TypeError):
                    return jsonify({"error": "Quantity must be a valid number."}), 400
            else:
                quantity = None

        # Create the new entry with the correct entry_type_id
        cursor.execute('''
            INSERT INTO Entry (title, description, entry_type_id, created_at) 
            VALUES (?, ?, ?, datetime('now'))
        ''', (new_entry_title, new_entry_description, target_entry_type_id))
        new_entry_id = cursor.lastrowid

        # Add the relationship
        cursor.execute('''
            INSERT INTO EntryRelationship (source_entry_id, target_entry_id, relationship_type, quantity, unit)
            VALUES (?, ?, ?, ?, ?)
        ''', (entry_id, new_entry_id, definition_id, quantity, unit))
        conn.commit()

        return jsonify({"message": "New entry and relationship added successfully!", "new_entry_id": new_entry_id}), 201
    except sqlite3.IntegrityError as e:
        conn.rollback()
        return jsonify({"error": f"An integrity error occurred: {e}"}), 409
    except Exception as e:
        conn.rollback()
        logger.error(f"Error adding new entry and relationship: {e}", exc_info=True)
        return jsonify({"error": f"An internal error occurred: {e}"}), 500


@relationships_api_bp.route('/relationships/<int:relationship_id>', methods=['PUT'])
def update_relationship_quantity_unit(relationship_id):
    """Update the quantity and unit for a specific relationship"""
    data = request.get_json()
    quantity = data.get('quantity')
    unit = data.get('unit')

    conn = get_db()
    cursor = conn.cursor()
    try:
        # Check if relationship exists
        cursor.execute("SELECT id FROM EntryRelationship WHERE id = ?", (relationship_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Relationship not found."}), 404

        # Convert quantity to float if provided
        if quantity is not None and quantity != '':
            try:
                quantity = float(quantity)
            except (ValueError, TypeError):
                return jsonify({"error": "Quantity must be a valid number."}), 400
        else:
            quantity = None

        # Clean up unit string
        if unit is not None:
            unit = unit.strip()
            if unit == '':
                unit = None

        # Update the relationship
        cursor.execute('''
            UPDATE EntryRelationship 
            SET quantity = ?, unit = ? 
            WHERE id = ?
        ''', (quantity, unit, relationship_id))
        
        conn.commit()
        
        return jsonify({
            "message": "Relationship quantity and unit updated successfully!",
            "relationship_id": relationship_id,
            "quantity": quantity,
            "unit": unit
        }), 200
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error updating relationship quantity/unit: {e}", exc_info=True)
        return jsonify({"error": f"An internal error occurred: {e}"}), 500


@relationships_api_bp.route('/entries/<int:entry_id>/relationships/incoming', methods=['GET'])
def get_incoming_relationships(entry_id):
    """Get all relationships where this entry is the target (incoming relationships)"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Get the current entry's title for the query
        cursor.execute("SELECT title FROM Entry WHERE id = ?", (entry_id,))
        entry_row = cursor.fetchone()
        if not entry_row:
            return jsonify({"error": "Entry not found."}), 404
        current_entry_title = entry_row['title']
        
        # Query relationships where current entry is the target
        cursor.execute('''
            SELECT
                er.id AS relationship_id,
                er.source_entry_id AS related_entry_id,
                e_from.title AS related_entry_title,
                e_from.status AS related_entry_status,
                et_from.id AS related_entry_type_id,
                et_from.singular_label AS related_entry_type_label,
                rd.id AS definition_id,
                rd.name AS definition_name,
                rd.label_from_side,
                rd.label_to_side,
                er.quantity,
                er.unit
            FROM EntryRelationship er
            JOIN RelationshipDefinition rd ON er.relationship_type = rd.id
            JOIN Entry e_from ON er.source_entry_id = e_from.id
            JOIN EntryType et_from ON e_from.entry_type_id = et_from.id
            WHERE er.target_entry_id = ?
            ORDER BY rd.name, e_from.title
        ''', (entry_id,))
        
        relationships = []
        for row in cursor.fetchall():
            relationships.append({
                'id': row['relationship_id'],
                'related_entry_id': row['related_entry_id'],
                'related_entry_title': row['related_entry_title'],
                'related_entry_status': row['related_entry_status'],
                'related_entry_type': {
                    'id': row['related_entry_type_id'],
                    'label': row['related_entry_type_label'],
                    'icon': 'fas fa-link',  # Default icon
                    'color': '#6c757d'  # Default color
                },
                'relationship_type': row['label_to_side'],  # Use "to" label since we're on the receiving end
                'definition_name': row['definition_name'],
                'quantity': row['quantity'],
                'unit': row['unit'],
                'is_incoming': True
            })
        
        return jsonify({'relationships': relationships}), 200
        
    except Exception as e:
        logger.error(f"Error fetching incoming relationships: {e}", exc_info=True)
        return jsonify({"error": f"An internal error occurred: {e}"}), 500


@relationships_api_bp.route('/entries/<int:entry_id>/relationships/grouped', methods=['GET'])
def get_grouped_relationships(entry_id):
    """Get relationships grouped by type (for outgoing relationships)"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Get current entry title
        cursor.execute("SELECT title FROM Entry WHERE id = ?", (entry_id,))
        entry_row = cursor.fetchone()
        if not entry_row:
            return jsonify({"error": "Entry not found."}), 404
        
        # Query outgoing relationships
        cursor.execute('''
            SELECT
                er.id AS relationship_id,
                er.target_entry_id AS related_entry_id,
                e_to.title AS related_entry_title,
                e_to.status AS related_entry_status,
                et_to.id AS related_entry_type_id,
                et_to.singular_label AS related_entry_type_label,
                rd.id AS definition_id,
                rd.name AS definition_name,
                rd.label_from_side AS relationship_type,
                er.quantity,
                er.unit
            FROM EntryRelationship er
            JOIN RelationshipDefinition rd ON er.relationship_type = rd.id
            JOIN Entry e_to ON er.target_entry_id = e_to.id
            JOIN EntryType et_to ON e_to.entry_type_id = et_to.id
            WHERE er.source_entry_id = ?
            ORDER BY rd.name, e_to.title
        ''', (entry_id,))
        
        # Group by relationship type
        grouped = {}
        for row in cursor.fetchall():
            rel_type = row['relationship_type']
            if rel_type not in grouped:
                grouped[rel_type] = []
            
            grouped[rel_type].append({
                'id': row['relationship_id'],
                'related_entry_id': row['related_entry_id'],
                'related_entry_title': row['related_entry_title'],
                'related_entry_status': row['related_entry_status'],
                'related_entry_type': {
                    'id': row['related_entry_type_id'],
                    'label': row['related_entry_type_label'],
                    'icon': 'fas fa-link',  # Default icon
                    'color': '#6c757d'  # Default color
                },
                'definition_name': row['definition_name'],
                'quantity': row['quantity'],
                'unit': row['unit']
            })
        
        return jsonify({'grouped': grouped}), 200
        
    except Exception as e:
        logger.error(f"Error fetching grouped relationships: {e}", exc_info=True)
        return jsonify({"error": f"An internal error occurred: {e}"}), 500


@relationships_api_bp.route('/entries/<int:entry_id>/relationships/hierarchy', methods=['GET'])
def get_relationship_hierarchy(entry_id):
    """Get direct lineage hierarchy: ancestors up, current entry, descendants down (no siblings), grouped by relationship type"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        max_depth = request.args.get('max_depth', 10, type=int)
        
        # First check if there are any hierarchical relationships for this entry
        cursor.execute('''
            SELECT COUNT(*) as count
            FROM EntryRelationship er
            JOIN RelationshipDefinition rd ON er.relationship_type = rd.id
            WHERE rd.is_hierarchical = 1
            AND (er.source_entry_id = ? OR er.target_entry_id = ?)
        ''', (entry_id, entry_id))
        
        hierarchical_count = cursor.fetchone()['count']
        
        if hierarchical_count == 0:
            return jsonify({
                'hierarchy': [],
                'target_entry_id': entry_id,
                'message': 'No hierarchical relationships found. Please mark relationship definitions as hierarchical in the Relationship Definitions settings.'
            }), 200
        
        def get_entry_details(entry_id):
            """Get entry details"""
            cursor.execute('''
                SELECT e.id, e.title, e.status, et.singular_label
                FROM Entry e
                JOIN EntryType et ON e.entry_type_id = et.id
                WHERE e.id = ?
            ''', (entry_id,))
            return cursor.fetchone()
        
        def get_parents_by_relationship(child_id, relationship_type_id=None):
            """Get all parent entries for a given child, optionally filtered by relationship type"""
            query = '''
                SELECT DISTINCT 
                    CASE 
                        WHEN rd.hierarchy_direction = 'from_to_child' THEN er.source_entry_id
                        WHEN rd.hierarchy_direction = 'to_from_child' THEN er.target_entry_id
                    END as parent_id,
                    rd.id as relationship_type_id,
                    rd.name as relationship_type_name,
                    CASE 
                        WHEN rd.hierarchy_direction = 'from_to_child' THEN rd.label_from_side
                        WHEN rd.hierarchy_direction = 'to_from_child' THEN rd.label_to_side
                    END as relationship_label
                FROM EntryRelationship er
                JOIN RelationshipDefinition rd ON er.relationship_type = rd.id
                WHERE rd.is_hierarchical = 1
                AND (
                    (rd.hierarchy_direction = 'from_to_child' AND er.target_entry_id = ?)
                    OR (rd.hierarchy_direction = 'to_from_child' AND er.source_entry_id = ?)
                )
            '''
            params = [child_id, child_id]
            
            if relationship_type_id:
                query += ' AND rd.id = ?'
                params.append(relationship_type_id)
            
            cursor.execute(query, params)
            return cursor.fetchall()
        
        def get_children_by_relationship(parent_id, relationship_type_id=None):
            """Get all child entries for a given parent, optionally filtered by relationship type"""
            query = '''
                SELECT 
                    er.id as relationship_id,
                    CASE 
                        WHEN rd.hierarchy_direction = 'from_to_child' THEN er.target_entry_id
                        WHEN rd.hierarchy_direction = 'to_from_child' THEN er.source_entry_id
                    END as child_id,
                    rd.id as relationship_type_id,
                    CASE 
                        WHEN rd.hierarchy_direction = 'from_to_child' THEN rd.label_from_side
                        WHEN rd.hierarchy_direction = 'to_from_child' THEN rd.label_to_side
                    END as relationship_label
                FROM EntryRelationship er
                JOIN RelationshipDefinition rd ON er.relationship_type = rd.id
                WHERE rd.is_hierarchical = 1
                AND (
                    (rd.hierarchy_direction = 'from_to_child' AND er.source_entry_id = ?)
                    OR (rd.hierarchy_direction = 'to_from_child' AND er.target_entry_id = ?)
                )
            '''
            params = [parent_id, parent_id]
            
            if relationship_type_id:
                query += ' AND rd.id = ?'
                params.append(relationship_type_id)
            
            query += ' ORDER BY child_id'
            
            cursor.execute(query, params)
            return cursor.fetchall()
        
        def get_all_hierarchical_parents(child_id):
            """Get ALL parents from ANY hierarchical relationship type"""
            query = '''
                SELECT 
                    er.id as relationship_id,
                    CASE 
                        WHEN rd.hierarchy_direction = 'from_to_child' THEN er.source_entry_id
                        WHEN rd.hierarchy_direction = 'to_from_child' THEN er.target_entry_id
                    END as parent_id,
                    rd.id as relationship_type_id,
                    rd.name as relationship_type_name,
                    CASE 
                        WHEN rd.hierarchy_direction = 'from_to_child' THEN rd.label_to_side
                        WHEN rd.hierarchy_direction = 'to_from_child' THEN rd.label_to_side
                    END as relationship_label
                FROM EntryRelationship er
                JOIN RelationshipDefinition rd ON er.relationship_type = rd.id
                WHERE rd.is_hierarchical = 1
                AND (
                    (rd.hierarchy_direction = 'from_to_child' AND er.target_entry_id = ?)
                    OR (rd.hierarchy_direction = 'to_from_child' AND er.source_entry_id = ?)
                )
                ORDER BY rd.name, parent_id
            '''
            cursor.execute(query, [child_id, child_id])
            return cursor.fetchall()
        
        def get_all_hierarchical_children(parent_id):
            """Get ALL children from ANY hierarchical relationship type"""
            query = '''
                SELECT 
                    er.id as relationship_id,
                    CASE 
                        WHEN rd.hierarchy_direction = 'from_to_child' THEN er.target_entry_id
                        WHEN rd.hierarchy_direction = 'to_from_child' THEN er.source_entry_id
                    END as child_id,
                    rd.id as relationship_type_id,
                    rd.name as relationship_type_name,
                    CASE 
                        WHEN rd.hierarchy_direction = 'from_to_child' THEN rd.label_from_side
                        WHEN rd.hierarchy_direction = 'to_from_child' THEN rd.label_from_side
                    END as relationship_label
                FROM EntryRelationship er
                JOIN RelationshipDefinition rd ON er.relationship_type = rd.id
                WHERE rd.is_hierarchical = 1
                AND (
                    (rd.hierarchy_direction = 'from_to_child' AND er.source_entry_id = ?)
                    OR (rd.hierarchy_direction = 'to_from_child' AND er.target_entry_id = ?)
                )
                ORDER BY rd.name, child_id
            '''
            cursor.execute(query, [parent_id, parent_id])
            return cursor.fetchall()
        
        def build_lineage_for_relationship_type(target_id, relationship_type_id, relationship_type_name, depth=0, visited=None):
            """
            Build a lineage tree for a specific relationship type
            Shows: ancestors → target → descendants (no siblings at any level)
            """
            if visited is None:
                visited = set()
            
            # Find the root ancestor for this relationship type
            def find_root_ancestor(entry_id, rel_type_id, visited_roots=None):
                """Recursively find the topmost ancestor for this relationship type"""
                if visited_roots is None:
                    visited_roots = set()
                
                if entry_id in visited_roots:
                    return entry_id
                
                visited_roots.add(entry_id)
                parents = get_parents_by_relationship(entry_id, rel_type_id)
                
                if not parents:
                    return entry_id  # This is the root
                
                # Follow the first parent up (could be multiple, but we just need one path to root)
                return find_root_ancestor(parents[0]['parent_id'], rel_type_id, visited_roots)
            
            # Get entry type for filtering
            def get_entry_type(entry_id):
                """Get the entry type ID for an entry"""
                entry = get_entry_details(entry_id)
                if entry:
                    cursor.execute('SELECT entry_type_id FROM Entry WHERE id = ?', (entry_id,))
                    result = cursor.fetchone()
                    return result['entry_type_id'] if result else None
                return None
            
            # Build descendants only (follow children downward, never back up to parents)
            def build_descendants_only(current_id, root_entry_type, depth=0, node_visited=None):
                """Build tree of descendants from ALL hierarchical relationships - stop when we encounter same entry type as root (siblings)"""
                if node_visited is None:
                    node_visited = set()
                
                if depth >= max_depth or current_id in node_visited:
                    return None
                
                node_visited.add(current_id)
                
                entry = get_entry_details(current_id)
                if not entry:
                    return None
                
                node = {
                    'id': entry['id'],
                    'title': entry['title'],
                    'status': entry['status'],
                    'entry_type': {
                        'label': entry['singular_label'],
                        'icon': 'fas fa-link',
                        'color': '#6c757d'
                    },
                    'is_target': False,
                    'children': []
                }
                
                # Get ALL hierarchical children (from any relationship type)
                children = get_all_hierarchical_children(current_id)
                
                # Only recurse into children that are NOT the same entry type as the root
                # (to avoid following sibling connections through shared resources)
                for child_rel in children:
                    child_id = child_rel['child_id']
                    if child_id and child_id not in node_visited:
                        child_entry_type = get_entry_type(child_id)
                        
                        # Skip if child has same entry type as root (these are siblings)
                        if child_entry_type != root_entry_type:
                            child_node = build_descendants_only(child_id, root_entry_type, depth + 1, node_visited.copy())
                            if child_node:
                                child_node['relationship_id'] = child_rel['relationship_id']
                                child_node['relationship_type'] = child_rel['relationship_label']
                                node['children'].append(child_node)
                
                return node
            
            # Build the tree from a specific node
            def build_node(current_id, target_id, rel_type_id, depth=0, node_visited=None):
                """Build a single node and recursively build descendants"""
                if node_visited is None:
                    node_visited = set()
                
                if depth >= max_depth or current_id in node_visited:
                    return None
                
                node_visited.add(current_id)
                
                entry = get_entry_details(current_id)
                if not entry:
                    return None
                
                is_target = (current_id == target_id)
                
                node = {
                    'id': entry['id'],
                    'title': entry['title'],
                    'status': entry['status'],
                    'entry_type': {
                        'label': entry['singular_label'],
                        'icon': 'fas fa-link',
                        'color': '#6c757d'
                    },
                    'is_target': is_target,
                    'direction': 'current' if is_target else 'ancestor',  # Will be 'ancestor' or 'descendant' or 'current'
                    'children': []
                }
                
                # Get all children
                children = get_children_by_relationship(current_id, rel_type_id)
                
                if is_target:
                    # AT TARGET: Show ONLY direct children from THIS relationship type (no recursion, no grandchildren)
                    for child_rel in children:
                        child_id = child_rel['child_id']
                        if child_id and child_id not in node_visited:
                            # Build simple child node - NO recursion, NO grandchildren
                            child_entry = get_entry_details(child_id)
                            if child_entry:
                                child_node = {
                                    'id': child_entry['id'],
                                    'title': child_entry['title'],
                                    'status': child_entry['status'],
                                    'entry_type': {
                                        'label': child_entry['singular_label'],
                                        'icon': 'fas fa-link',
                                        'color': '#6c757d'
                                    },
                                    'is_target': False,
                                    'direction': 'descendant',  # This is a child of the target
                                    'relationship_id': child_rel['relationship_id'],
                                    'relationship_type': child_rel['relationship_label'],
                                    'children': []  # NO grandchildren - keep it simple
                                }
                                node['children'].append(child_node)
                else:
                    # NOT TARGET: We must be an ancestor (above target)
                    # Only show the ONE child that leads to target (no siblings)
                    for child_rel in children:
                        child_id = child_rel['child_id']
                        if child_id and child_id not in node_visited:
                            # Check if this child is on the path to target
                            if child_id == target_id or is_on_path_to_target(child_id, target_id, rel_type_id, node_visited.copy()):
                                # This child leads to target, include it
                                child_node = build_node(child_id, target_id, rel_type_id, depth + 1, node_visited.copy())
                                if child_node:
                                    child_node['relationship_id'] = child_rel['relationship_id']
                                    child_node['relationship_type'] = child_rel['relationship_label']
                                    node['children'].append(child_node)
                                    break  # Only show ONE child (the path to target), no siblings
                
                return node
            
            def is_on_path_to_target(current_id, target_id, rel_type_id, path_visited=None):
                """Check if current_id has target_id as a descendant in this relationship type"""
                if path_visited is None:
                    path_visited = set()
                
                if current_id == target_id:
                    return True
                
                if current_id in path_visited:
                    return False
                
                path_visited.add(current_id)
                
                children = get_children_by_relationship(current_id, rel_type_id)
                for child_rel in children:
                    child_id = child_rel['child_id']
                    if child_id and is_on_path_to_target(child_id, target_id, rel_type_id, path_visited):
                        return True
                
                return False
            
            # Find root and build tree
            root_id = find_root_ancestor(target_id, relationship_type_id)
            tree = build_node(root_id, target_id, relationship_type_id, 0)
            
            # Add relationship type metadata to the root
            if tree:
                tree['relationship_type_name'] = relationship_type_name
                tree['relationship_type_id'] = relationship_type_id
            
            return tree
        
        # Build a single unified hierarchy tree combining all hierarchical relationships
        def find_root_ancestors(start_id, visited=None):
            """Find all root ancestors (entries with no parents)"""
            if visited is None:
                visited = set()
            
            if start_id in visited:
                return []
            
            visited.add(start_id)
            
            parents = get_all_hierarchical_parents(start_id)
            
            if not parents:
                # This is a root - no parents
                return [start_id]
            
            # Recursively find roots from all parents
            roots = []
            for parent_rel in parents:
                parent_id = parent_rel['parent_id']
                if parent_id:
                    parent_roots = find_root_ancestors(parent_id, visited.copy())
                    roots.extend(parent_roots)
            
            return roots
        
        def build_tree_from_node(current_id, target_id, visited=None):
            """Build tree starting from current node, going down toward and through target"""
            if visited is None:
                visited = set()
            
            if current_id in visited:
                return None
            
            visited.add(current_id)
            
            entry = get_entry_details(current_id)
            if not entry:
                return None
            
            is_target = (current_id == target_id)
            
            node = {
                'id': entry['id'],
                'title': entry['title'],
                'status': entry['status'],
                'entry_type': {
                    'label': entry['singular_label'],
                    'icon': 'fas fa-link',
                    'color': '#6c757d'
                },
                'is_target': is_target,
                'direction': 'current' if is_target else ('ancestor' if not is_target else 'unknown'),
                'children': []
            }
            
            # Get ALL hierarchical children
            all_children = get_all_hierarchical_children(current_id)
            
            if is_target:
                # TARGET ENTRY: Show ALL children with their grandchildren
                for child_rel in all_children:
                    child_id = child_rel['child_id']
                    if child_id and child_id not in visited:
                        child_entry = get_entry_details(child_id)
                        if child_entry:
                            child_node = {
                                'id': child_entry['id'],
                                'title': child_entry['title'],
                                'status': child_entry['status'],
                                'entry_type': {
                                    'label': child_entry['singular_label'],
                                    'icon': 'fas fa-link',
                                    'color': '#6c757d'
                                },
                                'is_target': False,
                                'direction': 'descendant',
                                'relationship_id': child_rel['relationship_id'],
                                'relationship_type': child_rel['relationship_label'],
                                'children': []
                            }
                            
                            # Get grandchildren (children of this child)
                            grandchildren = get_all_hierarchical_children(child_id)
                            for grandchild_rel in grandchildren:
                                grandchild_id = grandchild_rel['child_id']
                                if grandchild_id and grandchild_id not in visited and grandchild_id != target_id:
                                    grandchild_entry = get_entry_details(grandchild_id)
                                    if grandchild_entry:
                                        grandchild_node = {
                                            'id': grandchild_entry['id'],
                                            'title': grandchild_entry['title'],
                                            'status': grandchild_entry['status'],
                                            'entry_type': {
                                                'label': grandchild_entry['singular_label'],
                                                'icon': 'fas fa-link',
                                                'color': '#6c757d'
                                            },
                                            'is_target': False,
                                            'direction': 'descendant',
                                            'relationship_id': grandchild_rel['relationship_id'],
                                            'relationship_type': grandchild_rel['relationship_label'],
                                            'children': []
                                        }
                                        child_node['children'].append(grandchild_node)
                            
                            node['children'].append(child_node)
            else:
                # ANCESTOR ENTRY: Only show the child that leads to target
                for child_rel in all_children:
                    child_id = child_rel['child_id']
                    if child_id and child_id not in visited:
                        # Check if this child is the target or leads to target
                        if child_id == target_id or is_ancestor_of(child_id, target_id, visited.copy()):
                            child_node = build_tree_from_node(child_id, target_id, visited.copy())
                            if child_node:
                                child_node['relationship_id'] = child_rel['relationship_id']
                                child_node['relationship_type'] = child_rel['relationship_label']
                                node['children'].append(child_node)
                                break  # Only show ONE path to target
            
            return node
        
        def is_ancestor_of(potential_ancestor_id, target_id, checked=None):
            """Check if potential_ancestor_id is an ancestor of target_id"""
            if checked is None:
                checked = set()
            
            if potential_ancestor_id == target_id:
                return True
            
            if potential_ancestor_id in checked:
                return False
            
            checked.add(potential_ancestor_id)
            
            children = get_all_hierarchical_children(potential_ancestor_id)
            for child_rel in children:
                child_id = child_rel['child_id']
                if child_id and is_ancestor_of(child_id, target_id, checked):
                    return True
            
            return False
        
        # Find root ancestors and build tree from each
        root_ids = find_root_ancestors(entry_id)
        
        if root_ids:
            # Build from the first root (or you could build from all roots)
            unified_tree = build_tree_from_node(root_ids[0], entry_id)
        else:
            # No roots found, start from entry itself
            unified_tree = build_tree_from_node(entry_id, entry_id)
        
        return jsonify({
            'hierarchy': [unified_tree] if unified_tree else [],
            'target_entry_id': entry_id
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching relationship hierarchy: {e}", exc_info=True)
        return jsonify({"error": f"An internal error occurred: {e}"}), 500


@relationships_api_bp.route('/relationship_filter_preferences', methods=['GET'])
def get_relationship_filter_preferences():
    """Get all relationship filter preferences"""
    try:
        from ..db import get_user_preference
        preferences_json = get_user_preference('relationship_filters', '{}')
        preferences_dict = json.loads(preferences_json) if preferences_json else {}
        
        # Convert dict to array format expected by frontend
        preferences_array = []
        for def_id, pref_data in preferences_dict.items():
            preferences_array.append({
                'relationship_definition_id': int(def_id),
                'status_category': pref_data.get('status_category', ''),
                'specific_state': pref_data.get('specific_state', '')
            })
        
        return jsonify(preferences_array), 200
    except Exception as e:
        logger.error(f"Error getting relationship filter preferences: {e}", exc_info=True)
        return jsonify({"error": f"An internal error occurred: {e}"}), 500


@relationships_api_bp.route('/relationship_filter_preferences', methods=['POST'])
def save_relationship_filter_preference():
    """Save a relationship filter preference for a specific definition"""
    try:
        data = request.get_json()
        # Accept both 'definition_id' and 'relationship_definition_id' for compatibility
        definition_id = data.get('relationship_definition_id') or data.get('definition_id')
        status_category = data.get('status_category', '')
        specific_state = data.get('specific_state', '')
        
        if not definition_id:
            return jsonify({'success': False, 'error': 'relationship_definition_id is required'}), 400
        
        from ..db import get_user_preference, set_user_preference
        
        # Get existing preferences
        preferences_json = get_user_preference('relationship_filters', '{}')
        preferences = json.loads(preferences_json) if preferences_json else {}
        
        # Update the preference for this definition
        preferences[str(definition_id)] = {
            'status_category': status_category,
            'specific_state': specific_state
        }
        
        # Save back to database
        success = set_user_preference('relationship_filters', json.dumps(preferences))
        
        if success:
            return jsonify({'success': True}), 200
        else:
            return jsonify({'success': False, 'error': 'Failed to save preference'}), 500
            
    except Exception as e:
        logger.error(f"Error saving relationship filter preference: {e}", exc_info=True)
        return jsonify({"error": f"An internal error occurred: {e}"}), 500