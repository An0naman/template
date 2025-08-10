#!/usr/bin/env python3
"""
Test creating a note with a reminder date to verify notification creation
"""

import requests
import json
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://172.20.0.2:5001"  # Based on HAR log - Flask app running in Docker
ENTRY_ID = 1

def test_note_with_reminder():
    print("Testing note creation with reminder date...")
    
    # Create a reminder for 2 minutes from now
    future_time = datetime.now() + timedelta(minutes=2)
    reminder_datetime = future_time.strftime("%Y-%m-%dT%H:%M")
    
    # Note data with reminder
    note_data = {
        "note_title": "Test Reminder Note",
        "note_text": "This note should create a notification in 2 minutes",
        "note_type": "General",
        "reminder_date": reminder_datetime
    }
    
    print(f"Creating note with reminder for: {reminder_datetime}")
    
    try:
        # Create the note
        response = requests.post(
            f"{BASE_URL}/api/entries/{ENTRY_ID}/notes",
            headers={"Content-Type": "application/json"},
            data=json.dumps(note_data)
        )
        
        if response.status_code == 201:
            result = response.json()
            print(f"✅ Note created successfully! Note ID: {result.get('note_id')}")
            
            # Check if notification was created
            print("Checking for notifications...")
            notifications_response = requests.get(f"{BASE_URL}/api/notifications")
            
            if notifications_response.status_code == 200:
                notifications = notifications_response.json()
                print(f"Found {len(notifications)} total notifications")
                
                # Look for our note-based notification
                for notif in notifications:
                    if notif.get('notification_type') == 'note_based' and 'Test Reminder Note' in notif.get('title', ''):
                        print(f"✅ Found notification: {notif['title']}")
                        print(f"   Scheduled for: {notif.get('scheduled_for')}")
                        print(f"   Entry ID: {notif.get('entry_id')}")
                        print(f"   Priority: {notif.get('priority')}")
                        return True
                
                print("❌ No matching notification found")
                print("All notifications:", json.dumps(notifications, indent=2))
                
            else:
                print(f"❌ Failed to fetch notifications: {notifications_response.status_code}")
                
        else:
            print(f"❌ Failed to create note: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to Flask app. Make sure it's running on the correct port.")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return False

if __name__ == "__main__":
    test_note_with_reminder()
