#!/usr/bin/env python3
"""
Simple Dashboard Table Creator
Creates Dashboard and DashboardWidget tables in all databases
"""
import sqlite3
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / 'data'

def create_dashboard_tables(db_path):
    """Create Dashboard tables in the specified database"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create schema_migrations table first
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                migration_name TEXT UNIQUE NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                success BOOLEAN DEFAULT TRUE,
                error_message TEXT,
                execution_time_ms INTEGER
            )
        """)
        
        # Check if Dashboard tables already exist
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name IN ('Dashboard', 'DashboardWidget')
        """)
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        if 'Dashboard' in existing_tables and 'DashboardWidget' in existing_tables:
            conn.close()
            return 'already_exists'
        
        # Create Dashboard table
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
        
        # Create DashboardWidget table
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
        
        # Record migration
        cursor.execute("""
            INSERT OR REPLACE INTO schema_migrations 
            (migration_name, success, applied_at)
            VALUES ('add_dashboard_tables.py', TRUE, CURRENT_TIMESTAMP)
        """)
        
        conn.commit()
        conn.close()
        return 'created'
        
    except sqlite3.OperationalError as e:
        if 'readonly' in str(e).lower() or 'locked' in str(e).lower():
            return 'readonly'
        return f'error: {e}'
    except Exception as e:
        return f'error: {e}'

def main():
    """Process all databases"""
    if not DATA_DIR.exists():
        print(f"Error: Data directory not found: {DATA_DIR}")
        return 1
    
    databases = sorted(DATA_DIR.glob('*.db'))
    print(f"Found {len(databases)} databases\n")
    print("="*70)
    
    results = {}
    for db_path in databases:
        # Skip empty databases
        if db_path.stat().st_size == 0:
            print(f"⊘ {db_path.name:25} - Empty file (skipped)")
            results[db_path.name] = 'skipped'
            continue
        
        result = create_dashboard_tables(db_path)
        results[db_path.name] = result
        
        icons = {
            'created': '✓',
            'already_exists': '→',
            'readonly': '🔒',
            'skipped': '⊘'
        }
        
        if result == 'created':
            print(f"✓ {db_path.name:25} - Dashboard tables CREATED")
        elif result == 'already_exists':
            print(f"→ {db_path.name:25} - Tables already exist")
        elif result == 'readonly':
            print(f"🔒 {db_path.name:25} - Database is readonly (permissions issue)")
        elif result.startswith('error'):
            print(f"✗ {db_path.name:25} - {result}")
        else:
            print(f"? {db_path.name:25} - {result}")
    
    # Summary
    print("="*70)
    print("\nSUMMARY:")
    created = sum(1 for r in results.values() if r == 'created')
    exists = sum(1 for r in results.values() if r == 'already_exists')
    errors = sum(1 for r in results.values() if r.startswith('error') or r == 'readonly')
    skipped = sum(1 for r in results.values() if r == 'skipped')
    
    print(f"  Created: {created}")
    print(f"  Already exists: {exists}")
    print(f"  Errors/Readonly: {errors}")
    print(f"  Skipped: {skipped}")
    print(f"  Total: {len(results)}")
    
    if errors > 0:
        print(f"\n⚠ {errors} database(s) need permission fixes:")
        print("  Run: sudo chown $USER:$USER data/*.db")
    
    return 0 if (created + exists > 0) else 1

if __name__ == '__main__':
    sys.exit(main())
