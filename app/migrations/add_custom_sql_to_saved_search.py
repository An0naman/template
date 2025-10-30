#!/usr/bin/env python3
"""
Migration: Add custom_sql_query column to SavedSearch table
Created: 2025-10-30
Description: Adds support for custom SQL queries in saved searches
"""

import sqlite3
import sys
import os
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DATABASE_PATH = os.environ.get('DATABASE_PATH', '/app/data/template.db')


def migration_already_applied(cursor) -> bool:
    """Check if custom_sql_query column already exists"""
    try:
        # First check schema_migrations table if it exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='schema_migrations'
        """)
        if cursor.fetchone():
            cursor.execute("""
                SELECT COUNT(*) FROM schema_migrations 
                WHERE migration_name = ?
            """, (Path(__file__).name,))
            if cursor.fetchone()[0] > 0:
                return True
        
        # Fallback: Check if column exists
        cursor.execute("PRAGMA table_info(SavedSearch)")
        columns = [column[1] for column in cursor.fetchall()]
        return 'custom_sql_query' in columns
        
    except Exception:
        return False


def apply_migration(cursor):
    """Add custom_sql_query column to SavedSearch table"""
    logger.info("Adding custom_sql_query column to SavedSearch table...")
    cursor.execute("""
        ALTER TABLE SavedSearch 
        ADD COLUMN custom_sql_query TEXT
    """)
    logger.info("✓ Successfully added custom_sql_query column")


def record_migration(cursor, migration_name: str, success: bool = True, error_msg: str = None, execution_time_ms: int = 0):
    """Record this migration in the schema_migrations table if it exists"""
    try:
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='schema_migrations'
        """)
        if cursor.fetchone():
            cursor.execute("""
                INSERT OR IGNORE INTO schema_migrations 
                (migration_name, success, error_message, execution_time_ms) 
                VALUES (?, ?, ?, ?)
            """, (migration_name, success, error_msg, execution_time_ms))
    except Exception as e:
        logger.warning(f"Could not record migration: {e}")


def main():
    migration_name = Path(__file__).name
    start_time = datetime.now()
    
    logger.info(f"Running migration: {migration_name}")
    logger.info(f"Database path: {DATABASE_PATH}")
    
    # Allow override via command line
    db_path = DATABASE_PATH
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
        logger.info(f"Using command line database path: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        if migration_already_applied(cursor):
            logger.info("✓ Migration already applied, skipping...")
            return 0
        
        apply_migration(cursor)
        
        execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
        record_migration(cursor, migration_name, success=True, execution_time_ms=execution_time)
        
        conn.commit()
        logger.info(f"✓ Migration completed successfully in {execution_time}ms")
        return 0
        
    except Exception as e:
        logger.error(f"✗ Migration failed: {e}")
        if 'conn' in locals():
            conn.rollback()
        return 1
        
    finally:
        if 'conn' in locals():
            conn.close()


if __name__ == "__main__":
    sys.exit(main())
