#!/usr/bin/env python3
"""
Test script to create and test enhanced reminder progress functionality
"""

import requests
import json
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://192.168.68.104:5001"
ENTRY_ID = 1  # Use existing entry

def test_reminder_progress():
    """Test the enhanced reminder progress functionality"""
    print("🔔 Testing Enhanced Reminder Progress Functionality")
    print("=" * 60)
    
    # Test data - create different types of reminders
    test_notes = [
        {
            "title": "Overdue Reminder Test",
            "text": "This note has an overdue reminder for testing",
            "reminder": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%dT%H:%M")
        },
        {
            "title": "Due Soon Reminder",
            "text": "This reminder is due in 1 hour",
            "reminder": (datetime.now() + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M")
        },
        {
            "title": "Future Reminder",
            "text": "This reminder is scheduled for tomorrow",
            "reminder": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M")
        },
        {
            "title": "Next Week Reminder",
            "text": "This reminder is scheduled for next week",
            "reminder": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%dT%H:%M")
        }
    ]
    
    print(f"Creating test notes with reminders for entry {ENTRY_ID}...")
    
    for i, note_data in enumerate(test_notes, 1):
        print(f"\n📝 Creating note {i}: {note_data['title']}")
        print(f"   Reminder scheduled for: {note_data['reminder']}")
        
        # Create note with reminder
        form_data = {
            'note_title': note_data['title'],
            'note_text': note_data['text'],
            'note_type': 'General',
            'reminder_date': note_data['reminder']
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/entries/{ENTRY_ID}/notes",
                data=form_data
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Note created successfully with ID: {result.get('note_id')}")
            else:
                print(f"   ❌ Failed to create note: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Error creating note: {e}")
    
    print(f"\n🔍 Testing reminder progress summary...")
    
    # Test fetching notes to see the reminder progress
    try:
        response = requests.get(f"{BASE_URL}/api/entries/{ENTRY_ID}/notes")
        if response.status_code == 200:
            notes = response.json()
            notes_with_reminders = [note for note in notes if note.get('reminder')]
            
            print(f"   📊 Found {len(notes_with_reminders)} notes with reminders")
            
            # Categorize reminders
            now = datetime.now()
            overdue = []
            upcoming = []
            
            for note in notes_with_reminders:
                reminder_date = datetime.fromisoformat(note['reminder']['scheduled_for'].replace('Z', '+00:00'))
                if reminder_date <= now:
                    overdue.append(note)
                else:
                    upcoming.append(note)
            
            print(f"   🚨 Overdue reminders: {len(overdue)}")
            print(f"   ⏰ Upcoming reminders: {len(upcoming)}")
            
            for note in overdue:
                print(f"      - {note['note_title']} (Overdue)")
            
            for note in upcoming:
                reminder_time = datetime.fromisoformat(note['reminder']['scheduled_for'].replace('Z', '+00:00'))
                time_until = reminder_time - now
                days = time_until.days
                hours = time_until.seconds // 3600
                print(f"      - {note['note_title']} (Due in {days}d {hours}h)")
                
        else:
            print(f"   ❌ Failed to fetch notes: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error fetching notes: {e}")
    
    print(f"\n🌐 Open the entry detail page to see the enhanced reminder display:")
    print(f"   👉 {BASE_URL}/entry/{ENTRY_ID}")
    print("\nExpected enhancements:")
    print("   1. ✨ Reminder Progress Summary section at the top of Notes")
    print("   2. 🎯 Color-coded badges (Overdue, Upcoming, Completed, Dismissed)")
    print("   3. 📅 Next upcoming reminder preview")
    print("   4. 🔗 'View All' button to highlight reminder notes")
    print("   5. 💎 Enhanced modal with detailed reminder status")
    print("   6. ⏱️  Relative time indicators (in X hours/days)")

if __name__ == "__main__":
    test_reminder_progress()
