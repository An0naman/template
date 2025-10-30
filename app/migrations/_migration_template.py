#!/usr/bin/env python3
"""
Migration Template
==================

Copy this file and rename with sequential numbering and descriptive name:
Format: XXX_descriptive_name.py
Example: 001_add_custom_sql_column.py, 002_add_user_preferences_table.py

Created: YYYY-MM-DD
Description: [Describe what this migration does]

Usage:
------
This migration will be automatically run by docker-entrypoint.sh on container startup.
You can also run it manually:
    python app/migrations/XXX_descriptive_name.py

Guidelines:
-----------
1. Always check if migration already applied before running
2. Record migration in schema_migrations table
3. Include proper error handling and rollback logic
4. Log all actions for debugging
5. Make migrations idempotent (safe to run multiple times)
"""

import sqlite3
import os
import sys
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get database path from environment or use default
DATABASE_PATH = os.environ.get('DATABASE_PATH', '/app/data/template.db')


def migration_already_applied(cursor) -> bool:
    """
    Check if this migration has already been applied.
    
    Returns:
        bool: True if migration was already applied, False otherwise
    
    Implementation Options:
    -----------------------
    Option 1: Check schema_migrations table (recommended)
        cursor.execute(
            "SELECT COUNT(*) FROM schema_migrations WHERE migration_name = ?",
            (Path(__file__).name,)
        )
        return cursor.fetchone()[0] > 0
    
    Option 2: Check for specific column existence
        cursor.execute("PRAGMA table_info(YourTable)")
        columns = [col[1] for col in cursor.fetchall()]
        return 'your_column_name' in columns
    
    Option 3: Check for table existence
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            ('your_table_name',)
        )
        return cursor.fetchone() is not None
    """
    try:
        # Check if this migration is already recorded
        cursor.execute("""
            SELECT COUNT(*) FROM schema_migrations 
            WHERE migration_name = ?
        """, (Path(__file__).name,))
        
        count = cursor.fetchone()[0]
        return count > 0
        
    except sqlite3.OperationalError as e:
        # If schema_migrations table doesn't exist, migration hasn't been applied
        if "no such table: schema_migrations" in str(e):
            logger.warning("schema_migrations table not found - run 000_init_migration_tracking.py first")
            return False
        raise


def apply_migration(cursor):
    """
    Apply the actual migration changes.
    
    Examples:
    ---------
    
    # Add a new column
    cursor.execute('''
        ALTER TABLE YourTable 
        ADD COLUMN new_column TEXT DEFAULT NULL
    ''')
    
    # Create a new table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS NewTable (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create an index
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_table_column 
        ON YourTable(column_name)
    ''')
    
    # Insert default data
    cursor.execute('''
        INSERT INTO Settings (key, value) 
        VALUES (?, ?)
    ''', ('setting_name', 'default_value'))
    
    # Update existing data
    cursor.execute('''
        UPDATE YourTable 
        SET column_name = ? 
        WHERE condition = ?
    ''', ('new_value', 'some_condition'))
    """
    
    logger.info("Applying migration changes...")
    
    # TODO: Implement your migration logic here
    # Example:
    # cursor.execute("""
    #     ALTER TABLE SavedSearch 
    #     ADD COLUMN custom_sql_query TEXT
    # """)
    
    logger.info("✓ Migration changes applied successfully")


def record_migration(cursor, migration_name: str, success: bool = True, error_msg: str = None, execution_time_ms: int = 0):
    """
    Record this migration in the schema_migrations table.
    """
    try:
        cursor.execute("""
            INSERT INTO schema_migrations 
            (migration_name, success, error_message, execution_time_ms) 
            VALUES (?, ?, ?, ?)
        """, (migration_name, success, error_msg, execution_time_ms))
        logger.info(f"✓ Recorded migration: {migration_name}")
    except Exception as e:
        logger.error(f"Failed to record migration: {e}")


def main():
    """
    Main migration execution function.
    """
    migration_name = Path(__file__).name
    start_time = datetime.now()
    
    logger.info("=" * 60)
    logger.info(f"Migration: {migration_name}")
    logger.info(f"Database: {DATABASE_PATH}")
    logger.info("=" * 60)
    
    # Ensure database directory exists
    db_dir = Path(DATABASE_PATH).parent
    db_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Connect to database
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Check if migration already applied
        if migration_already_applied(cursor):
            logger.info("✓ Migration already applied, skipping...")
            return 0
        
        # Apply migration
        logger.info("Applying migration...")
        apply_migration(cursor)
        
        # Calculate execution time
        execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        # Record this migration
        record_migration(cursor, migration_name, success=True, execution_time_ms=execution_time)
        
        # Commit changes
        conn.commit()
        
        logger.info("=" * 60)
        logger.info(f"✓ Migration completed successfully in {execution_time}ms")
        logger.info("=" * 60)
        return 0
        
    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"✗ Migration failed: {str(e)}")
        logger.error("=" * 60)
        logger.exception("Full traceback:")
        
        if 'conn' in locals():
            try:
                # Try to record the failed migration
                record_migration(cursor, migration_name, success=False, error_msg=str(e))
                conn.commit()
            except:
                pass
            
            conn.rollback()
        
        return 1
        
    finally:
        if 'conn' in locals():
            conn.close()


if __name__ == "__main__":
    sys.exit(main())
