# template_app/app/serializers.py
import json

def serialize_entry(entry):
    """Helper to serialize entry rows into dictionaries."""
    if entry is None:
        return None
    return {
        "id": entry['id'],
        "title": entry['title'],
        "description": entry['description'],
        "entry_type_label": entry['entry_type_label'],
        "entry_type_name": entry['entry_type_name'],
        "intended_end_date": entry['intended_end_date'] if 'intended_end_date' in entry.keys() else None,
        "actual_end_date": entry['actual_end_date'] if 'actual_end_date' in entry.keys() else None,
        "status": entry['status'] if 'status' in entry.keys() else 'active',
        "created_at": entry['created_at']
    }

def serialize_note(note):
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
        "file_paths": json.loads(note['file_paths']) if note['file_paths'] else [],
        "associated_entry_ids": json.loads(note['associated_entry_ids']) if note['associated_entry_ids'] else [],
        "urls": json.loads(note['urls']) if note.get('urls') else []
    }

def serialize_relationship_definition(definition):
    """Helper to serialize RelationshipDefinition rows into dictionaries."""
    if definition is None:
        return None
    return {
        "id": definition['id'],
        "name": definition['name'],
        "description": definition['description'],
        "entry_type_id_from": definition['entry_type_id_from'],
        "entry_type_from_label": definition['entry_type_from_label'],
        "entry_type_id_to": definition['entry_type_id_to'],
        "entry_type_to_label": definition['entry_type_to_label'],
        "cardinality_from": definition['cardinality_from'],
        "cardinality_to": definition['cardinality_to'],
        "label_from_side": definition['label_from_side'],
        "label_to_side": definition['label_to_side'],
        "allow_quantity_unit": bool(definition['allow_quantity_unit']),
        "is_active": bool(definition['is_active'])
    }

def serialize_entry_relationship(relationship_row, is_inverse=False):
    """Helper to serialize EntryRelationship rows into dictionaries."""
    if relationship_row is None:
        return None
    
    # Adjust labels based on whether it's an inverse relationship view
    relationship_label = relationship_row['label_from_side'] if not is_inverse else relationship_row['label_to_side']
    opposite_relationship_label = relationship_row['label_to_side'] if not is_inverse else relationship_row['label_from_side']
    
    # For cardinalities, display the 'from' side's cardinality when viewing from the 'from' side,
    # and the 'to' side's cardinality when viewing from the 'to' side.
    # The 'related' entry's cardinality is the *other* side of the definition.
    current_entry_cardinality = relationship_row['cardinality_from'] if not is_inverse else relationship_row['cardinality_to']
    related_entry_cardinality = relationship_row['cardinality_to'] if not is_inverse else relationship_row['cardinality_from']


    result = {
        "relationship_id": relationship_row['relationship_id'],
        "related_entry_id": relationship_row['related_entry_id'],
        "related_entry_title": relationship_row['related_entry_title'],
        "relationship_label": relationship_label,
        "opposite_relationship_label": opposite_relationship_label,
        "allow_quantity_unit": bool(relationship_row['allow_quantity_unit']),
        "quantity": relationship_row['quantity'],
        "unit": relationship_row['unit'],
        "definition_id": relationship_row['definition_id'],
        "definition_name": relationship_row['definition_name'],
        "current_entry_cardinality": current_entry_cardinality,
        "related_entry_cardinality": related_entry_cardinality,
        "is_inverse": is_inverse
    }
    
    # Add status if available
    if relationship_row['related_entry_status'] is not None:
        result['related_entry_status'] = relationship_row['related_entry_status']
        result['related_entry_status_color'] = relationship_row['related_entry_status_color']
        result['related_entry_status_category'] = relationship_row['related_entry_status_category']
    
    return result
    
    # Add source/target IDs if available
    if 'source_entry_id' in relationship_row.keys():
        result['source_entry_id'] = relationship_row['source_entry_id']
    if 'source_entry_title' in relationship_row.keys():
        result['source_title'] = relationship_row['source_entry_title']
    if 'target_entry_id' in relationship_row.keys():
        result['target_entry_id'] = relationship_row['target_entry_id']
    if 'target_entry_title' in relationship_row.keys():
        result['target_title'] = relationship_row['target_entry_title']
    
    # Add relationship_type (definition_id) for compatibility
    result['relationship_type'] = relationship_row['definition_id']
    
    return result