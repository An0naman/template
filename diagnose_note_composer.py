#!/usr/bin/env python3
"""
Diagnostic script to test note type and related entries fetching
"""
import sys
import sqlite3
import os

def test_note_types(db_path, entry_id):
    """Test the note types query"""
    print(f"\n{'='*60}")
    print(f"Testing Note Types for Entry {entry_id}")
    print(f"{'='*60}")
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # First, check if the entry exists
    cursor.execute('SELECT * FROM entries WHERE id = ?', (entry_id,))
    entry = cursor.fetchone()
    
    if not entry:
        print(f"❌ Entry {entry_id} not found!")
        return
    
    print(f"✓ Entry found: {entry['title']}")
    print(f"  Entry Type ID: {entry['entry_type_id']}")
    
    # Get the entry type
    cursor.execute('SELECT * FROM entry_types WHERE id = ?', (entry['entry_type_id'],))
    entry_type = cursor.fetchone()
    
    if entry_type:
        print(f"✓ Entry Type: {entry_type['singular_label']}")
        print(f"  Note Types Field: {entry_type['note_types']}")
        
        if entry_type['note_types']:
            note_types = [nt.strip() for nt in entry_type['note_types'].split(',')]
            print(f"  Parsed Note Types: {note_types}")
        else:
            print(f"  ⚠️ Note types field is NULL or empty!")
    else:
        print(f"❌ Entry type not found!")
    
    # Now test the actual query used in the code
    print(f"\n--- Testing Actual Query ---")
    cursor.execute('''
        SELECT et.note_types
        FROM entries e
        JOIN entry_types et ON e.entry_type_id = et.id
        WHERE e.id = ?
    ''', (entry_id,))
    
    row = cursor.fetchone()
    if row and row['note_types']:
        note_types = [nt.strip() for nt in row['note_types'].split(',')]
        print(f"✓ Query returned: {note_types}")
    else:
        print(f"⚠️ Query returned empty or NULL note_types")
        print(f"  Falling back to: ['General']")
    
    conn.close()


def test_related_entries(db_path, entry_id):
    """Test the related entries query"""
    print(f"\n{'='*60}")
    print(f"Testing Related Entries for Entry {entry_id}")
    print(f"{'='*60}")
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Check how many relationships exist
    cursor.execute('''
        SELECT COUNT(*) as count
        FROM relationships
        WHERE from_entry_id = ? OR to_entry_id = ?
    ''', (entry_id, entry_id))
    
    count = cursor.fetchone()['count']
    print(f"Total relationships found: {count}")
    
    if count == 0:
        print("⚠️ No relationships found for this entry!")
        conn.close()
        return
    
    # Test the actual query used in the code
    print(f"\n--- Testing Actual Query ---")
    cursor.execute('''
        SELECT 
            e2.id,
            e2.title,
            et2.singular_label as type,
            r.relationship_type
        FROM relationships r
        JOIN entries e2 ON (
            CASE 
                WHEN r.from_entry_id = ? THEN r.to_entry_id
                ELSE r.from_entry_id
            END = e2.id
        )
        JOIN entry_types et2 ON e2.entry_type_id = et2.id
        WHERE r.from_entry_id = ? OR r.to_entry_id = ?
        LIMIT 20
    ''', (entry_id, entry_id, entry_id))
    
    rows = cursor.fetchall()
    
    if rows:
        print(f"✓ Found {len(rows)} related entries:")
        for i, row in enumerate(rows, 1):
            print(f"  {i}. ID {row['id']}: {row['title']} ({row['type']}) - {row['relationship_type']}")
    else:
        print("❌ Query returned no results!")
        print("\nDebugging: Let's check the relationships table directly...")
        cursor.execute('SELECT * FROM relationships WHERE from_entry_id = ? OR to_entry_id = ?', 
                      (entry_id, entry_id))
        rels = cursor.fetchall()
        for rel in rels:
            print(f"  Relationship: from={rel['from_entry_id']}, to={rel['to_entry_id']}, type={rel['relationship_type']}")
    
    conn.close()


def list_all_entry_types(db_path):
    """List all entry types and their note types"""
    print(f"\n{'='*60}")
    print(f"All Entry Types and Their Note Types")
    print(f"{'='*60}")
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM entry_types ORDER BY singular_label')
    entry_types = cursor.fetchall()
    
    for et in entry_types:
        note_types = et['note_types'] if et['note_types'] else 'NULL'
        print(f"{et['singular_label']:20} → {note_types}")
    
    conn.close()


def main():
    # Default to the Docker container path
    db_path = '/app/data/database.db'
    
    # Check if running outside Docker
    if not os.path.exists(db_path):
        # Try local path
        db_path = './data/database.db'
        if not os.path.exists(db_path):
            print("❌ Database not found!")
            print("   Expected: /app/data/database.db (in Docker)")
            print("   Or: ./data/database.db (local)")
            sys.exit(1)
    
    print(f"Using database: {db_path}")
    
    # List all entry types first
    list_all_entry_types(db_path)
    
    # Test with a specific entry ID (you can pass as argument)
    if len(sys.argv) > 1:
        entry_id = int(sys.argv[1])
    else:
        # Get the first entry as default
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT id, title FROM entries ORDER BY id LIMIT 1')
        row = cursor.fetchone()
        conn.close()
        
        if row:
            entry_id = row[0]
            print(f"\nNo entry ID provided, using first entry: {row[0]} - {row[1]}")
        else:
            print("❌ No entries found in database!")
            sys.exit(1)
    
    # Run tests
    test_note_types(db_path, entry_id)
    test_related_entries(db_path, entry_id)
    
    print(f"\n{'='*60}")
    print("Diagnostic complete!")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()
