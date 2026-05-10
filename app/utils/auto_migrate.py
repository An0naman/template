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
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


def _get_conn(db_path):
    """Return a DB connection — MariaDB if DATABASE_URL is set, else SQLite."""
    database_url = os.environ.get('DATABASE_URL', '')
    if database_url.startswith('mysql'):
        import pymysql
        parsed = urlparse(database_url)
        return pymysql.connect(
            host=parsed.hostname,
            port=parsed.port or 3306,
            user=parsed.username,
            password=parsed.password,
            database=parsed.path.lstrip('/'),
            charset='utf8mb4',
            autocommit=False,
            connect_timeout=10,
        )
    return sqlite3.connect(db_path)


def _placeholder(database_url=None):
    """Return the correct placeholder for the active DB driver."""
    url = database_url or os.environ.get('DATABASE_URL', '')
    return '%s' if url.startswith('mysql') else '?'


def _is_mysql():
    return os.environ.get('DATABASE_URL', '').startswith('mysql')


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
            conn = _get_conn(self.db_path)
            cursor = conn.cursor()

            if _is_mysql():
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS schema_migrations (
                        id INTEGER PRIMARY KEY AUTO_INCREMENT,
                        migration_name VARCHAR(500) UNIQUE NOT NULL,
                        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        success BOOLEAN DEFAULT TRUE,
                        error_message LONGTEXT,
                        execution_time_ms INTEGER
                    )
                """)
            else:
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
            conn = _get_conn(self.db_path)
            cursor = conn.cursor()
            ph = _placeholder()
            cursor.execute(f"""
                SELECT COUNT(*) FROM schema_migrations 
                WHERE migration_name = {ph} AND success = TRUE
            """, (migration_name,))
            row = cursor.fetchone()
            count = row[0] if row else 0
            conn.close()
            return count > 0
        except:
            return False
    
    def record_migration(self, migration_name, success=True, error_msg=None, exec_time=0):
        """Record migration in tracking table"""
        try:
            conn = _get_conn(self.db_path)
            cursor = conn.cursor()
            ph = _placeholder()
            if _is_mysql():
                cursor.execute(f"""
                    INSERT INTO schema_migrations 
                    (migration_name, success, error_message, execution_time_ms, applied_at)
                    VALUES ({ph}, {ph}, {ph}, {ph}, CURRENT_TIMESTAMP)
                    ON DUPLICATE KEY UPDATE
                        success={ph}, error_message={ph}, execution_time_ms={ph}, applied_at=CURRENT_TIMESTAMP
                """, (migration_name, success, error_msg, exec_time, success, error_msg, exec_time))
            else:
                cursor.execute(f"""
                    INSERT OR REPLACE INTO schema_migrations 
                    (migration_name, success, error_message, execution_time_ms, applied_at)
                    VALUES ({ph}, {ph}, {ph}, {ph}, CURRENT_TIMESTAMP)
                """, (migration_name, success, error_msg, exec_time))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to record migration: {e}")
    
    def check_table_exists(self, table_name):
        """Check if a table exists"""
        try:
            conn = _get_conn(self.db_path)
            cursor = conn.cursor()
            ph = _placeholder()
            if _is_mysql():
                cursor.execute(f"""
                    SELECT COUNT(*) FROM information_schema.tables
                    WHERE table_schema = DATABASE() AND table_name = {ph}
                """, (table_name,))
                row = cursor.fetchone()
                result = (row[0] if row else 0) > 0
            else:
                cursor.execute(f"""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name={ph}
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

        mysql = _is_mysql()
        pk = "INTEGER PRIMARY KEY AUTO_INCREMENT" if mysql else "INTEGER PRIMARY KEY AUTOINCREMENT"
        text = "LONGTEXT" if mysql else "TEXT"

        try:
            conn = _get_conn(self.db_path)
            cursor = conn.cursor()

            # Migration: Add Dashboard tables
            migration_name = "add_dashboard_tables.py"
            if not self.is_migration_applied(migration_name):
                if not self.check_table_exists('Dashboard'):
                    logger.info("Creating Dashboard tables...")
                    start_time = datetime.now()

                    cursor.execute(f'''
                        CREATE TABLE IF NOT EXISTS Dashboard (
                            id {pk},
                            name VARCHAR(500) NOT NULL UNIQUE,
                            description {text},
                            is_default INTEGER DEFAULT 0,
                            layout_config {text},
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    ''')

                    cursor.execute(f'''
                        CREATE TABLE IF NOT EXISTS DashboardWidget (
                            id {pk},
                            dashboard_id INTEGER NOT NULL,
                            widget_type {text} NOT NULL,
                            title {text} NOT NULL,
                            position_x INTEGER DEFAULT 0,
                            position_y INTEGER DEFAULT 0,
                            width INTEGER DEFAULT 4,
                            height INTEGER DEFAULT 2,
                            config {text},
                            data_source_type {text},
                            data_source_id INTEGER,
                            refresh_interval INTEGER DEFAULT 300,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    ''')

                    conn.commit()
                    exec_time = int((datetime.now() - start_time).total_seconds() * 1000)
                    self.record_migration(migration_name, success=True, exec_time=exec_time)
                    logger.info(f"✓ Dashboard tables created ({exec_time}ms)")
                else:
                    self.record_migration(migration_name, success=True, exec_time=0)
                    logger.info("✓ Dashboard tables already exist")

            # Migration: Add EntryState table
            migration_name = "add_entry_state_table.py"
            if not self.is_migration_applied(migration_name):
                if not self.check_table_exists('EntryState'):
                    logger.info("Creating EntryState table...")
                    start_time = datetime.now()

                    if mysql:
                        cursor.execute(f'''
                            CREATE TABLE IF NOT EXISTS EntryState (
                                id {pk},
                                entry_type_id INTEGER NOT NULL,
                                name {text} NOT NULL,
                                category {text} NOT NULL,
                                color {text} DEFAULT '#6c757d',
                                display_order INTEGER DEFAULT 0,
                                is_default INTEGER DEFAULT 0,
                                created_at {text} DEFAULT CURRENT_TIMESTAMP,
                                UNIQUE KEY uq_entry_type_name (entry_type_id, name(191))
                            )
                        ''')
                    else:
                        cursor.execute(f'''
                            CREATE TABLE IF NOT EXISTS EntryState (
                                id {pk},
                                entry_type_id INTEGER NOT NULL,
                                name TEXT NOT NULL,
                                category TEXT NOT NULL CHECK(category IN ('active', 'inactive')),
                                color TEXT DEFAULT '#6c757d',
                                display_order INTEGER DEFAULT 0,
                                is_default INTEGER DEFAULT 0,
                                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                                UNIQUE(entry_type_id, name)
                            )
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

                    cursor.execute(f'''
                        CREATE TABLE IF NOT EXISTS SavedSearch (
                            id {pk},
                            name VARCHAR(500) NOT NULL UNIQUE,
                            search_term {text} DEFAULT '',
                            type_filter {text} DEFAULT '',
                            status_filter {text} DEFAULT '',
                            specific_states {text} DEFAULT '',
                            date_range {text} DEFAULT '',
                            sort_by {text} DEFAULT 'created_desc',
                            content_display {text} DEFAULT '',
                            result_limit {text} DEFAULT '50',
                            is_default INTEGER DEFAULT 0,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    ''')

                    conn.commit()
                    exec_time = int((datetime.now() - start_time).total_seconds() * 1000)
                    self.record_migration(migration_name, success=True, exec_time=exec_time)
                    logger.info(f"✓ SavedSearch table created ({exec_time}ms)")
                else:
                    self.record_migration(migration_name, success=True, exec_time=0)

            # Migration: Add CustomColumn tables
            migration_name = "add_custom_columns.py"
            if not self.is_migration_applied(migration_name):
                if not self.check_table_exists('CustomColumn'):
                    logger.info("Creating CustomColumn tables...")
                    start_time = datetime.now()

                    cursor.execute(f'''
                        CREATE TABLE IF NOT EXISTS CustomColumn (
                            id {pk},
                            name VARCHAR(255) NOT NULL UNIQUE,
                            label {text} NOT NULL,
                            description {text},
                            column_type {text} NOT NULL DEFAULT 'text',
                            `options` {text},
                            default_value {text},
                            is_required INTEGER NOT NULL DEFAULT 0,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    ''')

                    cursor.execute(f'''
                        CREATE TABLE IF NOT EXISTS CustomColumnAssignment (
                            id {pk},
                            custom_column_id INTEGER NOT NULL,
                            entry_type_id INTEGER NOT NULL,
                            section_placement {text} NOT NULL DEFAULT 'custom_columns',
                            display_order INTEGER NOT NULL DEFAULT 0,
                            is_visible INTEGER NOT NULL DEFAULT 1,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (custom_column_id) REFERENCES CustomColumn(id) ON DELETE CASCADE,
                            FOREIGN KEY (entry_type_id) REFERENCES EntryType(id) ON DELETE CASCADE
                        )
                    ''')

                    # Unique index on (custom_column_id, entry_type_id) so same column can't be
                    # assigned to the same entry type twice.
                    if mysql:
                        cursor.execute('''
                            ALTER TABLE CustomColumnAssignment
                            ADD UNIQUE KEY uq_col_entry_type (custom_column_id, entry_type_id)
                        ''')
                    else:
                        cursor.execute('''
                            CREATE UNIQUE INDEX IF NOT EXISTS uq_col_entry_type
                            ON CustomColumnAssignment(custom_column_id, entry_type_id)
                        ''')

                    cursor.execute(f'''
                        CREATE TABLE IF NOT EXISTS CustomColumnValue (
                            id {pk},
                            entry_id INTEGER NOT NULL,
                            custom_column_id INTEGER NOT NULL,
                            value {text},
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (entry_id) REFERENCES Entry(id) ON DELETE CASCADE,
                            FOREIGN KEY (custom_column_id) REFERENCES CustomColumn(id) ON DELETE CASCADE
                        )
                    ''')

                    if mysql:
                        cursor.execute('''
                            ALTER TABLE CustomColumnValue
                            ADD UNIQUE KEY uq_entry_col (entry_id, custom_column_id)
                        ''')
                    else:
                        cursor.execute('''
                            CREATE UNIQUE INDEX IF NOT EXISTS uq_entry_col
                            ON CustomColumnValue(entry_id, custom_column_id)
                        ''')

                    conn.commit()
                    exec_time = int((datetime.now() - start_time).total_seconds() * 1000)
                    self.record_migration(migration_name, success=True, exec_time=exec_time)
                    logger.info(f"✓ CustomColumn tables created ({exec_time}ms)")
                else:
                    self.record_migration(migration_name, success=True, exec_time=0)
                    logger.info("✓ CustomColumn tables already exist")

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
        if not _is_mysql() and not self.db_path.exists():
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
