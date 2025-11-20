"""
Test script to verify automatic status change notes are created.
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5000"

def test_auto_status_note():
    """Test that changing an entry's status creates an automatic System note."""
    
    # First, get an existing entry
    print("Fetching entries...")
    response = requests.get(f"{BASE_URL}/api/entries")
    
    if response.status_code != 200:
        print(f"Error fetching entries: {response.status_code}")
        return
    
    entries = response.json()
    if not entries:
        print("No entries found. Please create an entry first.")
        return
    
    # Use the first entry for testing
    entry = entries[0]
    entry_id = entry['id']
    old_status = entry['status']
    
    print(f"\nTesting with Entry ID: {entry_id}")
    print(f"Current Status: {old_status}")
    
    # Get current notes count
    notes_response = requests.get(f"{BASE_URL}/api/entries/{entry_id}/notes")
    if notes_response.status_code == 200:
        old_notes_count = len(notes_response.json())
        print(f"Current notes count: {old_notes_count}")
    else:
        old_notes_count = 0
    
    # Change the status
    new_status = "In Progress" if old_status != "In Progress" else "Completed"
    print(f"\nChanging status to: {new_status}")
    
    update_response = requests.put(
        f"{BASE_URL}/api/entries/{entry_id}",
        json={"status": new_status}
    )
    
    if update_response.status_code != 200:
        print(f"Error updating entry: {update_response.status_code}")
        print(update_response.json())
        return
    
    print(f"✓ Entry updated successfully")
    
    # Check if a new note was created
    print("\nChecking for auto-generated note...")
    notes_response = requests.get(f"{BASE_URL}/api/entries/{entry_id}/notes")
    
    if notes_response.status_code != 200:
        print(f"Error fetching notes: {notes_response.status_code}")
        return
    
    new_notes = notes_response.json()
    new_notes_count = len(new_notes)
    
    print(f"New notes count: {new_notes_count}")
    
    if new_notes_count > old_notes_count:
        # Find the new note
        latest_note = new_notes[-1]  # Assuming it's the last one
        print(f"\n✓ Auto-generated note created!")
        print(f"  Note ID: {latest_note.get('id')}")
        print(f"  Title: {latest_note.get('note_title')}")
        print(f"  Type: {latest_note.get('type')}")
        print(f"  Content: {latest_note.get('note_text')}")
        print(f"  Created: {latest_note.get('created_at')}")
        
        # Verify it's a System note with the correct content
        if latest_note.get('type') == 'System':
            print("\n✓ Note type is 'System' as expected")
        else:
            print(f"\n✗ Warning: Note type is '{latest_note.get('type')}', expected 'System'")
        
        expected_content = f"Status automatically changed from '{old_status}' to '{new_status}'"
        if latest_note.get('note_text') == expected_content:
            print("✓ Note content matches expected format")
        else:
            print(f"✗ Note content doesn't match. Expected: {expected_content}")
    else:
        print("\n✗ No new note was created")
    
    # Optionally, change status back
    print(f"\n\nChanging status back to: {old_status}")
    restore_response = requests.put(
        f"{BASE_URL}/api/entries/{entry_id}",
        json={"status": old_status}
    )
    
    if restore_response.status_code == 200:
        print("✓ Status restored")
    else:
        print(f"✗ Error restoring status: {restore_response.status_code}")

if __name__ == "__main__":
    try:
        test_auto_status_note()
    except Exception as e:
        print(f"\n✗ Error during test: {str(e)}")
