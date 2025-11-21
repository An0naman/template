#!/usr/bin/env python3
"""
Unified Database Migration Script
==================================
Applies all necessary migrations to all databases in the data directory.
This ensures schema consistency across all downstream app instances.

Usage:
    python scripts/migrate_all_databases.py [--dry-run] [--database <specific_db>]
"""

import sqlite3
import os
import sys
import logging
import argparse
from pathlib import Path
from datetime import datetime
import hashlib
import importlib.util

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get project root
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / 'data'
MIGRATIONS_DIR = PROJECT_ROOT / 'app' / 'migrations'
OLD_MIGRATIONS_DIR = PROJECT_ROOT / 'migrations'


class MigrationManager:
    """Manages database migrations across multiple database files"""
    
    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self.migration_tracker = {}
        
    def get_all_databases(self):
        """Find all SQLite database files in the data directory"""
        if not DATA_DIR.exists():
            logger.warning(f"Data directory not found: {DATA_DIR}")
            return []
        
        db_files = list(DATA_DIR.glob('*.db'))
        logger.info(f"Found {len(db_files)} database files")
        return db_files
    
    def get_migration_files(self):
        """Get all migration files from both old and new migration directories"""
        migration_files = []
        
        # Check new migrations directory (app/migrations)
        if MIGRATIONS_DIR.exists():
            new_migrations = sorted([
                f for f in MIGRATIONS_DIR.glob('*.py')
                if not f.name.startswith('_') and not f.name.startswith('.')
            ])
            migration_files.extend(new_migrations)
            logger.info(f"Found {len(new_migrations)} migrations in {MIGRATIONS_DIR}")
        
        # Check old migrations directory (migrations/)
        if OLD_MIGRATIONS_DIR.exists():
            old_migrations = sorted([
                f for f in OLD_MIGRATIONS_DIR.glob('*.py')
                if not f.name.startswith('_') and not f.name.startswith('.')
            ])
            # Filter out duplicates already in new migrations
            new_names = {f.name for f in migration_files}
            old_migrations = [f for f in old_migrations if f.name not in new_names]
            migration_files.extend(old_migrations)
            logger.info(f"Found {len(old_migrations)} additional migrations in {OLD_MIGRATIONS_DIR}")
        
        return sorted(migration_files, key=lambda x: x.name)
    
    def ensure_migration_tracking(self, conn):
        """Ensure schema_migrations table exists"""
        try:
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
            return True
        except sqlite3.OperationalError as e:
            if 'readonly' in str(e).lower():
                logger.warning("Database is readonly, skipping migration tracking setup")
                return False
            raise
    
    def is_migration_applied(self, conn, migration_name):
        """Check if a migration has already been applied"""
        try:
            cursor = conn.cursor()
            # Check if table exists first
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='schema_migrations'
            """)
            if not cursor.fetchone():
                return False  # Table doesn't exist, migration not applied
            
            cursor.execute("""
                SELECT COUNT(*) FROM schema_migrations 
                WHERE migration_name = ? AND success = TRUE
            """, (migration_name,))
            count = cursor.fetchone()[0]
            return count > 0
        except sqlite3.OperationalError:
            return False  # If any error, assume not applied
    
    def record_migration(self, conn, migration_name, success=True, error_msg=None, exec_time=0):
        """Record migration execution in the tracking table"""
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO schema_migrations 
                (migration_name, success, error_message, execution_time_ms, applied_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (migration_name, success, error_msg, exec_time))
            conn.commit()
        except sqlite3.OperationalError as e:
            if 'readonly' not in str(e).lower():
                logger.warning(f"Could not record migration: {e}")
    
    def check_table_exists(self, conn, table_name):
        """Check if a table exists in the database"""
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name=?
        """, (table_name,))
        return cursor.fetchone() is not None
    
    def apply_init_db_schema(self, db_path):
        """Apply the base schema from db.py init_db() to ensure core tables exist"""
        logger.info(f"Applying base schema to {db_path.name}")
        
        try:
            # Set up minimal Flask app context to run init_db
            sys.path.insert(0, str(PROJECT_ROOT))
            
            # Temporarily override DATABASE_PATH
            os.environ['DATABASE_PATH'] = str(db_path)
            
            from flask import Flask
            app = Flask(__name__)
            app.config['DATABASE_PATH'] = str(db_path)
            
            with app.app_context():
                from app.db import init_db
                init_db()
                logger.info(f"✓ Base schema applied to {db_path.name}")
                return True
        except Exception as e:
            logger.error(f"✗ Failed to apply base schema to {db_path.name}: {e}")
            return False
    
    def apply_migration(self, db_path, migration_file):
        """Apply a single migration to a database"""
        migration_name = migration_file.name
        
        conn = sqlite3.connect(db_path)
        start_time = datetime.now()
        
        try:
            # Ensure migration tracking table exists
            self.ensure_migration_tracking(conn)
            
            # Check if migration already applied
            if self.is_migration_applied(conn, migration_name):
                logger.info(f"  ↳ Already applied: {migration_name}")
                return True
            
            # Check if migration is needed (for smart migrations)
            # For Dashboard tables, check if they already exist
            if 'dashboard' in migration_name.lower():
                if self.check_table_exists(conn, 'Dashboard') and \
                   self.check_table_exists(conn, 'DashboardWidget'):
                    logger.info(f"  ↳ Tables exist, recording: {migration_name}")
                    exec_time = int((datetime.now() - start_time).total_seconds() * 1000)
                    self.record_migration(conn, migration_name, success=True, exec_time=exec_time)
                    conn.close()
                    return True
            
            if self.dry_run:
                logger.info(f"  ↳ [DRY RUN] Would apply: {migration_name}")
                conn.close()
                return True
            
            # Load and execute the migration
            logger.info(f"  → Applying: {migration_name}")
            
            # Import the migration module
            spec = importlib.util.spec_from_file_location(
                migration_name.replace('.py', ''), 
                migration_file
            )
            migration_module = importlib.util.module_from_spec(spec)
            
            # Temporarily override DATABASE_PATH for the migration
            old_db_path = os.environ.get('DATABASE_PATH')
            os.environ['DATABASE_PATH'] = str(db_path)
            
            try:
                spec.loader.exec_module(migration_module)
                
                # Try different migration entry points
                if hasattr(migration_module, 'apply_migration'):
                    cursor = conn.cursor()
                    migration_module.apply_migration(cursor)
                    conn.commit()
                elif hasattr(migration_module, 'migrate'):
                    result = migration_module.migrate()
                    if result is False:
                        raise Exception("Migration returned False")
                elif hasattr(migration_module, 'main'):
                    result = migration_module.main()
                    if result != 0:
                        raise Exception(f"Migration exited with code {result}")
                else:
                    logger.warning(f"  ⚠ No recognized entry point for {migration_name}")
                
                # Record successful migration
                exec_time = int((datetime.now() - start_time).total_seconds() * 1000)
                self.record_migration(conn, migration_name, success=True, exec_time=exec_time)
                logger.info(f"  ✓ Applied: {migration_name} ({exec_time}ms)")
                return True
                
            finally:
                # Restore DATABASE_PATH
                if old_db_path:
                    os.environ['DATABASE_PATH'] = old_db_path
                elif 'DATABASE_PATH' in os.environ:
                    del os.environ['DATABASE_PATH']
                    
        except Exception as e:
            conn.rollback()
            exec_time = int((datetime.now() - start_time).total_seconds() * 1000)
            self.record_migration(conn, migration_name, success=False, 
                                error_msg=str(e), exec_time=exec_time)
            logger.error(f"  ✗ Failed: {migration_name} - {e}")
            return False
        finally:
            conn.close()
    
    def migrate_database(self, db_path, migrations):
        """Apply all migrations to a single database"""
        logger.info(f"\n{'='*60}")
        logger.info(f"Database: {db_path.name}")
        logger.info(f"{'='*60}")
        
        # First ensure base schema exists
        if not self.dry_run:
            self.apply_init_db_schema(db_path)
        
        applied = 0
        failed = 0
        skipped = 0
        
        for migration_file in migrations:
            result = self.apply_migration(db_path, migration_file)
            if result is True:
                applied += 1
            elif result is False:
                failed += 1
            else:
                skipped += 1
        
        logger.info(f"\nResults for {db_path.name}:")
        logger.info(f"  Applied: {applied}")
        logger.info(f"  Failed: {failed}")
        logger.info(f"  Skipped: {skipped}")
        
        return failed == 0
    
    def migrate_all(self, specific_db=None):
        """Migrate all databases or a specific one"""
        databases = self.get_all_databases()
        
        if specific_db:
            databases = [db for db in databases if db.name == specific_db]
            if not databases:
                logger.error(f"Database not found: {specific_db}")
                return False
        
        if not databases:
            logger.error("No databases found!")
            return False
        
        migrations = self.get_migration_files()
        logger.info(f"\nFound {len(migrations)} migration files")
        
        if self.dry_run:
            logger.info("\n*** DRY RUN MODE - No changes will be made ***\n")
        
        all_success = True
        for db_path in databases:
            success = self.migrate_database(db_path, migrations)
            all_success = all_success and success
        
        return all_success


def main():
    parser = argparse.ArgumentParser(
        description='Migrate all databases in the data directory'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )
    parser.add_argument(
        '--database', '-d',
        help='Migrate only a specific database file (e.g., homebrew.db)'
    )
    
    args = parser.parse_args()
    
    logger.info("="*60)
    logger.info("Unified Database Migration Tool")
    logger.info("="*60)
    
    manager = MigrationManager(dry_run=args.dry_run)
    success = manager.migrate_all(specific_db=args.database)
    
    logger.info("\n" + "="*60)
    if success:
        logger.info("✓ All migrations completed successfully!")
        return 0
    else:
        logger.error("✗ Some migrations failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
