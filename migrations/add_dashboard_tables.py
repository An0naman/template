#!/usr/bin/env python3
"""
Migration: Add Dashboard and DashboardWidget tables
"""

import sqlite3
import os
import sys

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def migrate():
    """Add Dashboard and DashboardWidget tables to the database"""
    
    # Determine database path
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'app.db')
    
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return False
    
    print(f"Connecting to database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create SavedSearch Table
        print("Creating SavedSearch table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS SavedSearch (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                search_term TEXT DEFAULT '',
                type_filter TEXT DEFAULT '',
                status_filter TEXT DEFAULT '',
                specific_states TEXT DEFAULT '',
                date_range TEXT DEFAULT '',
                sort_by TEXT DEFAULT 'created_desc',
                content_display TEXT DEFAULT '',
                result_limit TEXT DEFAULT '50',
                is_default INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        
        # Create EntryState Table
        print("Creating EntryState table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS EntryState (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_type_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                category TEXT NOT NULL CHECK(category IN ('active', 'inactive')),
                color TEXT DEFAULT '#6c757d',
                display_order INTEGER DEFAULT 0,
                is_default INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(entry_type_id, name),
                FOREIGN KEY (entry_type_id) REFERENCES EntryType(id) ON DELETE CASCADE
            );
        ''')
        
        # Create Dashboard Table
        print("Creating Dashboard table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Dashboard (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                is_default INTEGER DEFAULT 0,
                layout_config TEXT DEFAULT '{"cols": 12, "rowHeight": 100}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        
        # Create DashboardWidget Table
        print("Creating DashboardWidget table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS DashboardWidget (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dashboard_id INTEGER NOT NULL,
                widget_type TEXT NOT NULL,
                title TEXT NOT NULL,
                position_x INTEGER DEFAULT 0,
                position_y INTEGER DEFAULT 0,
                width INTEGER DEFAULT 4,
                height INTEGER DEFAULT 2,
                config TEXT DEFAULT '{}',
                data_source_type TEXT,
                data_source_id INTEGER,
                refresh_interval INTEGER DEFAULT 300,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (dashboard_id) REFERENCES Dashboard(id) ON DELETE CASCADE
            );
        ''')
        
        conn.commit()
        
        # Verify tables were created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('SavedSearch', 'EntryState', 'Dashboard', 'DashboardWidget')")
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = ['SavedSearch', 'EntryState', 'Dashboard', 'DashboardWidget']
        missing_tables = [t for t in expected_tables if t not in tables]
        
        if not missing_tables:
            print("✓ All required tables created successfully")
            print(f"  Tables found: {', '.join(tables)}")
            return True
        else:
            print(f"✗ Error: Some tables were not created")
            print(f"  Tables found: {', '.join(tables)}")
            print(f"  Missing tables: {', '.join(missing_tables)}")
            return False
        
    except Exception as e:
        print(f"✗ Error during migration: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    print("=" * 60)
    print("Migration: Add Dashboard Tables")
    print("=" * 60)
    success = migrate()
    print("=" * 60)
    if success:
        print("Migration completed successfully!")
        sys.exit(0)
    else:
        print("Migration failed!")
        sys.exit(1)
