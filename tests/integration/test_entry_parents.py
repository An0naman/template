#!/usr/bin/env python3
"""
Test the get_hierarchical_relations function for entry 85
"""
import sys
import sqlite3

# Import the function
sys.path.insert(0, '/app')
from hierarchy_function import get_hierarchical_relations

def main():
    # Connect to database
    db_path = '/app/data/template.db'
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Test entry 85 - seeking parents
    entry_id = 85
    
    print(f"\n{'='*70}")
    print(f"Testing get_hierarchical_relations() for Entry ID: {entry_id}")
    print(f"{'='*70}\n")
    
    print("DIRECTION: 'parents'")
    print("-" * 70)
    
    try:
        parents = get_hierarchical_relations(cursor, entry_id, 'parents')
        
        if parents:
            print(f"✓ Found {len(parents)} parent(s):\n")
            for idx, parent in enumerate(parents, 1):
                print(f"{idx}. Entry ID: {parent['id']}")
                print(f"   Title: {parent['title']}")
                print(f"   Status: {parent['status']}")
                print(f"   Type: {parent['entry_type']['label']}")
                print(f"   Relationship: {parent['relationship_type_name']}")
                print(f"   Direction: {parent['hierarchy_direction']}")
                print(f"   Label: {parent['relationship_type']}")
                print(f"   Rel ID: {parent['relationship_id']}")
                print()
        else:
            print("✗ No parents found\n")
            
    except Exception as e:
        print(f"✗ Error: {e}\n")
        import traceback
        traceback.print_exc()
    
    conn.close()
    print("=" * 70)

if __name__ == '__main__':
    main()
