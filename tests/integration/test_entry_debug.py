import sqlite3
from hierarchy_function import get_hierarchical_relations

def main():
    # Connect to the database inside the Docker container
    conn = sqlite3.connect('/app/data/template.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    entry_id = 85
    
    print("=" * 70)
    print(f"Testing get_hierarchical_relations() for Entry ID: {entry_id}")
    print("=" * 70)
    print()
    
    # Test PARENTS direction with debug
    print("DIRECTION: 'parents'")
    print("-" * 70)
    
    # Get entry type
    cursor.execute("SELECT entry_type_id FROM Entry WHERE id = ?", [entry_id])
    entry_row = cursor.fetchone()
    entry_type_id = entry_row['entry_type_id']
    print(f"Entry {entry_id} has type {entry_type_id}")
    print()
    
    # Find child definitions
    cursor.execute('''
        SELECT 
            id,
            name,
            entry_type_id_from,
            entry_type_id_to,
            hierarchy_direction,
            label_from_side,
            label_to_side,
            CASE 
                WHEN entry_type_id_from = ? AND hierarchy_direction = 'from_to_child' THEN 'Parent'
                WHEN entry_type_id_from = ? AND hierarchy_direction = 'to_from_child' THEN 'Child' 
                WHEN entry_type_id_to = ? AND hierarchy_direction = 'from_to_child' THEN 'Child'
                WHEN entry_type_id_to = ? AND hierarchy_direction = 'to_from_child' THEN 'Parent'
                ELSE 'NA'
            END as role
        FROM RelationshipDefinition
        WHERE is_hierarchical = 1
        AND (entry_type_id_from = ? OR entry_type_id_to = ?)
    ''', [entry_type_id, entry_type_id, entry_type_id, entry_type_id, entry_type_id, entry_type_id])
    
    all_defs = cursor.fetchall()
    print(f"Found {len(all_defs)} hierarchical definitions involving type {entry_type_id}:")
    child_defs = [d for d in all_defs if d['role'] == 'Child']
    print(f"  {len(child_defs)} where type {entry_type_id} is CHILD")
    print()
    
    for defn in child_defs:
        print(f"Processing definition {defn['id']}: {defn['name']}")
        
        # Find relationships
        cursor.execute('''
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
        ''', [entry_id, entry_id, defn['id'], entry_id, entry_id])
        
        rels = cursor.fetchall()
        print(f"  Found {len(rels)} relationship(s)")
        for rel in rels:
            print(f"    Rel ID: {rel['relationship_id']}, Parent Entry: {rel['parent_id']}")
        print()
    
    # Now run the actual function
    parents = get_hierarchical_relations(cursor, entry_id, 'parents')
    
    print(f"✓ Found {len(parents)} parent(s):")
    print()
    
    for i, parent in enumerate(parents, 1):
        print(f"{i}. Entry ID: {parent['id']}")
        print(f"   Title: {parent['title']}")
        print(f"   Status: {parent['status']}")
        print(f"   Type: {parent['entry_type']['label']}")
        print(f"   Relationship: {parent['relationship_type_name']}")
        print(f"   Direction: {parent['hierarchy_direction']}")
        print(f"   Label: {parent['relationship_type']}")
        print(f"   Rel ID: {parent['relationship_id']}")
        print()
    
    print("=" * 70)
    
    conn.close()

if __name__ == '__main__':
    main()
