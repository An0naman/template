#!/usr/bin/env python3
"""
Script to initialize notification tables in the database
"""

import sqlite3
import os
from datetime import datetime

def init_notification_tables():
    # Find the correct database path
    db_paths = ['data/template.db', 'template.db', 'data/app.db']
    db_path = None
    
    for path in db_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        print("No database found! Please run the app first to create the database.")
        return
    
    print(f"Using database: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if Notification table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Notification';")
        if not cursor.fetchone():
            print("Creating Notification table...")
            cursor.execute('''
                CREATE TABLE Notification (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    message TEXT NOT NULL,
                    notification_type TEXT NOT NULL DEFAULT 'manual',
                    priority TEXT NOT NULL DEFAULT 'medium',
                    entry_id INTEGER,
                    note_id INTEGER,
                    is_read BOOLEAN DEFAULT 0,
                    is_dismissed BOOLEAN DEFAULT 0,
                    created_at TEXT NOT NULL,
                    read_at TEXT,
                    scheduled_for TEXT,
                    FOREIGN KEY (entry_id) REFERENCES Entry (id) ON DELETE CASCADE,
                    FOREIGN KEY (note_id) REFERENCES Note (id) ON DELETE CASCADE
                )
            ''')
            print("✓ Notification table created")
        else:
            print("✓ Notification table already exists")
        
        # Check if NotificationRule table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='NotificationRule';")
        if not cursor.fetchone():
            print("Creating NotificationRule table...")
            cursor.execute('''
                CREATE TABLE NotificationRule (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    sensor_type TEXT NOT NULL,
                    condition_type TEXT NOT NULL,
                    threshold_value REAL NOT NULL,
                    entry_type_id INTEGER,
                    priority TEXT DEFAULT 'medium',
                    cooldown_minutes INTEGER DEFAULT 60,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (entry_type_id) REFERENCES EntryType (id) ON DELETE CASCADE
                )
            ''')
            print("✓ NotificationRule table created")
        else:
            print("✓ NotificationRule table already exists")
        
        conn.commit()
        
        # Test creating a notification
        print("\nTesting notification creation...")
        test_notification_id = create_test_notification(cursor)
        conn.commit()
        
        # Test reading notifications
        print("Testing notification reading...")
        test_read_notifications(cursor)
        
        print("\nNotification system initialized successfully!")
        return test_notification_id
        
    except Exception as e:
        print(f"Error initializing notification tables: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()

def create_test_notification(cursor):
    """Create a test notification"""
    try:
        cursor.execute('''
            INSERT INTO Notification 
            (title, message, notification_type, priority, entry_id, created_at, scheduled_for)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            "Test Notification",
            "This is a test notification to verify the system works",
            "manual",
            "medium",
            1,  # Assuming entry ID 1 exists
            datetime.now().isoformat(),
            datetime.now().isoformat()  # Scheduled for now
        ))
        
        notification_id = cursor.lastrowid
        print(f"✓ Created test notification with ID: {notification_id}")
        return notification_id
        
    except Exception as e:
        print(f"Error creating test notification: {e}")
        return None

def test_read_notifications(cursor):
    """Test reading notifications"""
    try:
        # Get all notifications
        cursor.execute('SELECT * FROM Notification ORDER BY created_at DESC')
        notifications = cursor.fetchall()
        
        print(f"Found {len(notifications)} notifications:")
        for notification in notifications:
            print(f"  ID: {notification[0]}, Title: {notification[1]}, Type: {notification[3]}")
        
        # Test the specific query used by the API
        cursor.execute('''
            SELECT n.*, e.title as entry_title
            FROM Notification n
            LEFT JOIN Entry e ON n.entry_id = e.id
            WHERE (n.entry_id = ? OR n.entry_id IS NULL)
            AND (n.scheduled_for IS NULL OR n.scheduled_for <= ?)
            ORDER BY n.created_at DESC
        ''', (1, datetime.now().isoformat()))
        
        api_notifications = cursor.fetchall()
        print(f"API query returned {len(api_notifications)} notifications")
        
    except Exception as e:
        print(f"Error reading notifications: {e}")

if __name__ == "__main__":
    init_notification_tables()
