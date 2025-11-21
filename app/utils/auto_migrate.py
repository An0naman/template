#!/usr/bin/env python3
"""
Auto-Migration System for Framework
====================================
Automatically runs pending migrations when the app starts.
This ensures downstream apps always have the correct schema.
"""

import sqlite3
import os
import sys
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class AutoMigration:
    """Simple auto-migration system that runs on app startup"""
    
    def __init__(self, db_path, migrations_dir=None):
        self.db_path = Path(db_path)
        
        # Try to find migrations directory
        if migrations_dir:
            self.migrations_dir = Path(migrations_dir)
        else:
            # Look in standard locations
            app_dir = Path(__file__).parent.parent
            self.migrations_dir = app_dir / 'migrations'
            if not self.migrations_dir.exists():
                # Try old location
                self.migrations_dir = app_dir.parent / 'migrations'
    
    def ensure_migration_table(self):
        """Create schema_migrations table if it doesn't exist"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
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
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_migration_name 
                ON schema_migrations(migration_name)
            """)
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Failed to create migration tracking table: {e}")
            return False
    
    def is_migration_applied(self, migration_name):
        """Check if migration was already applied"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM schema_migrations 
                WHERE migration_name = ? AND success = TRUE
            """, (migration_name,))
            count = cursor.fetchone()[0]
            conn.close()
            return count > 0
        except:
            return False
    
    def record_migration(self, migration_name, success=True, error_msg=None, exec_time=0):
        """Record migration in tracking table"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO schema_migrations 
                (migration_name, success, error_message, execution_time_ms, applied_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (migration_name, success, error_msg, exec_time))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to record migration: {e}")
    
    def check_table_exists(self, table_name):
        """Check if a table exists"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name=?
            """, (table_name,))
            result = cursor.fetchone() is not None
            conn.close()
            return result
        except:
            return False
    
    def apply_critical_migrations(self):
        """
        Apply critical migrations inline without importing migration files.
        This ensures Dashboard and other essential tables exist.
        """
        logger.info("Checking for critical schema updates...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Migration: Add Dashboard tables
            migration_name = "add_dashboard_tables.py"
            if not self.is_migration_applied(migration_name):
                if not self.check_table_exists('Dashboard'):
                    logger.info("Creating Dashboard tables...")
                    start_time = datetime.now()
                    
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
                    exec_time = int((datetime.now() - start_time).total_seconds() * 1000)
                    self.record_migration(migration_name, success=True, exec_time=exec_time)
                    logger.info(f"✓ Dashboard tables created ({exec_time}ms)")
                else:
                    # Tables exist, just record the migration
                    self.record_migration(migration_name, success=True, exec_time=0)
                    logger.info("✓ Dashboard tables already exist")
            
            # Add more critical migrations here as needed
            # Example: Add EntryState, SavedSearch, etc.
            
            # Migration: Add EntryState table
            migration_name = "add_entry_state_table.py"
            if not self.is_migration_applied(migration_name):
                if not self.check_table_exists('EntryState'):
                    logger.info("Creating EntryState table...")
                    start_time = datetime.now()
                    
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
                    
                    conn.commit()
                    exec_time = int((datetime.now() - start_time).total_seconds() * 1000)
                    self.record_migration(migration_name, success=True, exec_time=exec_time)
                    logger.info(f"✓ EntryState table created ({exec_time}ms)")
                else:
                    self.record_migration(migration_name, success=True, exec_time=0)
            
            # Migration: Add SavedSearch table
            migration_name = "add_saved_search_table.py"
            if not self.is_migration_applied(migration_name):
                if not self.check_table_exists('SavedSearch'):
                    logger.info("Creating SavedSearch table...")
                    start_time = datetime.now()
                    
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
                    
                    conn.commit()
                    exec_time = int((datetime.now() - start_time).total_seconds() * 1000)
                    self.record_migration(migration_name, success=True, exec_time=exec_time)
                    logger.info(f"✓ SavedSearch table created ({exec_time}ms)")
                else:
                    self.record_migration(migration_name, success=True, exec_time=0)
            
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error applying critical migrations: {e}")
            if 'conn' in locals():
                conn.rollback()
                conn.close()
            return False
    
    def run(self):
        """Run auto-migration process"""
        if not self.db_path.exists():
            logger.info(f"Database not found: {self.db_path}")
            return False
        
        # Ensure migration tracking table exists
        if not self.ensure_migration_table():
            logger.error("Failed to initialize migration tracking")
            return False
        
        # Apply critical inline migrations
        if not self.apply_critical_migrations():
            logger.error("Failed to apply critical migrations")
            return False
        
        logger.info("✓ Auto-migration completed")
        return True


def run_auto_migration(db_path):
    """
    Convenience function to run auto-migration.
    Call this from app initialization (e.g., in run.py or __init__.py)
    
    Example:
        from app.utils.auto_migrate import run_auto_migration
        run_auto_migration(app.config['DATABASE_PATH'])
    """
    try:
        migrator = AutoMigration(db_path)
        return migrator.run()
    except Exception as e:
        logger.error(f"Auto-migration failed: {e}")
        return False


if __name__ == '__main__':
    # For testing
    import sys
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
        success = run_auto_migration(db_path)
        sys.exit(0 if success else 1)
    else:
        print("Usage: python auto_migrate.py <database_path>")
        sys.exit(1)
