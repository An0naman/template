#!/usr/bin/env python3
"""
Initialize notification tables in the database.
This script creates the missing Notification and NotificationRule tables.
"""

import sqlite3
import os
from datetime import datetime

def init_notification_tables():
    # Get the database path - Flask app uses root template.db
    db_path = 'template.db'
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("Creating Notification table...")
        # Create Notification Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Notification (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                notification_type TEXT NOT NULL, -- 'note_based', 'sensor_based', 'manual'
                priority TEXT NOT NULL DEFAULT 'medium', -- 'low', 'medium', 'high', 'critical'
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                note_id INTEGER, -- Related note (optional for note-based notifications)
                scheduled_for TEXT, -- ISO datetime when notification should be shown
                entry_id INTEGER, -- Related entry (optional)
                is_read INTEGER NOT NULL DEFAULT 0, -- Boolean: 0 = unread, 1 = read
                is_dismissed INTEGER NOT NULL DEFAULT 0, -- Boolean: 0 = active, 1 = dismissed
                read_at TEXT, -- When the notification was read
                dismissed_at TEXT, -- When the notification was dismissed
                FOREIGN KEY (note_id) REFERENCES Note(id) ON DELETE CASCADE,
                FOREIGN KEY (entry_id) REFERENCES Entry(id) ON DELETE CASCADE
            )
        ''')
        
        print("Creating NotificationRule table...")
        # Create NotificationRule Table for sensor-based notifications
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS NotificationRule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                entry_type_id INTEGER, -- Apply to specific entry type (optional)
                entry_id INTEGER, -- Apply to specific entry (optional)
                sensor_type TEXT NOT NULL, -- Which sensor type to monitor
                condition_type TEXT NOT NULL, -- 'greater_than', 'less_than', 'equals', 'between', 'change_rate'
                threshold_value REAL NOT NULL, -- Primary threshold value
                threshold_value_secondary REAL, -- Secondary threshold (for 'between' conditions)
                threshold_unit TEXT, -- Unit for the threshold
                notification_title TEXT NOT NULL,
                notification_message TEXT NOT NULL,
                priority TEXT NOT NULL DEFAULT 'medium', -- 'low', 'medium', 'high', 'critical'
                cooldown_minutes INTEGER DEFAULT 60, -- Minimum minutes between notifications for same rule
                is_active INTEGER NOT NULL DEFAULT 1, -- Boolean: 0 = disabled, 1 = enabled
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (entry_type_id) REFERENCES EntryType(id) ON DELETE CASCADE,
                FOREIGN KEY (entry_id) REFERENCES Entry(id) ON DELETE CASCADE
            )
        ''')
        
        # Commit the changes
        conn.commit()
        
        # Verify tables were created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('Notification', 'NotificationRule')")
        created_tables = cursor.fetchall()
        
        print(f"Successfully created {len(created_tables)} notification tables:")
        for table in created_tables:
            print(f"  - {table[0]}")
        
        # Check if we have any existing notifications to test with
        cursor.execute("SELECT COUNT(*) FROM Notification")
        notification_count = cursor.fetchone()[0]
        print(f"Current notifications in database: {notification_count}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error creating notification tables: {e}")
        return False

if __name__ == "__main__":
    print("Initializing notification tables...")
    if init_notification_tables():
        print("✅ Notification tables initialized successfully!")
    else:
        print("❌ Failed to initialize notification tables!")
