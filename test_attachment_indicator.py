#!/usr/bin/env python3
"""
Quick test to add a note with attachment through the API
to verify attachment indicators are showing
"""

import requests
import tempfile
from pathlib import Path

def test_attachment_indicator():
    """Test adding a note with attachment to see the indicator"""
    
    base_url = "http://localhost:5002"
    entry_id = 1
    
    # Create a test file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as temp_file:
        temp_file.write(b'This is a test file for attachment indicator verification.')
        temp_file_path = temp_file.name
    
    try:
        print("Creating a note with attachment...")
        
        with open(temp_file_path, 'rb') as f:
            files = {'files': ('test_attachment_indicator.txt', f, 'text/plain')}
            data = {
                'note_title': 'Test Attachment Indicator',
                'note_text': 'This note has an attachment to test the paperclip icon indicator.',
                'note_type': 'General',
                'reminder_date': '',
                'reminder_time': ''
            }
            response = requests.post(f"{base_url}/api/entries/{entry_id}/notes", files=files, data=data)
            
        if response.status_code == 201:
            result = response.json()
            print(f"✅ Note created successfully!")
            print(f"   Note ID: {result.get('note_id')}")
            print(f"   Files attached: {len(result.get('file_paths', []))}")
            if result.get('file_paths'):
                for file_path in result['file_paths']:
                    print(f"     - {file_path}")
            print("\n🔗 Check the UI at http://localhost:5002/entry/1 to see the paperclip icon!")
        else:
            print(f"❌ Failed to create note: {response.status_code}")
            print(f"   Response: {response.text}")
            
    finally:
        # Clean up temp file
        Path(temp_file_path).unlink(missing_ok=True)

if __name__ == "__main__":
    test_attachment_indicator()
