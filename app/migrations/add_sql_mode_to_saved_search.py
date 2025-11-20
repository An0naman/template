"""
Migration: Add use_sql_mode column to SavedSearch table

This migration adds a boolean column to track whether a saved search
should use SQL mode (custom SQL query) instead of standard filters.
"""

import sqlite3
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Migration metadata
MIGRATION_ID = "add_sql_mode_to_saved_search"
MIGRATION_NAME = "Add use_sql_mode to SavedSearch"
MIGRATION_VERSION = "1.0.0"
DEPENDENCIES = ["add_custom_sql_to_saved_search"]  # Depends on the custom_sql_query column


def check_if_applied(db_path: str) -> bool:
    """Check if this migration has already been applied"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
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
            """, ('add_sql_mode_to_saved_search.py',))
            if cursor.fetchone()[0] > 0:
                logger.info(f"Migration {MIGRATION_ID} already applied (found in schema_migrations)")
                return True
        
        # Fallback: Check if column exists
        cursor.execute("PRAGMA table_info(SavedSearch)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'use_sql_mode' in columns:
            logger.info(f"Migration {MIGRATION_ID} already applied (column exists)")
            return True
            
        return False
        
    except Exception as e:
        logger.warning(f"Error checking if migration applied: {e}")
        # If there's an error, check column existence as fallback
        try:
            cursor.execute("PRAGMA table_info(SavedSearch)")
            columns = [row[1] for row in cursor.fetchall()]
            return 'use_sql_mode' in columns
        except:
            return False
        
    finally:
        conn.close()


def apply_migration(db_path: str) -> bool:
    """Add use_sql_mode column to SavedSearch table"""
    logger.info("Adding use_sql_mode column to SavedSearch table...")
    
    sql = """
        ALTER TABLE SavedSearch 
        ADD COLUMN use_sql_mode INTEGER DEFAULT 0
    """
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute(sql)
        conn.commit()
        
        # Record migration in schema_migrations table if it exists
        try:
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='schema_migrations'
            """)
            if cursor.fetchone():
                cursor.execute("""
                    INSERT OR IGNORE INTO schema_migrations (migration_name) 
                    VALUES (?)
                """, ('add_sql_mode_to_saved_search.py',))
                conn.commit()
                logger.info("✓ Migration recorded in schema_migrations")
        except Exception as e:
            logger.warning(f"Could not record migration in schema_migrations: {e}")
        
        logger.info(f"✓ Successfully added use_sql_mode column to SavedSearch table")
        return True
        
    except Exception as e:
        conn.rollback()
        logger.error(f"✗ Error adding use_sql_mode column: {e}")
        return False
        
    finally:
        conn.close()


def rollback_migration(db_path: str) -> bool:
    """
    Rollback this migration
    Note: SQLite doesn't support DROP COLUMN directly in older versions,
    so this would require recreating the table
    """
    logger.warning("Rollback not implemented for this migration (SQLite limitation)")
    logger.warning("To rollback, you would need to recreate the SavedSearch table without the column")
    return False


if __name__ == "__main__":
    # For testing - use the default database path
    import sys
    from pathlib import Path
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Get database path
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    else:
        db_path = Path(__file__).parent.parent.parent / 'data' / 'app.db'
        db_path = str(db_path.absolute())
    
    logger.info(f"Using database: {db_path}")
    
    # Check if already applied
    if check_if_applied(db_path):
        logger.info("Migration already applied")
        sys.exit(0)
    
    # Apply migration
    success = apply_migration(db_path)
    sys.exit(0 if success else 1)
