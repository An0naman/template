#!/usr/bin/env python3
"""
Test the notification system by creating test notifications.
"""

import sqlite3
import os
from datetime import datetime, timedelta

def test_notifications():
    # Get the database path
    db_path = 'data/template.db'
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get an existing entry to use for testing
        cursor.execute("SELECT id, title FROM Entry LIMIT 1")
        entry = cursor.fetchone()
        
        if not entry:
            print("No entries found in database. Creating a test entry...")
            # Get an entry type
            cursor.execute("SELECT id FROM EntryType LIMIT 1")
            entry_type = cursor.fetchone()
            if not entry_type:
                print("No entry types found. Cannot create test entry.")
                return False
            
            cursor.execute(
                "INSERT INTO Entry (title, entry_type_id, created_at) VALUES (?, ?, ?)",
                ("Test Entry for Notifications", entry_type[0], datetime.now().isoformat())
            )
            entry_id = cursor.lastrowid
            entry_title = "Test Entry for Notifications"
        else:
            entry_id, entry_title = entry
        
        print(f"Using entry: {entry_title} (ID: {entry_id})")
        
        # Create test notifications
        now = datetime.now()
        future_date = now + timedelta(minutes=5)  # 5 minutes from now
        past_date = now - timedelta(minutes=10)   # 10 minutes ago (should show immediately)
        
        test_notifications = [
            {
                'title': 'Immediate Test Notification',
                'message': 'This notification should appear immediately',
                'notification_type': 'manual',
                'priority': 'high',
                'entry_id': entry_id,
                'scheduled_for': None  # Show immediately
            },
            {
                'title': 'Past Due Reminder',
                'message': 'This was scheduled for the past and should appear now',
                'notification_type': 'note_based',
                'priority': 'medium',
                'entry_id': entry_id,
                'scheduled_for': past_date.isoformat()
            },
            {
                'title': 'Future Reminder',
                'message': f'This is scheduled for {future_date.strftime("%H:%M")} and should not appear yet',
                'notification_type': 'note_based',
                'priority': 'low',
                'entry_id': entry_id,
                'scheduled_for': future_date.isoformat()
            }
        ]
        
        print(f"\nCreating {len(test_notifications)} test notifications...")
        
        for i, notif in enumerate(test_notifications, 1):
            cursor.execute('''
                INSERT INTO Notification 
                (title, message, notification_type, priority, entry_id, scheduled_for)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                notif['title'],
                notif['message'], 
                notif['notification_type'],
                notif['priority'],
                notif['entry_id'],
                notif['scheduled_for']
            ))
            print(f"  {i}. Created: {notif['title']}")
        
        conn.commit()
        
        # Show current notifications that should be visible
        current_time = now.isoformat()
        cursor.execute('''
            SELECT id, title, message, scheduled_for, priority
            FROM Notification 
            WHERE is_dismissed = 0 
            AND (scheduled_for IS NULL OR scheduled_for <= ?)
            ORDER BY priority DESC, created_at DESC
        ''', (current_time,))
        
        visible_notifications = cursor.fetchall()
        
        print(f"\nNotifications that should be visible now (current time: {current_time}):")
        if visible_notifications:
            for notif in visible_notifications:
                notif_id, title, message, scheduled, priority = notif
                scheduled_str = f" (scheduled: {scheduled})" if scheduled else " (immediate)"
                print(f"  - [{priority.upper()}] {title}{scheduled_str}")
        else:
            print("  No notifications should be visible right now.")
        
        # Show future notifications
        cursor.execute('''
            SELECT id, title, scheduled_for
            FROM Notification 
            WHERE is_dismissed = 0 
            AND scheduled_for IS NOT NULL 
            AND scheduled_for > ?
            ORDER BY scheduled_for ASC
        ''', (current_time,))
        
        future_notifications = cursor.fetchall()
        
        print(f"\nFuture notifications:")
        if future_notifications:
            for notif in future_notifications:
                notif_id, title, scheduled = notif
                print(f"  - {title} (scheduled: {scheduled})")
        else:
            print("  No future notifications.")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error testing notifications: {e}")
        return False

if __name__ == "__main__":
    print("Testing notification system...")
    if test_notifications():
        print("\n✅ Notification test completed!")
        print("\nNow you can:")
        print("1. Visit your app in the browser")
        print("2. Look for the notification bell icon")
        print("3. Test creating a note with a future reminder date")
        print("4. Check that notifications appear and can be dismissed")
    else:
        print("\n❌ Notification test failed!")
