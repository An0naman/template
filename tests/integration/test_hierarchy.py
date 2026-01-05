"""
Test function for getting hierarchical relationships
This can be used to find either parents or children of an entry
"""

def get_hierarchical_relations(cursor, entry_id, direction='parents'):
    """
    Get hierarchical relationships for an entry.
    
    Args:
        cursor: Database cursor
        entry_id: The entry ID to find relationships for
        direction: Either 'parents' or 'children'
        
    Returns:
        List of related entries with their details
        
    Logic:
    - For 'parents': Find entries where current entry is a CHILD
      * If hierarchy_direction = 'from_to_child': source_entry_id is parent, target_entry_id is child
        → Current entry is target, so return source entries
      * If hierarchy_direction = 'to_from_child': target_entry_id is parent, source_entry_id is child  
        → Current entry is source, so return target entries
        
    - For 'children': Find entries where current entry is a PARENT
      * If hierarchy_direction = 'from_to_child': source_entry_id is parent, target_entry_id is child
        → Current entry is source, so return target entries
      * If hierarchy_direction = 'to_from_child': target_entry_id is parent, source_entry_id is child
        → Current entry is target, so return source entries
    """
    
    if direction == 'parents':
        # Find parents: entries where current entry is the child
        query = '''
            SELECT DISTINCT 
                CASE 
                    WHEN rd.hierarchy_direction = 'from_to_child' THEN er.source_entry_id
                    WHEN rd.hierarchy_direction = 'to_from_child' THEN er.target_entry_id
                END as related_entry_id,
                rd.id as relationship_def_id,
                rd.name as relationship_type_name,
                rd.hierarchy_direction,
                CASE 
                    WHEN rd.hierarchy_direction = 'from_to_child' THEN rd.label_from_side
                    WHEN rd.hierarchy_direction = 'to_from_child' THEN rd.label_to_side
                END as relationship_label,
                er.id as relationship_id,
                e.id as entry_id,
                e.title as entry_title,
                e.status as entry_status,
                et.singular_label as entry_type
            FROM EntryRelationship er
            JOIN RelationshipDefinition rd ON er.relationship_type = rd.id
            JOIN Entry e ON e.id = CASE 
                WHEN rd.hierarchy_direction = 'from_to_child' THEN er.source_entry_id
                WHEN rd.hierarchy_direction = 'to_from_child' THEN er.target_entry_id
            END
            JOIN EntryType et ON e.entry_type_id = et.id
            WHERE rd.is_hierarchical = 1
            AND (
                (rd.hierarchy_direction = 'from_to_child' AND er.target_entry_id = ?)
                OR (rd.hierarchy_direction = 'to_from_child' AND er.source_entry_id = ?)
            )
        '''
        
    elif direction == 'children':
        # Find children: entries where current entry is the parent
        query = '''
            SELECT DISTINCT 
                CASE 
                    WHEN rd.hierarchy_direction = 'from_to_child' THEN er.target_entry_id
                    WHEN rd.hierarchy_direction = 'to_from_child' THEN er.source_entry_id
                END as related_entry_id,
                rd.id as relationship_def_id,
                rd.name as relationship_type_name,
                rd.hierarchy_direction,
                CASE 
                    WHEN rd.hierarchy_direction = 'from_to_child' THEN rd.label_from_side
                    WHEN rd.hierarchy_direction = 'to_from_child' THEN rd.label_to_side
                END as relationship_label,
                er.id as relationship_id,
                e.id as entry_id,
                e.title as entry_title,
                e.status as entry_status,
                et.singular_label as entry_type
            FROM EntryRelationship er
            JOIN RelationshipDefinition rd ON er.relationship_type = rd.id
            JOIN Entry e ON e.id = CASE 
                WHEN rd.hierarchy_direction = 'from_to_child' THEN er.target_entry_id
                WHEN rd.hierarchy_direction = 'to_from_child' THEN er.source_entry_id
            END
            JOIN EntryType et ON e.entry_type_id = et.id
            WHERE rd.is_hierarchical = 1
            AND (
                (rd.hierarchy_direction = 'from_to_child' AND er.source_entry_id = ?)
                OR (rd.hierarchy_direction = 'to_from_child' AND er.target_entry_id = ?)
            )
        '''
    else:
        raise ValueError(f"Invalid direction: {direction}. Must be 'parents' or 'children'")
    
    cursor.execute(query, [entry_id, entry_id])
    results = cursor.fetchall()
    
    # Format the results
    relations = []
    for row in results:
        relations.append({
            'id': row['entry_id'],
            'title': row['entry_title'],
            'status': row['entry_status'],
            'entry_type': {
                'label': row['entry_type'],
                'icon': 'fas fa-link',
                'color': '#6c757d'
            },
            'relationship_id': row['relationship_id'],
            'relationship_type': row['relationship_label'],
            'relationship_def_id': row['relationship_def_id'],
            'relationship_type_name': row['relationship_type_name'],
            'hierarchy_direction': row['hierarchy_direction']
        })
    
    return relations


# Test script
if __name__ == '__main__':
    import sys
    import sqlite3
    
    # Direct database connection
    db_path = '/app/data/lifestack.db'
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Test with an entry ID (change this to test different entries)
    test_entry_id = 85
    
    print(f"\n{'='*60}")
    print(f"Testing Entry ID: {test_entry_id}")
    print(f"{'='*60}\n")
    
    # Get parents
    print("PARENTS (entries where this entry is a child):")
    print("-" * 60)
    parents = get_hierarchical_relations(cursor, test_entry_id, 'parents')
    if parents:
        for parent in parents:
            print(f"  ID: {parent['id']}")
            print(f"  Title: {parent['title']}")
            print(f"  Type: {parent['entry_type']['label']}")
            print(f"  Relationship: {parent['relationship_type_name']} ({parent['hierarchy_direction']})")
            print(f"  Label: {parent['relationship_type']}")
            print()
    else:
        print("  No parents found\n")
    
    # Get children
    print("CHILDREN (entries where this entry is a parent):")
    print("-" * 60)
    children = get_hierarchical_relations(cursor, test_entry_id, 'children')
    if children:
        for child in children:
            print(f"  ID: {child['id']}")
            print(f"  Title: {child['title']}")
            print(f"  Type: {child['entry_type']['label']}")
            print(f"  Relationship: {child['relationship_type_name']} ({child['hierarchy_direction']})")
            print(f"  Label: {child['relationship_type']}")
            print()
    else:
        print("  No children found\n")
    
    conn.close()
