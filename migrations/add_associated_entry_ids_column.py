#!/usr/bin/env python3
"""
Migration script to add associated_entry_ids column to Note table.
This column will store a JSON array of entry IDs that are associated with a note.
"""

import sqlite3
import json
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def migrate_database(db_path):
    """Add associated_entry_ids column to Note table."""
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check if the column already exists
        cursor.execute("PRAGMA table_info(Note)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'associated_entry_ids' in columns:
            logger.info("Column 'associated_entry_ids' already exists in Note table")
            return True
        
        # Add the new column
        logger.info("Adding 'associated_entry_ids' column to Note table...")
        cursor.execute("""
            ALTER TABLE Note 
            ADD COLUMN associated_entry_ids TEXT DEFAULT '[]'
        """)
        
        # Commit the changes
        conn.commit()
        logger.info("Successfully added 'associated_entry_ids' column to Note table")
        
        # Verify the column was added
        cursor.execute("PRAGMA table_info(Note)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'associated_entry_ids' in columns:
            logger.info("Migration completed successfully!")
            return True
        else:
            logger.error("Migration failed: Column not found after addition")
            return False
            
    except sqlite3.Error as e:
        logger.error(f"Database error during migration: {e}")
        if conn:
            conn.rollback()
        return False
    except Exception as e:
        logger.error(f"Unexpected error during migration: {e}")
        return False
    finally:
        if conn:
            conn.close()

def main():
    """Run the migration on the main database."""
    # Get the database path
    script_dir = Path(__file__).parent.absolute()
    db_path = script_dir.parent / "data" / "template.db"
    
    if not db_path.exists():
        logger.error(f"Database file not found: {db_path}")
        return False
    
    logger.info(f"Running migration on database: {db_path}")
    return migrate_database(str(db_path))

if __name__ == "__main__":
    success = main()
    if success:
        print("Migration completed successfully!")
        exit(0)
    else:
        print("Migration failed!")
        exit(1)
