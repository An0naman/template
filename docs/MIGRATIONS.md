# Database Migrations Guide

## Overview

This template includes an automated database migration system that ensures all schema changes are applied consistently across all app instances. Migrations run automatically on container startup, making deployments seamless with Watchtower.

## Key Features

✅ **Automatic Execution**: Migrations run on container startup via `docker-entrypoint.sh`
✅ **Migration Tracking**: `schema_migrations` table tracks which migrations have been applied
✅ **Idempotent**: Safe to run multiple times - already applied migrations are skipped
✅ **Error Handling**: Failed migrations are logged but don't prevent container startup
✅ **Watchtower Compatible**: New migrations deploy automatically when images update

## Directory Structure

```
template/
├── app/
│   └── migrations/           # App-specific migrations
│       ├── 000_init_migration_tracking.py
│       ├── 001_add_custom_sql_to_saved_search.py
│       └── _migration_template.py
├── migrations/               # Root-level migrations (legacy)
└── docker-entrypoint.sh      # Runs migrations on startup
```

## Migration Naming Convention

Migrations should follow this naming pattern:
```
XXX_descriptive_name.py
```

**Examples:**
- `000_init_migration_tracking.py` - Initial migration tracking setup
- `001_add_custom_sql_column.py` - Add custom SQL support
- `002_create_user_preferences_table.py` - New table for user prefs
- `003_add_index_to_entries.py` - Performance optimization

**Guidelines:**
- Use sequential numbering (000, 001, 002, etc.)
- Use descriptive names with underscores
- Start with verb (add, create, update, remove, etc.)
- Keep names concise but clear

## Creating a New Migration

### Method 1: Copy the Template

```bash
# Copy the migration template
cp app/migrations/_migration_template.py app/migrations/002_your_migration_name.py

# Edit the new migration
nano app/migrations/002_your_migration_name.py
```

### Method 2: Use the Helper Script (Coming Soon)

```bash
# Generate a migration with proper naming
./scripts/create_migration.sh "add user avatar column"
# Creates: app/migrations/XXX_add_user_avatar_column.py
```

## Migration Template Structure

```python
#!/usr/bin/env python3
"""
Migration: [Description]
Created: YYYY-MM-DD
Description: [Detailed description of changes]
"""

import sqlite3
import os
import sys
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_PATH = os.environ.get('DATABASE_PATH', '/app/data/template.db')


def migration_already_applied(cursor) -> bool:
    """
    Check if this migration has already been applied.
    Use schema_migrations table for tracking.
    """
    cursor.execute("""
        SELECT COUNT(*) FROM schema_migrations 
        WHERE migration_name = ?
    """, (Path(__file__).name,))
    return cursor.fetchone()[0] > 0


def apply_migration(cursor):
    """
    Apply the actual migration changes here.
    """
    # Example: Add a column
    cursor.execute("""
        ALTER TABLE YourTable 
        ADD COLUMN new_column TEXT
    """)
    logger.info("✓ Migration changes applied")


def record_migration(cursor, migration_name, success=True, error_msg=None, execution_time_ms=0):
    """Record this migration in tracking table"""
    cursor.execute("""
        INSERT INTO schema_migrations 
        (migration_name, success, error_message, execution_time_ms) 
        VALUES (?, ?, ?, ?)
    """, (migration_name, success, error_msg, execution_time_ms))


def main():
    """Main execution function"""
    migration_name = Path(__file__).name
    start_time = datetime.now()
    
    logger.info(f"Running migration: {migration_name}")
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        if migration_already_applied(cursor):
            logger.info("✓ Already applied, skipping...")
            return 0
        
        apply_migration(cursor)
        
        execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
        record_migration(cursor, migration_name, success=True, execution_time_ms=execution_time)
        
        conn.commit()
        logger.info(f"✓ Completed in {execution_time}ms")
        return 0
        
    except Exception as e:
        logger.error(f"✗ Failed: {e}")
        if 'conn' in locals():
            conn.rollback()
        return 1
    finally:
        if 'conn' in locals():
            conn.close()


if __name__ == "__main__":
    sys.exit(main())
```

## Common Migration Patterns

### Adding a Column

```python
def apply_migration(cursor):
    cursor.execute("""
        ALTER TABLE TableName 
        ADD COLUMN new_column TEXT DEFAULT NULL
    """)
```

### Creating a Table

```python
def apply_migration(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS NewTable (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
```

### Creating an Index

```python
def apply_migration(cursor):
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_table_column 
        ON TableName(column_name)
    """)
```

### Updating Existing Data

```python
def apply_migration(cursor):
    # Update all rows
    cursor.execute("""
        UPDATE TableName 
        SET status = 'active' 
        WHERE status IS NULL
    """)
    
    # Or with more complex logic
    cursor.execute("SELECT id, old_field FROM TableName")
    rows = cursor.fetchall()
    
    for row_id, old_value in rows:
        new_value = transform_value(old_value)
        cursor.execute("""
            UPDATE TableName 
            SET new_field = ? 
            WHERE id = ?
        """, (new_value, row_id))
```

### Checking Before Modifying

```python
def migration_already_applied(cursor) -> bool:
    # Check if column exists
    cursor.execute("PRAGMA table_info(TableName)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'new_column' in columns:
        return True
    
    # Check if table exists
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='TableName'
    """)
    if cursor.fetchone():
        return True
    
    # Check schema_migrations (preferred)
    cursor.execute("""
        SELECT COUNT(*) FROM schema_migrations 
        WHERE migration_name = ?
    """, (Path(__file__).name,))
    return cursor.fetchone()[0] > 0
```

## Testing Migrations

### Test Locally Before Deploying

```bash
# Test in local environment
python app/migrations/002_your_migration.py

# Or test with Docker
docker build -t test-migration .
docker run --rm -v $(pwd)/test_data:/app/data test-migration

# Check logs
docker logs <container_name> | grep -i migration
```

### Verify Migration Applied

```bash
# Connect to database and check schema_migrations table
docker exec <container_name> python -c "
import sqlite3
conn = sqlite3.connect('/app/data/template.db')
cursor = conn.cursor()
cursor.execute('SELECT * FROM schema_migrations ORDER BY applied_at DESC LIMIT 5')
for row in cursor.fetchall():
    print(row)
conn.close()
"
```

### Check Column Was Added

```bash
docker exec <container_name> python -c "
import sqlite3
conn = sqlite3.connect('/app/data/template.db')
cursor = conn.cursor()
cursor.execute('PRAGMA table_info(YourTable)')
for col in cursor.fetchall():
    print(f'{col[0]}: {col[1]} ({col[2]})')
conn.close()
"
```

## Deployment Workflow

### With Watchtower (Automatic)

1. **Push Changes**: Commit migration files to repository
2. **Build Image**: GitHub Actions builds and pushes new image
3. **Watchtower Updates**: Automatically pulls new image
4. **Auto-Migration**: `docker-entrypoint.sh` runs pending migrations
5. **App Starts**: Application launches with updated schema

### Manual Deployment

```bash
# Build new image
docker build -t your-registry/app:latest .

# Push to registry
docker push your-registry/app:latest

# Pull and restart (Watchtower does this automatically)
docker pull your-registry/app:latest
docker-compose up -d --force-recreate
```

## Monitoring Migrations

### View Migration Logs

```bash
# Watch migrations in real-time during startup
docker logs -f <container_name> | grep -A 5 "=== Running Database Migrations ==="

# Check recent migration activity
docker logs <container_name> --tail 100 | grep migration
```

### Check Applied Migrations

```bash
# List all applied migrations
docker exec <container_name> sqlite3 /app/data/template.db \
  "SELECT migration_name, applied_at, success FROM schema_migrations ORDER BY applied_at DESC;"
```

### Verify Migration Status

```bash
# Check if specific migration applied
docker exec <container_name> python -c "
import sqlite3
conn = sqlite3.connect('/app/data/template.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM schema_migrations WHERE migration_name = ?', 
               ('002_your_migration.py',))
print('Applied' if cursor.fetchone()[0] > 0 else 'Not Applied')
conn.close()
"
```

## Troubleshooting

### Migration Failed During Startup

```bash
# Check error logs
docker logs <container_name> | grep -i "migration failed"

# Try running migration manually
docker exec <container_name> python /app/app/migrations/XXX_migration.py

# If migration is corrupted, fix and manually record it
docker exec -it <container_name> python -c "
import sqlite3
conn = sqlite3.connect('/app/data/template.db')
cursor = conn.cursor()
cursor.execute('DELETE FROM schema_migrations WHERE migration_name = ?', 
               ('XXX_migration.py',))
conn.commit()
conn.close()
print('Migration record removed. Restart container to retry.')
"
```

### Schema_migrations Table Missing

```bash
# Run the initialization migration
docker exec <container_name> python /app/app/migrations/000_init_migration_tracking.py
```

### Migration Stuck/Hanging

```bash
# Check for database locks
docker exec <container_name> fuser /app/data/template.db

# Restart container
docker restart <container_name>
```

### Need to Rollback

```bash
# Manually reverse the migration changes
docker exec -it <container_name> python -c "
import sqlite3
conn = sqlite3.connect('/app/data/template.db')
cursor = conn.cursor()

# Example: Remove a column (SQLite doesn't support DROP COLUMN directly)
# You'll need to recreate the table without the column

# Remove migration record
cursor.execute('DELETE FROM schema_migrations WHERE migration_name = ?', 
               ('XXX_migration.py',))
conn.commit()
conn.close()
"
```

## Best Practices

### ✅ DO

- Always use the migration template as a starting point
- Check if migration is already applied before running
- Record migrations in `schema_migrations` table
- Include descriptive migration names and comments
- Test migrations locally before deploying
- Make migrations idempotent (safe to run multiple times)
- Log all actions for debugging
- Handle errors gracefully

### ❌ DON'T

- Don't modify deployed migrations - create new ones instead
- Don't skip migration tracking
- Don't assume database state - always check first
- Don't use `DROP COLUMN` (SQLite doesn't support it cleanly)
- Don't deploy untested migrations to production
- Don't forget to commit migration files
- Don't hardcode database paths

## Migration Checklist

Before deploying a new migration:

- [ ] Migration follows naming convention (XXX_description.py)
- [ ] Uses migration template structure
- [ ] Checks if already applied (idempotent)
- [ ] Records in schema_migrations table
- [ ] Includes proper logging
- [ ] Handles errors gracefully
- [ ] Tested locally
- [ ] Verified in test container
- [ ] Committed to repository
- [ ] Documented any special requirements

## Advanced Topics

### Multiple Database Support

If your app uses multiple databases:

```python
def main():
    databases = [
        '/app/data/app1.db',
        '/app/data/app2.db',
    ]
    
    for db_path in databases:
        logger.info(f"Running migration on {db_path}")
        run_migration_on_db(db_path)
```

### Conditional Migrations

```python
def apply_migration(cursor):
    # Check app version or feature flag
    cursor.execute("SELECT value FROM settings WHERE key='feature_enabled'")
    row = cursor.fetchone()
    
    if row and row[0] == 'true':
        logger.info("Feature enabled, applying migration...")
        cursor.execute("ALTER TABLE...")
    else:
        logger.info("Feature disabled, skipping...")
```

### Data Migrations

For migrations that transform large amounts of data:

```python
def apply_migration(cursor):
    # Process in batches
    batch_size = 1000
    offset = 0
    
    while True:
        cursor.execute(f"""
            SELECT id, old_field FROM TableName 
            LIMIT {batch_size} OFFSET {offset}
        """)
        rows = cursor.fetchall()
        
        if not rows:
            break
        
        for row_id, old_value in rows:
            new_value = transform(old_value)
            cursor.execute("""
                UPDATE TableName SET new_field = ? WHERE id = ?
            """, (new_value, row_id))
        
        offset += batch_size
        logger.info(f"Processed {offset} rows...")
```

## Support

For questions or issues with migrations:

1. Check the logs: `docker logs <container_name> | grep migration`
2. Review this guide for common patterns
3. Test migrations locally before deploying
4. Check `schema_migrations` table for migration status

---

**Last Updated**: 2025-10-30
**Template Version**: 2.0
