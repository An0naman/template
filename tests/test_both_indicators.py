#!/usr/bin/env python3
"""
Test note with both reminder and attachment
"""

import requests
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

def test_note_with_both_indicators():
    """Test adding a note with both reminder and attachment"""
    
    base_url = "http://localhost:5002"
    entry_id = 1
    
    # Create a test file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as temp_file:
        temp_file.write(b'This note has both a reminder AND an attachment!')
        temp_file_path = temp_file.name
    
    # Set reminder for tomorrow at 2 PM
    tomorrow = datetime.now() + timedelta(days=1)
    reminder_datetime = tomorrow.replace(hour=14, minute=0, second=0, microsecond=0)
    reminder_str = reminder_datetime.strftime('%Y-%m-%dT%H:%M')
    
    try:
        print("Creating a note with BOTH reminder AND attachment...")
        
        with open(temp_file_path, 'rb') as f:
            files = {'files': ('both_indicators_test.txt', f, 'text/plain')}
            data = {
                'note_title': 'Both Indicators Test',
                'note_text': 'This note has both a reminder AND an attachment. You should see both a bell icon and a paperclip icon!',
                'note_type': 'General',
                'reminder_date': reminder_str,
                'reminder_time': ''
            }
            response = requests.post(f"{base_url}/api/entries/{entry_id}/notes", files=files, data=data)
            
        if response.status_code == 201:
            result = response.json()
            print(f"✅ Note created successfully!")
            print(f"   Note ID: {result.get('note_id')}")
            print(f"   Files attached: {len(result.get('file_paths', []))}")
            print(f"   Reminder set for: {reminder_str}")
            print("\n🔔📎 This note should show BOTH a bell icon AND a paperclip icon!")
        else:
            print(f"❌ Failed to create note: {response.status_code}")
            print(f"   Response: {response.text}")
            
    finally:
        # Clean up temp file
        Path(temp_file_path).unlink(missing_ok=True)

if __name__ == "__main__":
    test_note_with_both_indicators()
