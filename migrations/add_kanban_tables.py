#!/usr/bin/env python3
"""
Migration: Add Kanban Board and Column tables
"""

import sqlite3
import os
import sys

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def migrate():
    """Add KanbanBoard and KanbanColumn tables to the database"""
    
    # Determine database path
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'app.db')
    
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return False
    
    print(f"Connecting to database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create KanbanBoard Table
        print("Creating KanbanBoard table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS KanbanBoard (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                entry_type_id INTEGER NOT NULL,
                is_default INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (entry_type_id) REFERENCES EntryType(id) ON DELETE CASCADE
            );
        ''')
        print("✓ KanbanBoard table created")
        
        # Create KanbanColumn Table
        print("Creating KanbanColumn table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS KanbanColumn (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                board_id INTEGER NOT NULL,
                state_name TEXT NOT NULL,
                display_order INTEGER DEFAULT 0,
                wip_limit INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (board_id) REFERENCES KanbanBoard(id) ON DELETE CASCADE,
                UNIQUE(board_id, state_name)
            );
        ''')
        print("✓ KanbanColumn table created")
        
        conn.commit()
        print("\n✓ Migration completed successfully!")
        return True
        
    except sqlite3.Error as e:
        print(f"\n✗ Migration failed: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == '__main__':
    success = migrate()
    sys.exit(0 if success else 1)
