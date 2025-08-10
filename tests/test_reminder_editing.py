#!/usr/bin/env python3
"""
Test script to demonstrate reminder editing functionality.
This script will create a test note with a reminder and show how to edit it.
"""

import sqlite3
import json
from datetime import datetime, timedelta

def main():
    # Connect to the database
    db_path = "template.db"  # Use the template database in root
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # Find an existing entry to attach the note to
        cursor.execute("SELECT id, title FROM Entry LIMIT 1")
        entry = cursor.fetchone()
        
        if not entry:
            print("No entries found. Please create an entry first.")
            return
        
        print(f"Using entry: {entry['title']} (ID: {entry['id']})")
        
        # Create a test note with a reminder
        note_title = "Test Note with Reminder"
        note_text = "This is a test note to demonstrate reminder editing functionality."
        note_type = "Test"
        
        # Insert the note
        cursor.execute("""
            INSERT INTO Note (entry_id, note_title, note_text, type, created_at, image_paths)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (entry['id'], note_title, note_text, note_type, datetime.now().isoformat(), json.dumps([])))
        
        note_id = cursor.lastrowid
        print(f"Created test note with ID: {note_id}")
        
        # Create a reminder notification for tomorrow at 2 PM
        reminder_time = datetime.now() + timedelta(days=1)
        reminder_time = reminder_time.replace(hour=14, minute=0, second=0, microsecond=0)
        
        cursor.execute("""
            INSERT INTO Notification (notification_type, entry_id, note_id, scheduled_for, title, message, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            'note_based',
            entry['id'],
            note_id,
            reminder_time.isoformat(),
            f"Reminder: {note_title}",
            f"Reminder for note: {note_text[:100]}",
            datetime.now().isoformat()
        ))
        
        notification_id = cursor.lastrowid
        print(f"Created reminder notification with ID: {notification_id}")
        print(f"Reminder scheduled for: {reminder_time}")
        
        conn.commit()
        
        print("\n" + "="*50)
        print("TEST NOTE CREATED SUCCESSFULLY!")
        print("="*50)
        print(f"Note ID: {note_id}")
        print(f"Title: {note_title}")
        print(f"Text: {note_text}")
        print(f"Reminder: {reminder_time}")
        print("\nYou can now test the reminder editing functionality by:")
        print("1. Opening the entry in your web browser")
        print("2. Finding this note and clicking 'Open Details'")
        print("3. Clicking the 'Edit' button next to the reminder")
        print("4. Changing the reminder date/time and saving")
        print("5. Or removing the reminder entirely")
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    main()
