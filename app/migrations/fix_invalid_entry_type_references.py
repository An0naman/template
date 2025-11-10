#!/usr/bin/env python3
"""
Migration: Fix invalid entry_type_id references
Created: 2025-11-10
Description: Identifies and optionally fixes entries with invalid entry_type_id references.
             This can occur when:
             - Entry types are deleted but entries still reference them
             - Entries are created with hardcoded/invalid entry_type_id values
             - Data migration issues from older versions
             
             This migration uses LEFT JOINs in queries going forward to prevent entries
             from being hidden when they have invalid entry_type_id values.
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

MIGRATION_ID = 'fix_invalid_entry_type_references'
MIGRATION_DESCRIPTION = 'Fix entries with invalid entry_type_id references'


def migration_already_applied(cursor) -> bool:
    """Check if this migration has already been applied."""
    try:
        cursor.execute("""
            SELECT COUNT(*) FROM schema_migrations 
            WHERE migration_name = ?
        """, (MIGRATION_ID,))
        result = cursor.fetchone()
        return result and result[0] > 0
    except sqlite3.OperationalError:
        # schema_migrations table doesn't exist
        return False


def find_invalid_entries(cursor):
    """Find entries with invalid entry_type_id references."""
    cursor.execute("""
        SELECT e.id, e.title, e.entry_type_id, e.description, e.created_at
        FROM Entry e
        LEFT JOIN EntryType et ON e.entry_type_id = et.id
        WHERE et.id IS NULL
        ORDER BY e.id
    """)
    return cursor.fetchall()


def get_available_entry_types(cursor):
    """Get all available entry types."""
    cursor.execute("""
        SELECT id, name, singular_label, plural_label, is_primary
        FROM EntryType
        ORDER BY is_primary DESC, singular_label ASC
    """)
    return cursor.fetchall()


def apply_migration(cursor):
    """
    Find entries with invalid entry_type_id and report them.
    
    The actual fix is in the code (LEFT JOINs instead of INNER JOINs),
    but this migration identifies problematic data for manual review.
    """
    logger.info("=" * 70)
    logger.info("Checking for entries with invalid entry_type_id references...")
    logger.info("=" * 70)
    
    # Find invalid entries
    invalid_entries = find_invalid_entries(cursor)
    
    if not invalid_entries:
        logger.info("✅ No entries with invalid entry_type_id found!")
        logger.info("")
        logger.info("Code fixes applied:")
        logger.info("  - Changed INNER JOINs to LEFT JOINs in:")
        logger.info("    • /entries route (main index)")
        logger.info("    • /entry/<id> routes (detail pages)")
        logger.info("    • GET /api/entries endpoints")
        logger.info("    • Search and dashboard services")
        logger.info("")
        return True
    
    # Report invalid entries
    logger.warning(f"⚠️  Found {len(invalid_entries)} entries with invalid entry_type_id:")
    logger.info("")
    
    entry_types = get_available_entry_types(cursor)
    
    for entry in invalid_entries:
        logger.warning(f"Entry ID {entry[0]}: '{entry[1]}'")
        logger.warning(f"  Invalid entry_type_id: {entry[2]}")
        logger.warning(f"  Description: {entry[3] or '(none)'}")
        logger.warning(f"  Created: {entry[4]}")
        logger.warning("")
    
    logger.info("Available Entry Types:")
    for et in entry_types:
        primary_marker = " (PRIMARY)" if et[4] else ""
        logger.info(f"  [{et[0]}] {et[2]} ({et[1]}){primary_marker}")
    
    logger.info("")
    logger.info("=" * 70)
    logger.info("ACTION REQUIRED:")
    logger.info("=" * 70)
    logger.info("")
    logger.info("These entries have invalid entry_type_id values and need attention:")
    logger.info("")
    logger.info("Option 1 - Manual Fix (Recommended):")
    logger.info("  Update each entry through the web UI to assign a valid entry type")
    logger.info("")
    logger.info("Option 2 - Bulk Fix:")
    logger.info("  Run the fix_invalid_entry_types.py script in interactive mode:")
    logger.info("  python3 fix_invalid_entry_types.py --fix")
    logger.info("")
    logger.info("Option 3 - Auto-assign to primary entry type:")
    logger.info("  Set environment variable: AUTO_FIX_ENTRY_TYPES=1")
    logger.info("  This will assign all invalid entries to the first primary entry type")
    logger.info("")
    
    # Check if auto-fix is enabled
    auto_fix = os.environ.get('AUTO_FIX_ENTRY_TYPES', '0') == '1'
    
    if auto_fix:
        primary_type = next((et for et in entry_types if et[4]), None)
        if primary_type:
            logger.info(f"AUTO_FIX_ENTRY_TYPES enabled - assigning to: {primary_type[2]}")
            for entry in invalid_entries:
                cursor.execute("""
                    UPDATE Entry 
                    SET entry_type_id = ? 
                    WHERE id = ?
                """, (primary_type[0], entry[0]))
                logger.info(f"  ✓ Updated entry {entry[0]} to entry_type_id {primary_type[0]}")
            logger.info("")
            logger.info(f"✅ Auto-fixed {len(invalid_entries)} entries")
        else:
            logger.warning("⚠️  No primary entry type found for auto-fix")
            return False
    else:
        logger.info("Code changes ensure these entries will now appear in lists")
        logger.info("(they will show with no entry type label until manually fixed)")
    
    logger.info("")
    logger.info("=" * 70)
    
    return True


def record_migration(cursor):
    """Record this migration in the schema_migrations table."""
    cursor.execute("""
        INSERT INTO schema_migrations (migration_name, applied_at, success)
        VALUES (?, ?, ?)
    """, (MIGRATION_ID, datetime.now().isoformat(), True))


def main():
    """Main migration execution."""
    try:
        # Check database exists
        if not os.path.exists(DATABASE_PATH):
            logger.error(f"❌ Database not found: {DATABASE_PATH}")
            return 1
        
        logger.info(f"📂 Database: {DATABASE_PATH}")
        logger.info("")
        
        # Connect to database
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check if already applied
        if migration_already_applied(cursor):
            logger.info(f"⏭️  Migration '{MIGRATION_ID}' already applied - skipping")
            return 0
        
        # Apply migration
        if apply_migration(cursor):
            record_migration(cursor)
            conn.commit()
            logger.info("✅ Migration completed successfully")
            return 0
        else:
            logger.error("❌ Migration failed")
            conn.rollback()
            return 1
            
    except Exception as e:
        logger.error(f"❌ Migration error: {e}", exc_info=True)
        return 1
    finally:
        if 'conn' in locals():
            conn.close()


if __name__ == '__main__':
    sys.exit(main())
