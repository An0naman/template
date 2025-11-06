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
        logger.info(f"=== HIERARCHY DEBUG for Entry {entry_id} ===")
        
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
            """Get entry details including status color"""
            cursor.execute('''
                SELECT e.id, e.title, e.status, et.singular_label,
                       COALESCE(es.color, '#6c757d') AS status_color
                FROM Entry e
                JOIN EntryType et ON e.entry_type_id = et.id
                LEFT JOIN EntryState es ON e.status = es.name AND e.entry_type_id = es.entry_type_id
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
        
        def get_direct_parents(entry_id):
            """
            Find all parent entries where the current entry is a child.
            
            Logic based on RelationshipDefinition:
            - First get entry's type_id
            - Find definitions where CASE returns 'Child':
              * entry_type_id_to = type AND hierarchy_direction = 'from_to_child'
              * entry_type_id_to = type AND hierarchy_direction = 'to_from_child'
            - For each definition, find actual EntryRelationship records
            - Return the other entry as the parent
            """
            parents = []
            
            # Get entry's type
            cursor.execute("SELECT entry_type_id FROM Entry WHERE id = ?", [entry_id])
            entry_row = cursor.fetchone()
            if not entry_row:
                return parents
            entry_type_id = entry_row['entry_type_id']
            
            # Find RelationshipDefinitions where this entry type is a CHILD
            # According to user's CASE logic: entry_type_id_to = X means X is CHILD (regardless of direction)
            query = '''
                SELECT 
                    rd.id,
                    rd.name,
                    rd.entry_type_id_from,
                    rd.entry_type_id_to,
                    rd.hierarchy_direction,
                    rd.label_from_side,
                    rd.label_to_side
                FROM RelationshipDefinition rd
                WHERE rd.is_hierarchical = 1
                AND rd.entry_type_id_to = ?
            '''
            cursor.execute(query, [entry_type_id])
            child_definitions = cursor.fetchall()
            
            logger.info(f"get_direct_parents({entry_id}): Found {len(child_definitions)} definition(s) where type {entry_type_id} is child")
            
            # For each definition, find actual relationships involving this entry
            for defn in child_definitions:
                # Determine which side has the parent type and use the label for that side
                # We want the label that describes what the PARENT is (from the parent's side)
                if defn['entry_type_id_to'] == entry_type_id:
                    # Entry type is in TO position, so FROM type is the parent
                    # Use label_to_side because we want the label FROM the parent's perspective
                    relationship_label = defn['label_to_side']
                else:
                    # Entry type is in FROM position, so TO type is the parent
                    # Use label_from_side because we want the label FROM the parent's perspective
                    relationship_label = defn['label_from_side']
                
                # Find all EntryRelationship records matching this definition and entry
                rel_query = '''
                    SELECT 
                        er.id as relationship_id,
                        er.source_entry_id,
                        er.target_entry_id,
                        CASE 
                            WHEN er.source_entry_id = ? THEN er.target_entry_id
                            WHEN er.target_entry_id = ? THEN er.source_entry_id
                        END as parent_id
                    FROM EntryRelationship er
                    WHERE er.relationship_type = ?
                    AND (er.source_entry_id = ? OR er.target_entry_id = ?)
                '''
                cursor.execute(rel_query, [entry_id, entry_id, defn['id'], entry_id, entry_id])
                relationships = cursor.fetchall()
                
                # Get details for each parent entry
                for rel in relationships:
                    if not rel['parent_id']:
                        continue
                        
                    parent_entry = get_entry_details(rel['parent_id'])
                    if parent_entry:
                        parent_obj = {
                            'id': parent_entry['id'],
                            'title': parent_entry['title'],
                            'status': parent_entry['status'],
                            'status_color': parent_entry['status_color'],
                            'entry_type': {
                                'label': parent_entry['singular_label'],
                                'icon': 'fas fa-link',
                                'color': '#6c757d'
                            },
                            'relationship_id': rel['relationship_id'],
                            'relationship_type': relationship_label,
                            'relationship_def_id': defn['id'],
                            'relationship_type_name': defn['name']
                        }
                        parents.append(parent_obj)
                        logger.info(f"  Parent: {rel['parent_id']} ({parent_entry['title']}) via {defn['name']}")
            
            return parents

        def get_all_hierarchical_parents(child_id):
            """Get ALL parents from ANY hierarchical relationship type - wrapper around get_direct_parents"""
            parents_data = get_direct_parents(child_id)
            
            # Convert to the format expected by build_hierarchy_tree
            parents = []
            for parent in parents_data:
                parent_obj = {
                    'parent_id': parent['id'],
                    'relationship_id': parent['relationship_id'],
                    'relationship_def_id': parent.get('relationship_def_id', ''),
                    'relationship_type_name': parent['relationship_type_name'],
                    'relationship_label': parent['relationship_type']
                }
                parents.append(parent_obj)
            
            return parents
        
        def get_direct_children(entry_id):
            """
            Simple function to get ALL direct children of a given entry.
            Returns a list of child entry objects with all necessary details.
            This function will be used recursively for children, grandchildren, great-grandchildren, etc.
            
            Logic based on RelationshipDefinition:
            - First get entry's type_id
            - Find definitions where CASE returns 'Parent':
              * entry_type_id_from = type AND hierarchy_direction = 'from_to_child'
              * entry_type_id_from = type AND hierarchy_direction = 'to_from_child'
            - For each definition, find actual EntryRelationship records
            - Return the other entry as the child
            """
            # Get entry's type
            cursor.execute("SELECT entry_type_id FROM Entry WHERE id = ?", [entry_id])
            entry_row = cursor.fetchone()
            if not entry_row:
                return []
            entry_type_id = entry_row['entry_type_id']
            
            # Find RelationshipDefinitions where this entry type is a PARENT
            # According to user's CASE logic: entry_type_id_from = X means X is PARENT (regardless of direction)
            query = '''
                SELECT 
                    rd.id,
                    rd.name,
                    rd.entry_type_id_from,
                    rd.entry_type_id_to,
                    rd.hierarchy_direction,
                    rd.label_from_side,
                    rd.label_to_side
                FROM RelationshipDefinition rd
                WHERE rd.is_hierarchical = 1
                AND rd.entry_type_id_from = ?
            '''
            cursor.execute(query, [entry_type_id])
            parent_definitions = cursor.fetchall()
            
            logger.info(f"get_direct_children({entry_id}): Found {len(parent_definitions)} definition(s) where type {entry_type_id} is parent")
            
            children = []
            # For each definition, find actual relationships involving this entry
            for defn in parent_definitions:
                # Determine which side has the child type and use the label for that side
                # We want the label that describes what the CHILD is (from the child's side)
                if defn['entry_type_id_from'] == entry_type_id:
                    # Entry type is in FROM position, so TO type is the child
                    # Use label_from_side because we want the label FROM the child's perspective
                    relationship_label = defn['label_from_side']
                else:
                    # Entry type is in TO position, so FROM type is the child
                    # Use label_to_side because we want the label FROM the child's perspective
                    relationship_label = defn['label_to_side']
                
                # Find all EntryRelationship records matching this definition and entry
                rel_query = '''
                    SELECT 
                        er.id as relationship_id,
                        er.source_entry_id,
                        er.target_entry_id,
                        CASE 
                            WHEN er.source_entry_id = ? THEN er.target_entry_id
                            WHEN er.target_entry_id = ? THEN er.source_entry_id
                        END as child_id
                    FROM EntryRelationship er
                    WHERE er.relationship_type = ?
                    AND (er.source_entry_id = ? OR er.target_entry_id = ?)
                '''
                cursor.execute(rel_query, [entry_id, entry_id, defn['id'], entry_id, entry_id])
                relationships = cursor.fetchall()
                
                # Get details for each child entry
                for rel in relationships:
                    if not rel['child_id']:
                        continue
                        
                    child_entry = get_entry_details(rel['child_id'])
                    if child_entry:
                        child_obj = {
                            'id': child_entry['id'],
                            'title': child_entry['title'],
                            'status': child_entry['status'],
                            'status_color': child_entry['status_color'],
                            'entry_type': {
                                'label': child_entry['singular_label'],
                                'icon': 'fas fa-link',
                                'color': '#6c757d'
                            },
                            'relationship_id': rel['relationship_id'],
                            'relationship_type': relationship_label,
                            'children': []  # Will be populated by recursive calls
                        }
                        children.append(child_obj)
                        logger.info(f"  Child: {rel['child_id']} ({child_entry['title']}) via {defn['name']}")
            
            return children
        
        def build_complete_descendant_tree(entry_id, visited=None, depth=0):
            """
            STEP 2 & 3: Recursively build the complete descendant tree.
            
            Step 2: Get all direct children of the current entry
            Step 3: Recursively get descendants for each child
            
            Args:
                entry_id: The entry to get descendants for
                visited: Set of already visited entry IDs to prevent cycles
                depth: Current recursion depth
            
            Returns:
                List of child nodes with their descendants
            """
            if visited is None:
                visited = set()
            
            # Prevent infinite loops and respect max depth
            if depth >= max_depth or entry_id in visited:
                logger.info(f"{'  ' * depth}build_complete_descendant_tree({entry_id}): Stopping (depth={depth}, visited={entry_id in visited})")
                return []
            
            visited.add(entry_id)
            
            # STEP 2: Get all direct children of this entry
            children = get_direct_children(entry_id)
            logger.info(f"{'  ' * depth}STEP 2: Entry {entry_id} has {len(children)} direct child(ren)")
            
            # STEP 3: For each child, recursively get their descendants
            for child in children:
                child_id = child['id']
                logger.info(f"{'  ' * depth}STEP 3: Recursively getting descendants for child {child_id}")
                # Recursive call to get this child's descendants
                child['children'] = build_complete_descendant_tree(child_id, visited.copy(), depth + 1)
                logger.info(f"{'  ' * depth}  Child {child_id} has {len(child['children'])} descendant(s)")
            
            return children
        
        def build_hierarchy_tree(target_id):
            """
            Build hierarchy trees following the correct 3-step logic:
            
            STEP 1) Upwards - Look at relationship definitions where current record (target_id) is a CHILD.
                    Create a structure for any that exist, or if none, start one with the current entry.
            STEP 2) Downwards - Look at relationship definitions where current record is a PARENT, 
                    add all children records to the current structure as children (nesting where appropriate).
            STEP 3) Recursive - Undertake step 2 recursively for each child.
            """
            
            def build_upward_to_root(current_id, target_id, via_parent_id=None, visited=None, depth=0):
                """
                Build a node and recursively build upward to find all ancestors.
                This builds the path from root down to target.
                via_parent_id: If specified, only follow paths that go through this intermediate entry
                """
                if visited is None:
                    visited = set()
                
                if depth >= max_depth or current_id in visited:
                    return None
                
                visited.add(current_id)
                
                # Get entry details for current node
                entry = get_entry_details(current_id)
                if not entry:
                    return None
                
                is_target = (current_id == target_id)
                
                # Create the node
                node = {
                    'id': entry['id'],
                    'title': entry['title'],
                    'status': entry['status'],
                    'status_color': entry['status_color'],
                    'entry_type': {
                        'label': entry['singular_label'],
                        'icon': 'fas fa-link',
                        'color': '#6c757d'
                    },
                    'is_target': is_target,
                    'children': []
                }
                
                if is_target:
                    # STEP 2 & 3: We've reached the target entry!
                    # Add ALL descendants recursively
                    logger.info(f"STEP 2 & 3: At target {target_id}, building complete descendant tree")
                    node['children'] = build_complete_descendant_tree(target_id, set(), 0)
                    logger.info(f"STEP 2 & 3: Target has {len(node['children'])} direct child(ren)")
                else:
                    # We're above the target - only show the path that leads to target
                    # Get all children and find which one(s) lead to target
                    children_data = get_direct_children(current_id)
                    
                    for child in children_data:
                        child_id = child['id']
                        if child_id and child_id not in visited:
                            # Check if this child leads to target
                            child_leads_to_target = (child_id == target_id or is_ancestor_of_target(child_id, target_id, visited.copy()))
                            
                            if not child_leads_to_target:
                                continue
                            
                            # If via_parent_id is specified AND we haven't reached it yet
                            # only follow paths through that parent
                            if via_parent_id and current_id != via_parent_id:
                                child_leads_to_via_parent = (
                                    child_id == via_parent_id or 
                                    is_ancestor_of_target(child_id, via_parent_id, visited.copy())
                                )
                                if not child_leads_to_via_parent:
                                    continue
                            
                            # Once we reach via_parent_id, clear the constraint so we can reach target
                            next_via_parent = None if current_id == via_parent_id else via_parent_id
                            
                            # This child is on the correct path, include it
                            child_node = build_upward_to_root(child_id, target_id, next_via_parent, visited.copy(), depth + 1)
                            if child_node:
                                child_node['relationship_id'] = child['relationship_id']
                                child_node['relationship_type'] = child['relationship_type']
                                node['children'].append(child_node)
                                # Only show one path to target (don't add siblings)
                                break
                
                return node
            
            def is_ancestor_of_target(current_id, target_id, checked=None):
                """Check if current_id is an ancestor of target_id (has target as descendant)"""
                if checked is None:
                    checked = set()
                
                if current_id == target_id:
                    return True
                
                if current_id in checked:
                    return False
                
                checked.add(current_id)
                
                # Get children and check if any of them lead to target
                children_data = get_direct_children(current_id)
                for child in children_data:
                    child_id = child['id']
                    if child_id and is_ancestor_of_target(child_id, target_id, checked):
                        return True
                
                return False
            
            def find_all_root_ancestors(start_id, visited=None):
                """Recursively find ALL topmost ancestors (can be multiple if entry has multiple parent lineages)"""
                if visited is None:
                    visited = set()
                
                if start_id in visited:
                    return []
                
                visited.add(start_id)
                parents = get_all_hierarchical_parents(start_id)
                
                if not parents:
                    return [start_id]  # This is a root
                
                # Follow ALL parents to find all roots
                all_roots = []
                for parent in parents:
                    parent_id = parent['parent_id']
                    roots = find_all_root_ancestors(parent_id, visited.copy())
                    all_roots.extend(roots)
                
                return all_roots
            
            # STEP 1: Get DIRECT parents of the target entry
            direct_parents = get_all_hierarchical_parents(target_id)
            logger.info(f"STEP 1: Entry {target_id} has {len(direct_parents)} direct parent(s)")
            
            if not direct_parents:
                # No parents - target is the root
                logger.info(f"STEP 1: Entry {target_id} is a ROOT (no parents)")
                entry = get_entry_details(target_id)
                if not entry:
                    return []
                
                # Create structure starting with target as root
                root_node = {
                    'id': entry['id'],
                    'title': entry['title'],
                    'status': entry['status'],
                    'status_color': entry['status_color'],
                    'entry_type': {
                        'label': entry['singular_label'],
                        'icon': 'fas fa-link',
                        'color': '#6c757d'
                    },
                    'is_target': True,
                    'children': build_complete_descendant_tree(target_id, set(), 0)
                }
                logger.info(f"STEP 1: Root node has {len(root_node['children'])} direct child(ren)")
                return [root_node]
            
            # Target has parents - create a tree for EACH root of EACH parent
            # This ensures multiple paths through different parents are shown separately
            hierarchy_trees = []
            
            # For each direct parent, find all its roots and create separate trees
            for parent_info in direct_parents:
                parent_id = parent_info['parent_id']
                rel_type_name = parent_info['relationship_type_name']
                
                # Find all possible roots for this parent
                roots_for_parent = find_all_root_ancestors(parent_id)
                logger.info(f"STEP 1: Parent {parent_id} has {len(roots_for_parent)} root(s): {roots_for_parent}")
                
                # Create a separate tree for each root
                for root_id in roots_for_parent:
                    logger.info(f"STEP 1: Building tree from root {root_id} via parent {parent_id}")
                    
                    # Build the complete structure from root down to target, going through this specific parent
                    tree = build_upward_to_root(root_id, target_id, parent_id, set(), 0)
                    if tree:
                        hierarchy_trees.append(tree)
                        logger.info(f"STEP 1: Tree built successfully")
            
            logger.info(f"STEP 1: Returning {len(hierarchy_trees)} hierarchy tree(s)")
            return hierarchy_trees
        
        # Build the hierarchy tree(s) - can be multiple if entry has multiple parents
        hierarchy_trees = build_hierarchy_tree(entry_id)
        
        return jsonify({
            'hierarchy': hierarchy_trees if isinstance(hierarchy_trees, list) else [hierarchy_trees] if hierarchy_trees else [],
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


# --- Grid Ordering Endpoints ---
@relationships_api_bp.route('/entry_types/<int:entry_type_id>/relationship_grid_order', methods=['GET'])
def get_relationship_grid_order(entry_type_id):
    """Get the custom grid order for relationship cards for a specific entry type"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT relationship_definition_id, display_order
            FROM RelationshipGridOrder
            WHERE entry_type_id = ?
            ORDER BY display_order
        ''', (entry_type_id,))
        
        rows = cursor.fetchall()
        order_map = {row['relationship_definition_id']: row['display_order'] for row in rows}
        
        return jsonify(order_map), 200
    except Exception as e:
        logger.error(f"Error getting relationship grid order for entry type {entry_type_id}: {e}", exc_info=True)
        return jsonify({"error": f"An internal error occurred: {e}"}), 500


@relationships_api_bp.route('/entry_types/<int:entry_type_id>/relationship_grid_order', methods=['POST'])
def save_relationship_grid_order(entry_type_id):
    """Save the custom grid order for relationship cards for a specific entry type"""
    try:
        data = request.get_json()
        # Expect format: [{"definition_id": 1, "order": 0}, {"definition_id": 2, "order": 1}, ...]
        order_list = data.get('order', [])
        
        if not isinstance(order_list, list):
            return jsonify({'success': False, 'error': 'Invalid order format'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Delete existing order preferences for this entry type
        cursor.execute('DELETE FROM RelationshipGridOrder WHERE entry_type_id = ?', (entry_type_id,))
        
        # Insert new order preferences
        for item in order_list:
            definition_id = item.get('definition_id')
            display_order = item.get('order')
            
            if definition_id is not None and display_order is not None:
                cursor.execute('''
                    INSERT OR REPLACE INTO RelationshipGridOrder 
                    (entry_type_id, relationship_definition_id, display_order, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ''', (entry_type_id, definition_id, display_order))
        
        conn.commit()
        return jsonify({'success': True, 'message': 'Grid order saved successfully'}), 200
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error saving relationship grid order for entry type {entry_type_id}: {e}", exc_info=True)
        return jsonify({"error": f"An internal error occurred: {e}"}), 500