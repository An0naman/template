# template_app/app/api/shared_relationships_api.py
from flask import Blueprint, request, jsonify, g, current_app
import sqlite3
import logging

# Define a Blueprint for Shared Relationships API
shared_relationships_api_bp = Blueprint('shared_relationships_api', __name__)

# Get a logger for this module
logger = logging.getLogger(__name__)

def get_db():
    if 'db' not in g:
        db_path = current_app.config['DATABASE_PATH']
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
    return g.db

@shared_relationships_api_bp.route('/entries/<int:entry_id>/shared_relationship_opportunities', methods=['GET'])
def get_shared_relationship_opportunities(entry_id):
    """
    Find opportunities to automatically create relationships based on shared relationship patterns.
    
    For example, if entry A relates to entry B, and entry B relates to entries C1, C2, C3,
    and there's a relationship definition that allows entry A to relate directly to entries of type C,
    then this endpoint will return those potential relationships.
    """
    conn = get_db()
    cursor = conn.cursor()
    
    opportunities = []
    
    try:
        # Get the current entry details
        cursor.execute("SELECT id, title, entry_type_id FROM Entry WHERE id = ?", (entry_id,))
        current_entry = cursor.fetchone()
        if not current_entry:
            return jsonify({"error": "Entry not found"}), 404
            
        current_entry_type_id = current_entry['entry_type_id']
        
        # Find all entries that this entry is related to
        cursor.execute('''
            SELECT DISTINCT 
                er.target_entry_id as intermediate_entry_id,
                e.title as intermediate_entry_title,
                e.entry_type_id as intermediate_entry_type_id,
                rd.name as relationship_name,
                rd.id as relationship_definition_id
            FROM EntryRelationship er
            JOIN Entry e ON er.target_entry_id = e.id
            JOIN RelationshipDefinition rd ON er.relationship_type = rd.id
            WHERE er.source_entry_id = ?
            
            UNION
            
            SELECT DISTINCT 
                er.source_entry_id as intermediate_entry_id,
                e.title as intermediate_entry_title, 
                e.entry_type_id as intermediate_entry_type_id,
                rd.name as relationship_name,
                rd.id as relationship_definition_id
            FROM EntryRelationship er
            JOIN Entry e ON er.source_entry_id = e.id
            JOIN RelationshipDefinition rd ON er.relationship_type = rd.id
            WHERE er.target_entry_id = ?
        ''', (entry_id, entry_id))
        
        intermediate_entries = cursor.fetchall()
        
        # For each intermediate entry, find what it's related to
        for intermediate in intermediate_entries:
            intermediate_id = intermediate['intermediate_entry_id']
            intermediate_title = intermediate['intermediate_entry_title']
            intermediate_type_id = intermediate['intermediate_entry_type_id']
            
            # Find entries related to this intermediate entry
            cursor.execute('''
                SELECT DISTINCT
                    er.target_entry_id as target_id,
                    e.title as target_title,
                    e.entry_type_id as target_type_id,
                    rd.name as relationship_name,
                    rd.id as relationship_def_id,
                    er.quantity,
                    er.unit
                FROM EntryRelationship er
                JOIN Entry e ON er.target_entry_id = e.id
                JOIN RelationshipDefinition rd ON er.relationship_type = rd.id
                WHERE er.source_entry_id = ?
                AND er.target_entry_id != ?  -- Don't include the original entry
                
                UNION
                
                SELECT DISTINCT
                    er.source_entry_id as target_id,
                    e.title as target_title,
                    e.entry_type_id as target_type_id,
                    rd.name as relationship_name,
                    rd.id as relationship_def_id,
                    er.quantity,
                    er.unit
                FROM EntryRelationship er
                JOIN Entry e ON er.source_entry_id = e.id
                JOIN RelationshipDefinition rd ON er.relationship_type = rd.id
                WHERE er.target_entry_id = ?
                AND er.source_entry_id != ?  -- Don't include the original entry
            ''', (intermediate_id, entry_id, intermediate_id, entry_id))
            
            potential_targets = cursor.fetchall()
            
            # For each potential target, check if there's a relationship definition
            # that allows the current entry to relate to it
            for target in potential_targets:
                target_id = target['target_id']
                target_title = target['target_title']
                target_type_id = target['target_type_id']
                
                # Check if there's already a relationship between current entry and target
                cursor.execute('''
                    SELECT COUNT(*) as count FROM EntryRelationship 
                    WHERE (source_entry_id = ? AND target_entry_id = ?)
                    OR (source_entry_id = ? AND target_entry_id = ?)
                ''', (entry_id, target_id, target_id, entry_id))
                
                if cursor.fetchone()['count'] > 0:
                    continue  # Relationship already exists
                
                # Check if there's a relationship definition that allows this connection
                cursor.execute('''
                    SELECT 
                        rd.id,
                        rd.name,
                        rd.label_from_side,
                        rd.label_to_side,
                        rd.allow_quantity_unit,
                        rd.cardinality_from,
                        rd.cardinality_to,
                        rd.entry_type_id_from,
                        rd.entry_type_id_to,
                        et_from.singular_label as from_type_label,
                        et_to.singular_label as to_type_label
                    FROM RelationshipDefinition rd
                    JOIN EntryType et_from ON rd.entry_type_id_from = et_from.id
                    JOIN EntryType et_to ON rd.entry_type_id_to = et_to.id
                    WHERE rd.is_active = 1
                    AND (
                        (rd.entry_type_id_from = ? AND rd.entry_type_id_to = ?)
                        OR 
                        (rd.entry_type_id_from = ? AND rd.entry_type_id_to = ?)
                    )
                ''', (current_entry_type_id, target_type_id, target_type_id, current_entry_type_id))
                
                valid_definitions = cursor.fetchall()
                
                for definition in valid_definitions:
                    # Check cardinality constraints before suggesting
                    def_id = definition['id']
                    is_current_from_side = definition['entry_type_id_from'] == current_entry_type_id
                    
                    # Count existing relationships for cardinality check
                    if is_current_from_side:
                        cursor.execute('''
                            SELECT COUNT(*) as count FROM EntryRelationship 
                            WHERE source_entry_id = ? AND relationship_type = ?
                        ''', (entry_id, def_id))
                        current_count = cursor.fetchone()['count']
                        max_allowed = 1 if definition['cardinality_from'] == 'one' else float('inf')
                    else:
                        cursor.execute('''
                            SELECT COUNT(*) as count FROM EntryRelationship 
                            WHERE target_entry_id = ? AND relationship_type = ?
                        ''', (entry_id, def_id))
                        current_count = cursor.fetchone()['count']
                        max_allowed = 1 if definition['cardinality_to'] == 'one' else float('inf')
                    
                    if current_count >= max_allowed:
                        continue  # Cardinality constraint would be violated
                    
                    opportunities.append({
                        'intermediate_entry': {
                            'id': intermediate_id,
                            'title': intermediate_title,
                            'entry_type_id': intermediate_type_id
                        },
                        'target_entry': {
                            'id': target_id,
                            'title': target_title,
                            'entry_type_id': target_type_id
                        },
                        'relationship_definition': {
                            'id': definition['id'],
                            'name': definition['name'],
                            'label_from_side': definition['label_from_side'],
                            'label_to_side': definition['label_to_side'],
                            'allow_quantity_unit': definition['allow_quantity_unit'],
                            'from_type_label': definition['from_type_label'],
                            'to_type_label': definition['to_type_label']
                        },
                        'source_relationship': {
                            'quantity': target['quantity'],
                            'unit': target['unit']
                        },
                        'suggested_direction': 'from' if is_current_from_side else 'to'
                    })
        
        # Group opportunities by intermediate entry and relationship definition
        grouped_opportunities = {}
        for opportunity in opportunities:
            intermediate_id = opportunity['intermediate_entry']['id']
            def_id = opportunity['relationship_definition']['id']
            
            key = f"{intermediate_id}_{def_id}"
            if key not in grouped_opportunities:
                grouped_opportunities[key] = {
                    'intermediate_entry': opportunity['intermediate_entry'],
                    'relationship_definition': opportunity['relationship_definition'],
                    'potential_targets': []
                }
            
            grouped_opportunities[key]['potential_targets'].append({
                'target_entry': opportunity['target_entry'],
                'source_relationship': opportunity['source_relationship'],
                'suggested_direction': opportunity['suggested_direction']
            })
        
        return jsonify(list(grouped_opportunities.values()))
        
    except Exception as e:
        logger.error(f"Error finding shared relationship opportunities for entry {entry_id}: {e}", exc_info=True)
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@shared_relationships_api_bp.route('/entries/<int:entry_id>/create_shared_relationships', methods=['POST'])
def create_shared_relationships(entry_id):
    """
    Create multiple relationships based on shared relationship opportunities.
    
    Expected payload:
    {
        "relationships": [
            {
                "definition_id": 1,
                "target_entry_id": 2,
                "quantity": 100,
                "unit": "grams"
            },
            ...
        ]
    }
    """
    data = request.get_json()
    relationships = data.get('relationships', [])
    
    if not relationships:
        return jsonify({"error": "No relationships specified"}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    created_relationships = []
    failed_relationships = []
    
    try:
        for rel_data in relationships:
            definition_id = rel_data.get('definition_id')
            target_entry_id = rel_data.get('target_entry_id')
            quantity = rel_data.get('quantity')
            unit = rel_data.get('unit')
            
            if not definition_id or not target_entry_id:
                failed_relationships.append({
                    'data': rel_data,
                    'error': 'Missing definition_id or target_entry_id'
                })
                continue
            
            try:
                # Check if the relationship definition allows quantity/unit
                cursor.execute("SELECT allow_quantity_unit FROM RelationshipDefinition WHERE id = ?", (definition_id,))
                rel_def = cursor.fetchone()
                if not rel_def:
                    failed_relationships.append({
                        'data': rel_data,
                        'error': 'Relationship definition not found'
                    })
                    continue
                
                if not rel_def['allow_quantity_unit']:
                    quantity = None
                    unit = None
                else:
                    # Convert quantity to float if provided and allowed
                    if quantity is not None:
                        try:
                            quantity = float(quantity)
                        except (ValueError, TypeError):
                            failed_relationships.append({
                                'data': rel_data,
                                'error': 'Quantity must be a valid number'
                            })
                            continue
                
                # Prevent self-referencing relationships
                if entry_id == target_entry_id:
                    failed_relationships.append({
                        'data': rel_data,
                        'error': 'Cannot create a relationship to the same entry'
                    })
                    continue
                
                # Check for existing relationship
                cursor.execute(
                    "SELECT COUNT(*) FROM EntryRelationship WHERE source_entry_id = ? AND target_entry_id = ? AND relationship_type = ?",
                    (entry_id, target_entry_id, definition_id)
                )
                if cursor.fetchone()[0] > 0:
                    failed_relationships.append({
                        'data': rel_data,
                        'error': 'This specific relationship already exists'
                    })
                    continue
                
                # Create the relationship
                cursor.execute(
                    "INSERT INTO EntryRelationship (source_entry_id, target_entry_id, relationship_type, quantity, unit) VALUES (?, ?, ?, ?, ?)",
                    (entry_id, target_entry_id, definition_id, quantity, unit)
                )
                
                created_relationships.append({
                    'relationship_id': cursor.lastrowid,
                    'definition_id': definition_id,
                    'target_entry_id': target_entry_id,
                    'quantity': quantity,
                    'unit': unit
                })
                
            except sqlite3.IntegrityError as e:
                failed_relationships.append({
                    'data': rel_data,
                    'error': f'Database integrity error: {str(e)}'
                })
            except Exception as e:
                failed_relationships.append({
                    'data': rel_data,
                    'error': f'Unexpected error: {str(e)}'
                })
        
        # Commit all successful relationships
        if created_relationships:
            conn.commit()
        
        return jsonify({
            'created': created_relationships,
            'failed': failed_relationships,
            'summary': {
                'created_count': len(created_relationships),
                'failed_count': len(failed_relationships),
                'total_requested': len(relationships)
            }
        }), 201 if created_relationships else 400
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating shared relationships for entry {entry_id}: {e}", exc_info=True)
        return jsonify({"error": f"An internal error occurred: {str(e)}"}), 500
