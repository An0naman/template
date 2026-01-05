# Quick Fix: Dashboard Widgets Not Working

## Problem
Can't add widgets to dashboards in downstream apps (Game Development, Hardware Design, etc.)

## Root Cause
Database schema was missing `Dashboard` and `DashboardWidget` tables.

## Solution Applied ✓

The framework now includes:
1. **Auto-migration on startup** - Automatically creates missing tables
2. **Migration tracking** - Prevents duplicate migrations
3. **Multiple database support** - Works with all downstream app databases

## For Downstream App Users

### If Using Docker (Most Common)

Simply restart your app container to apply the fix:

```bash
cd ~/apps/your-app-name
docker-compose pull      # Get latest framework
docker-compose down
docker-compose up -d
docker-compose logs -f   # Watch for migration messages
```

Look for these log messages confirming the fix:
```
INFO - Running auto-migration check...
INFO - ✓ Dashboard tables created
INFO - ✓ Auto-migration completed
```

### If Running Directly (Without Docker)

Run the fix script:

```bash
cd /path/to/template
python scripts/fix_dashboard_tables.py
```

Expected output:
```
✓ your-app.db - Dashboard tables CREATED
```

## Verify the Fix

1. Open your app in a browser
2. Go to **Dashboards** 
3. Click **Edit Dashboard** or create new dashboard
4. Click **Add Widget**
5. Configure and save widget
6. Widget should appear successfully ✓

## What Was Fixed

### Before
```
homebrew.db      - ✗ Missing Dashboard tables
tracker.db       - ✗ Missing Dashboard tables  
entries.db       - ✗ Missing Dashboard tables
database.db      - ✗ Missing Dashboard tables
```

### After
```
All databases    - ✓ Dashboard tables present
All databases    - ✓ Migration tracking enabled
All databases    - ✓ Auto-migration active
```

## No Action Required

The framework now handles this automatically. Future schema updates will also be applied automatically.

## Troubleshooting

### Problem: Still can't add widgets after update

**Check database permissions:**
```bash
ls -la ~/apps/your-app/data/*.db
```

If owned by `root`, fix permissions:
```bash
sudo chown $USER:$USER ~/apps/your-app/data/*.db
```

Then restart the app.

### Problem: "Database is locked" error

Your app is still running. Stop it first:
```bash
docker-compose down
# or
pkill -f "python.*run.py"
```

Then start it again.

### Problem: Tables exist but widgets still don't work

Check the table structure:
```bash
sqlite3 data/your-app.db "PRAGMA table_info(Dashboard);"
sqlite3 data/your-app.db "PRAGMA table_info(DashboardWidget);"
```

Should show 7 columns in Dashboard, 14 columns in DashboardWidget.

If columns are missing, re-run the fix script:
```bash
python scripts/fix_dashboard_tables.py
```

## Technical Details (For Framework Developers)

### New Files Created

1. **`app/utils/auto_migrate.py`** - Auto-migration system (runs on startup)
2. **`scripts/migrate_all_databases.py`** - Comprehensive migration tool (manual use)
3. **`scripts/fix_dashboard_tables.py`** - Quick fix script (one-time use)

### Integration Points

- **`app/__init__.py`** - Calls auto-migration after database initialization
- **`app/db.py`** - Base schema still created via init_db()
- **Migration tracking** - All migrations recorded in `schema_migrations` table

### Migration Strategy

1. App starts
2. Auto-migration checks for `schema_migrations` table
3. Creates table if missing
4. Checks for critical tables (Dashboard, DashboardWidget, etc.)
5. Creates missing tables
6. Records migration
7. App continues normally

### Adding New Migrations

Add to `app/utils/auto_migrate.py` in the `apply_critical_migrations()` method:

```python
# Migration: Add YourNewFeature table
migration_name = "add_your_feature_table.py"
if not self.is_migration_applied(migration_name):
    if not self.check_table_exists('YourFeatureTable'):
        cursor.execute('''CREATE TABLE...''')
        conn.commit()
        self.record_migration(migration_name, success=True)
```

## Support

If issues persist:
1. Check logs: `docker-compose logs -f` or `logs/app_errors.log`
2. Verify database integrity: `sqlite3 data/app.db "PRAGMA integrity_check;"`
3. Check disk space: `df -h`
4. Review migration history: `sqlite3 data/app.db "SELECT * FROM schema_migrations;"`

## Related Documentation

- Full technical details: `docs/bug-fixes/DATABASE_SCHEMA_ALIGNMENT.md`
- Migration system: `scripts/migrate_all_databases.py --help`
- Auto-migration: `app/utils/auto_migrate.py`
