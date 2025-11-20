#!/usr/bin/env python3
"""
Test script for the new URL bookmarks functionality
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:5000"  # Adjust as needed
ENTRY_ID = 1

def test_url_bookmarks():
    """Test creating and updating notes with URL bookmarks"""
    
    print("Testing URL bookmarks functionality...")
    
    # Test data with URL bookmarks
    note_data = {
        "note_title": "Test Note with URL Bookmarks",
        "note_text": "This note contains some useful links",
        "note_type": "General",
        "url_bookmarks": [
            {
                "url": "https://www.example.com",
                "friendly_name": "Example Website"
            },
            {
                "url": "https://github.com/your-repo",
                "friendly_name": "GitHub Repository"
            },
            {
                "url": "https://docs.python.org",
                "friendly_name": "Python Documentation"
            }
        ]
    }
    
    try:
        # Create the note with URL bookmarks
        print("Creating note with URL bookmarks...")
        response = requests.post(
            f"{BASE_URL}/api/entries/{ENTRY_ID}/notes",
            headers={"Content-Type": "application/json"},
            data=json.dumps(note_data)
        )
        
        if response.status_code == 201:
            result = response.json()
            note_id = result.get('note_id')
            print(f"✅ Note created successfully! Note ID: {note_id}")
            
            # Retrieve the note to verify URL bookmarks
            print("Retrieving notes to verify URL bookmarks...")
            get_response = requests.get(f"{BASE_URL}/api/entries/{ENTRY_ID}/notes")
            
            if get_response.status_code == 200:
                notes = get_response.json()
                created_note = None
                
                for note in notes:
                    if note['id'] == note_id:
                        created_note = note
                        break
                
                if created_note and 'url_bookmarks' in created_note:
                    print("✅ URL bookmarks found in retrieved note:")
                    for i, bookmark in enumerate(created_note['url_bookmarks'], 1):
                        print(f"   {i}. {bookmark['friendly_name']}: {bookmark['url']}")
                    
                    # Test updating the note with modified bookmarks
                    print("\nTesting note update with modified URL bookmarks...")
                    updated_bookmarks = [
                        {
                            "url": "https://www.example.com",
                            "friendly_name": "Updated Example Site"
                        },
                        {
                            "url": "https://stackoverflow.com",
                            "friendly_name": "Stack Overflow"
                        }
                    ]
                    
                    update_data = {
                        'note_title': 'Updated Note Title',
                        'note_text': 'Updated note content',
                        'url_bookmarks': json.dumps(updated_bookmarks)
                    }
                    
                    update_response = requests.put(
                        f"{BASE_URL}/api/notes/{note_id}",
                        data=update_data
                    )
                    
                    if update_response.status_code == 200:
                        print("✅ Note updated successfully with modified URL bookmarks")
                        update_result = update_response.json()
                        if 'url_bookmarks' in update_result:
                            print("Updated bookmarks:")
                            for i, bookmark in enumerate(update_result['url_bookmarks'], 1):
                                print(f"   {i}. {bookmark['friendly_name']}: {bookmark['url']}")
                    else:
                        print(f"❌ Failed to update note: {update_response.status_code}")
                        print(f"Response: {update_response.text}")
                
                else:
                    print("❌ URL bookmarks not found in retrieved note")
                    print(f"Note data: {json.dumps(created_note, indent=2)}")
            else:
                print(f"❌ Failed to retrieve notes: {get_response.status_code}")
        else:
            print(f"❌ Failed to create note: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to Flask app. Make sure it's running.")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    test_url_bookmarks()
