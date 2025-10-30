# Migration Quick Reference

## Creating a New Migration

```bash
# 1. Copy the template
cp app/migrations/_migration_template.py app/migrations/XXX_your_description.py

# 2. Edit the migration
nano app/migrations/XXX_your_description.py

# 3. Test locally
python app/migrations/XXX_your_description.py

# 4. Commit and push
git add app/migrations/XXX_your_description.py
git commit -m "Add migration: your description"
git push
```

## Common Commands

```bash
# View migration logs
docker logs <container> | grep -i migration

# Check applied migrations
docker exec <container> python -c "
import sqlite3
conn = sqlite3.connect('/app/data/template.db')
cursor = conn.cursor()
cursor.execute('SELECT migration_name, applied_at FROM schema_migrations')
for row in cursor.fetchall():
    print(row)
"

# Run migration manually
docker exec <container> python /app/app/migrations/XXX_migration.py

# Check table structure
docker exec <container> python -c "
import sqlite3
conn = sqlite3.connect('/app/data/template.db')
cursor = conn.cursor()
cursor.execute('PRAGMA table_info(TableName)')
for col in cursor.fetchall():
    print(f'{col[0]}: {col[1]} ({col[2]})')
"
```

## Migration Template (Minimal)

```python
#!/usr/bin/env python3
import sqlite3, sys, logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
DATABASE_PATH = '/app/data/template.db'

def migration_already_applied(cursor):
    cursor.execute("SELECT COUNT(*) FROM schema_migrations WHERE migration_name = ?", 
                   (Path(__file__).name,))
    return cursor.fetchone()[0] > 0

def apply_migration(cursor):
    # Your migration code here
    cursor.execute("ALTER TABLE YourTable ADD COLUMN new_column TEXT")

def record_migration(cursor, name, success=True, error=None, time_ms=0):
    cursor.execute("INSERT INTO schema_migrations (migration_name, success, error_message, execution_time_ms) VALUES (?, ?, ?, ?)",
                   (name, success, error, time_ms))

def main():
    start = datetime.now()
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        if migration_already_applied(cursor):
            logger.info("✓ Already applied")
            return 0
        apply_migration(cursor)
        exec_time = int((datetime.now() - start).total_seconds() * 1000)
        record_migration(cursor, Path(__file__).name, execution_time_ms=exec_time)
        conn.commit()
        logger.info(f"✓ Done in {exec_time}ms")
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

## Common SQL Operations

### Add Column
```python
cursor.execute("ALTER TABLE TableName ADD COLUMN column_name TEXT")
```

### Create Table
```python
cursor.execute("""
    CREATE TABLE IF NOT EXISTS TableName (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL
    )
""")
```

### Create Index
```python
cursor.execute("CREATE INDEX IF NOT EXISTS idx_name ON TableName(column)")
```

### Update Data
```python
cursor.execute("UPDATE TableName SET column = ? WHERE id = ?", (value, id))
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Migration not running | Check `docker logs <container> \| grep migration` |
| Already applied but need to re-run | Delete from `schema_migrations` table |
| Table locked | Restart container: `docker restart <container>` |
| Column already exists error | Check `migration_already_applied()` logic |
| Migration failed | Check logs, fix code, remove from tracking, retry |

## Deployment Flow

```
1. Write migration → 2. Test locally → 3. Commit & push
                ↓
4. GitHub Actions builds image → 5. Watchtower pulls image
                ↓
6. Container restarts → 7. docker-entrypoint.sh runs migrations
                ↓
8. App starts with new schema ✅
```

---

For detailed documentation, see [MIGRATIONS.md](MIGRATIONS.md)
