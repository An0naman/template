# template_app/app/api/relationships_api.py
from flask import Blueprint, request, jsonify, g, current_app
import sqlite3
import logging
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
            rd.allow_quantity_unit, rd.is_active
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

    # Fetch relationships where current entry is the 'source' side
    cursor.execute('''
        SELECT
            er.id AS relationship_id,
            er.target_entry_id AS related_entry_id,
            e_to.title AS related_entry_title,
            rd.id AS definition_id,
            rd.name AS definition_name,
            rd.label_from_side,
            rd.label_to_side,
            rd.cardinality_from,
            rd.cardinality_to,
            rd.allow_quantity_unit,
            er.quantity,
            er.unit
        FROM EntryRelationship er
        JOIN RelationshipDefinition rd ON er.relationship_type = rd.id
        JOIN Entry e_to ON er.target_entry_id = e_to.id
        WHERE er.source_entry_id = ?
        ORDER BY rd.name, e_to.title
    ''', (entry_id,))
    from_relationships = cursor.fetchall()
    related_entries_data.extend([serialize_entry_relationship(row, is_inverse=False) for row in from_relationships])

    # Fetch relationships where current entry is the 'target' side
    cursor.execute('''
        SELECT
            er.id AS relationship_id,
            er.source_entry_id AS related_entry_id,
            e_from.title AS related_entry_title,
            rd.id AS definition_id,
            rd.name AS definition_name,
            rd.label_from_side,
            rd.label_to_side,
            rd.cardinality_from,
            rd.cardinality_to,
            rd.allow_quantity_unit,
            er.quantity,
            er.unit
        FROM EntryRelationship er
        JOIN RelationshipDefinition rd ON er.relationship_type = rd.id
        JOIN Entry e_from ON er.source_entry_id = e_from.id
        WHERE er.target_entry_id = ?
        ORDER BY rd.name, e_from.title
    ''', (entry_id,))
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

        # Check for existing relationship (same source, target, and definition)
        cursor.execute(
            "SELECT COUNT(*) FROM EntryRelationship WHERE source_entry_id = ? AND target_entry_id = ? AND relationship_type = ?",
            (source_entry_id, target_entry_id, definition_id)
        )
        if cursor.fetchone()[0] > 0:
            return jsonify({"error": "This specific relationship already exists."}), 409

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
    new_entry_name = data.get('name', '').strip()
    new_entry_description = data.get('description', '').strip()

    if not definition_id or not new_entry_name:
        return jsonify({"error": "Missing relationship definition ID or new entry name."}), 400

    conn = get_db()
    cursor = conn.cursor()
    try:
        # Create the new entry
        cursor.execute('''
            INSERT INTO Entry (name, description) VALUES (?, ?)
        ''', (new_entry_name, new_entry_description))
        new_entry_id = cursor.lastrowid

        # Add the relationship
        cursor.execute('''
            INSERT INTO EntryRelationship (source_entry_id, target_entry_id, relationship_type)
            VALUES (?, ?, ?)
        ''', (entry_id, new_entry_id, definition_id))
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