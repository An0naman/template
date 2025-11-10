#!/usr/bin/env python3
"""
Script to find and optionally fix entries with invalid entry_type_id references.

This issue can occur when:
- An entry type is deleted but entries still reference it
- An entry is created with a hardcoded/invalid entry_type_id
- Data migration issues
"""

import sqlite3
import sys
import os

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'template.db')

def find_invalid_entries():
    """Find entries with invalid entry_type_id"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Find entries with entry_type_id that doesn't exist in EntryType
    cursor.execute('''
        SELECT e.id, e.title, e.entry_type_id, e.description, e.created_at
        FROM Entry e
        LEFT JOIN EntryType et ON e.entry_type_id = et.id
        WHERE et.id IS NULL
        ORDER BY e.id
    ''')
    
    invalid_entries = cursor.fetchall()
    conn.close()
    
    return invalid_entries

def list_entry_types():
    """List all available entry types"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, name, singular_label, plural_label FROM EntryType ORDER BY singular_label')
    entry_types = cursor.fetchall()
    conn.close()
    
    return entry_types

def fix_entry_type(entry_id, new_entry_type_id):
    """Update an entry's entry_type_id"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('UPDATE Entry SET entry_type_id = ? WHERE id = ?', (new_entry_type_id, entry_id))
        conn.commit()
        print(f"✓ Updated entry {entry_id} to entry_type_id {new_entry_type_id}")
        return True
    except Exception as e:
        print(f"✗ Error updating entry {entry_id}: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def main():
    print("=" * 70)
    print("Finding entries with invalid entry_type_id references...")
    print("=" * 70)
    
    invalid_entries = find_invalid_entries()
    
    if not invalid_entries:
        print("\n✓ No entries with invalid entry_type_id found!")
        return
    
    print(f"\n⚠️  Found {len(invalid_entries)} entries with invalid entry_type_id:\n")
    
    for entry in invalid_entries:
        print(f"Entry ID: {entry['id']}")
        print(f"  Title: {entry['title']}")
        print(f"  Description: {entry['description'] or '(none)'}")
        print(f"  Invalid entry_type_id: {entry['entry_type_id']}")
        print(f"  Created: {entry['created_at']}")
        print()
    
    # Show available entry types
    print("\n" + "=" * 70)
    print("Available Entry Types:")
    print("=" * 70)
    entry_types = list_entry_types()
    for et in entry_types:
        print(f"  [{et['id']}] {et['singular_label']} ({et['name']})")
    
    # Interactive fix mode
    if len(sys.argv) > 1 and sys.argv[1] == '--fix':
        print("\n" + "=" * 70)
        print("Fix Mode - Update invalid entries")
        print("=" * 70)
        
        for entry in invalid_entries:
            print(f"\nEntry {entry['id']}: '{entry['title']}'")
            print(f"  Current invalid entry_type_id: {entry['entry_type_id']}")
            
            while True:
                choice = input("  Enter new entry_type_id (or 's' to skip): ").strip()
                
                if choice.lower() == 's':
                    print("  Skipped.")
                    break
                
                try:
                    new_type_id = int(choice)
                    # Validate it exists
                    valid_ids = [et['id'] for et in entry_types]
                    if new_type_id in valid_ids:
                        fix_entry_type(entry['id'], new_type_id)
                        break
                    else:
                        print(f"  ✗ Invalid entry_type_id. Choose from: {valid_ids}")
                except ValueError:
                    print("  ✗ Please enter a number or 's' to skip")
        
        print("\n✓ Done!")
    else:
        print("\n" + "=" * 70)
        print("To fix these entries, run:")
        print(f"  python3 {sys.argv[0]} --fix")
        print("=" * 70)

if __name__ == '__main__':
    main()
