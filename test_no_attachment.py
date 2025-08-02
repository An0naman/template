#!/usr/bin/env python3
"""
Add a note without attachments for comparison
"""

import requests

def test_note_without_attachment():
    """Test adding a note without attachment"""
    
    base_url = "http://localhost:5002"
    entry_id = 1
    
    print("Creating a note WITHOUT attachment...")
    
    data = {
        'note_title': 'No Attachment Note',
        'note_text': 'This note has no attachments, so it should not show a paperclip icon.',
        'note_type': 'General',
        'reminder_date': '',
        'reminder_time': ''
    }
    response = requests.post(f"{base_url}/api/entries/{entry_id}/notes", json=data)
    
    if response.status_code == 201:
        result = response.json()
        print(f"✅ Note created successfully!")
        print(f"   Note ID: {result.get('note_id')}")
        print(f"   Files attached: {len(result.get('file_paths', []))}")
        print("\n📝 This note should NOT have a paperclip icon!")
    else:
        print(f"❌ Failed to create note: {response.status_code}")
        print(f"   Response: {response.text}")

if __name__ == "__main__":
    test_note_without_attachment()
