#!/usr/bin/env python3
"""
Test script for the new note editing and attachment features
"""

import requests
import tempfile
import os
from pathlib import Path

def test_note_editing_and_attachments():
    """Test the new functionality"""
    
    base_url = "http://localhost:5003"
    entry_id = 1
    
    print("🧪 Testing new note editing and attachment features...")
    
    # First, create a note to test with
    print("\n1. Creating a test note...")
    try:
        data = {
            'note_title': 'Original Title',
            'note_text': 'This is the original content of the note.',
            'note_type': 'General'
        }
        response = requests.post(f"{base_url}/api/entries/{entry_id}/notes", data=data)
        
        if response.status_code == 201:
            result = response.json()
            note_id = result.get('note_id')
            print(f"✅ Note created successfully! Note ID: {note_id}")
        else:
            print(f"❌ Failed to create note: {response.status_code}")
            print(f"   Response: {response.text}")
            return
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Please make sure Flask is running on port 5003")
        return
    except Exception as e:
        print(f"❌ Error creating note: {e}")
        return
    
    # Test editing note content
    print(f"\n2. Testing note content editing (Note ID: {note_id})...")
    try:
        edit_data = {
            'note_title': 'Updated Title',
            'note_text': 'This content has been updated using the new edit feature!'
        }
        response = requests.put(f"{base_url}/api/notes/{note_id}", data=edit_data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Note updated successfully!")
            print(f"   New title: {result.get('note_title')}")
            print(f"   New text: {result.get('note_text')}")
        else:
            print(f"❌ Failed to update note: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error updating note: {e}")
    
    # Test adding attachments to existing note
    print(f"\n3. Testing adding attachments to existing note...")
    try:
        # Create a test file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as temp_file:
            temp_file.write(b'This is a test attachment for the existing note!')
            temp_file_path = temp_file.name
        
        with open(temp_file_path, 'rb') as f:
            files = {'files': ('test_attachment.txt', f, 'text/plain')}
            response = requests.post(f"{base_url}/api/notes/{note_id}/attachments", files=files)
            
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Attachment added successfully!")
            print(f"   Files attached: {len(result.get('file_paths', []))}")
            print(f"   New files: {result.get('new_files', [])}")
        else:
            print(f"❌ Failed to add attachment: {response.status_code}")
            print(f"   Response: {response.text}")
            
        # Clean up temp file
        Path(temp_file_path).unlink(missing_ok=True)
        
    except Exception as e:
        print(f"❌ Error adding attachment: {e}")
    
    # Test getting allowed file types from system parameters
    print(f"\n4. Testing system parameter for allowed file types...")
    try:
        response = requests.get(f"{base_url}/api/system_parameters")
        
        if response.status_code == 200:
            params = response.json()
            allowed_types = params.get('allowed_file_types', 'Not found')
            print(f"✅ Retrieved system parameters!")
            print(f"   Allowed file types: {allowed_types}")
        else:
            print(f"❌ Failed to get system parameters: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error getting system parameters: {e}")
    
    print(f"\n🎉 Testing completed! Note ID {note_id} was used for testing.")
    print("You can now check the UI to see the new features in action!")

if __name__ == "__main__":
    test_note_editing_and_attachments()
