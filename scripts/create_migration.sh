#!/bin/bash
# Migration Helper Script
# Usage: ./scripts/create_migration.sh "description of migration"

set -e

# Check if description is provided
if [ -z "$1" ]; then
    echo "❌ Error: Migration description is required"
    echo ""
    echo "Usage: $0 \"description of migration\""
    echo "Example: $0 \"add user avatar column\""
    exit 1
fi

# Get the description and sanitize it
DESCRIPTION="$1"
SANITIZED_DESC=$(echo "$DESCRIPTION" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/_/g' | sed 's/__*/_/g' | sed 's/^_//;s/_$//')

# Find the next migration number
MIGRATIONS_DIR="app/migrations"
LAST_MIGRATION=$(ls -1 "$MIGRATIONS_DIR" | grep -E '^[0-9]{3}_' | tail -n 1 | cut -d'_' -f1 || echo "000")
NEXT_NUM=$(printf "%03d" $((10#$LAST_MIGRATION + 1)))

# Create filename
FILENAME="${NEXT_NUM}_${SANITIZED_DESC}.py"
FILEPATH="${MIGRATIONS_DIR}/${FILENAME}"

# Check if file already exists
if [ -f "$FILEPATH" ]; then
    echo "❌ Error: Migration file already exists: $FILEPATH"
    exit 1
fi

# Get current date
CURRENT_DATE=$(date +%Y-%m-%d)

# Create migration from template
cat > "$FILEPATH" << 'EOF'
#!/usr/bin/env python3
"""
Migration: MIGRATION_DESCRIPTION
Created: MIGRATION_DATE
Description: TODO: Add detailed description of what this migration does
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

DATABASE_PATH = os.environ.get('DATABASE_PATH', '/app/data/template.db')


def migration_already_applied(cursor) -> bool:
    """
    Check if this migration has already been applied.
    """
    try:
        cursor.execute("""
            SELECT COUNT(*) FROM schema_migrations 
            WHERE migration_name = ?
        """, (Path(__file__).name,))
        return cursor.fetchone()[0] > 0
    except sqlite3.OperationalError as e:
        if "no such table: schema_migrations" in str(e):
            logger.warning("schema_migrations table not found - run 000_init_migration_tracking.py first")
            return False
        raise


def apply_migration(cursor):
    """
    Apply the actual migration changes.
    
    TODO: Implement your migration logic here
    
    Examples:
    ---------
    # Add a column
    cursor.execute('''
        ALTER TABLE YourTable 
        ADD COLUMN new_column TEXT DEFAULT NULL
    ''')
    
    # Create a table
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
    """
    
    logger.info("Applying migration changes...")
    
    # TODO: Add your migration code here
    # Example:
    # cursor.execute("""
    #     ALTER TABLE YourTable 
    #     ADD COLUMN new_column TEXT
    # """)
    
    logger.info("✓ Migration changes applied successfully")


def record_migration(cursor, migration_name: str, success: bool = True, error_msg: str = None, execution_time_ms: int = 0):
    """Record this migration in the schema_migrations table."""
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
    """Main migration execution function."""
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
EOF

# Replace placeholders
sed -i "s/MIGRATION_DESCRIPTION/$DESCRIPTION/g" "$FILEPATH"
sed -i "s/MIGRATION_DATE/$CURRENT_DATE/g" "$FILEPATH"

# Make executable
chmod +x "$FILEPATH"

echo "✅ Migration created successfully!"
echo ""
echo "📄 File: $FILEPATH"
echo "📝 Description: $DESCRIPTION"
echo ""
echo "Next steps:"
echo "1. Edit the migration file and implement apply_migration()"
echo "2. Test locally: python $FILEPATH"
echo "3. Commit and push to deploy"
echo ""
echo "Opening in editor..."
echo "${EDITOR:-nano} $FILEPATH"
