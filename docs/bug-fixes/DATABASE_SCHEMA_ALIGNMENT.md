# Database Schema Alignment Solution

## Problem Summary

Downstream apps (Game Development, Hardware Design/Build, and others) were unable to add new widgets to their dashboards. The root cause was **schema misalignment** across multiple database files, with some databases missing critical tables like `Dashboard` and `DashboardWidget`.

### Key Issues Identified

1. **Multiple Database Files**: The framework has multiple `.db` files in the `data/` directory, each potentially serving different downstream apps
2. **Inconsistent Migrations**: Migration files exist in two locations (`migrations/` and `app/migrations/`), causing confusion
3. **No Migration Tracking**: Most databases lacked the `schema_migrations` table to track which migrations were applied
4. **Manual Migration Process**: Migrations required manual execution and weren't automatically applied during app startup
5. **Missing Tables**: Databases like `homebrew.db`, `tracker.db`, `entries.db`, `lifestack.db`, and `database.db` were missing the `Dashboard` and `DashboardWidget` tables

### Analysis Results

```
Database Status (before fix):
- app.db: ✓ Has Dashboard tables
- template.db: ✓ Has Dashboard tables  
- homebrew.db: ✗ Missing Dashboard tables
- tracker.db: ✗ Missing Dashboard tables
- entries.db: ✗ Missing Dashboard tables
- lifestack.db: ✗ Missing Dashboard tables
- database.db: ✗ Missing Dashboard tables
```

## Solution Implemented

### 1. Auto-Migration System (`app/utils/auto_migrate.py`)

Created an automatic migration system that runs on app startup to ensure schema consistency across all databases.

**Features:**
- Automatic detection and creation of missing tables
- Migration tracking via `schema_migrations` table
- Inline critical migrations (Dashboard, EntryState, SavedSearch)
- Non-blocking: warnings logged but app continues if migration fails
- Zero configuration required for downstream apps

**Critical Migrations Applied:**
- Dashboard and DashboardWidget tables
- EntryState table for configurable statuses
- SavedSearch table for search configurations
- Migration tracking infrastructure

### 2. Unified Migration Tool (`scripts/migrate_all_databases.py`)

Created a comprehensive command-line tool for manual migration management across all databases.

**Usage:**
```bash
# Migrate all databases
python scripts/migrate_all_databases.py

# Dry run to see what would be done
python scripts/migrate_all_databases.py --dry-run

# Migrate specific database
python scripts/migrate_all_databases.py --database homebrew.db
```

**Features:**
- Processes all `.db` files in `data/` directory
- Applies base schema from `db.py init_db()`
- Runs all migrations from both `migrations/` and `app/migrations/`
- Smart detection: skips migrations if tables already exist
- Detailed logging and progress reporting
- Migration tracking and rollback support

### 3. Framework Integration

The auto-migration system is integrated into the Flask app initialization (`app/__init__.py`), ensuring:
- Runs automatically when any app instance starts
- Checks database schema before serving requests
- Updates schema if new migrations are available
- Graceful handling of migration failures

## How It Works

### Startup Flow

```
App Startup
    ↓
Flask create_app()
    ↓
Auto-Migration Check
    ↓
Create schema_migrations table
    ↓
Check for missing tables
    ↓
Apply critical migrations inline
    ↓
Record migrations in tracking table
    ↓
Continue app initialization
```

### Migration Tracking

Each database now maintains a `schema_migrations` table:

```sql
CREATE TABLE schema_migrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    migration_name TEXT UNIQUE NOT NULL,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    execution_time_ms INTEGER
);
```

This ensures:
- Migrations are never applied twice
- Failed migrations are logged
- Migration history is preserved
- Easy debugging and auditing

## Benefits for Downstream Apps

### Immediate Benefits

1. **Zero Configuration**: Downstream apps get schema updates automatically
2. **No Manual Intervention**: No need to run migration scripts manually
3. **Backward Compatible**: Existing databases are updated safely
4. **Dashboard Widgets Work**: All apps can now add widgets without errors
5. **Consistent Schemas**: All databases have the same table structure

### Future Benefits

1. **Easy Updates**: New framework features with schema changes deploy seamlessly
2. **No Breaking Changes**: Migration system handles schema evolution
3. **Developer Friendly**: New migrations are automatically discovered and applied
4. **Audit Trail**: Complete history of schema changes in each database

## Migration Strategy

### For Existing Downstream Apps

**When apps update to the new framework version:**

1. App container pulls new image
2. App starts up
3. Auto-migration detects missing tables
4. Tables are created automatically
5. Migration is recorded
6. App becomes fully functional

**No action required from app maintainers!**

### For New Downstream Apps

New apps automatically get:
- Complete schema from `init_db()`
- All critical migrations applied
- Migration tracking enabled
- Dashboard functionality ready to use

### Manual Migration (if needed)

If you need to manually migrate databases:

```bash
# From the template directory
cd /home/an0naman/Documents/GitHub/template

# Test what would be migrated (dry run)
python scripts/migrate_all_databases.py --dry-run

# Migrate all databases
python scripts/migrate_all_databases.py

# Migrate specific database
python scripts/migrate_all_databases.py --database homebrew.db
```

## Testing the Solution

### Test Auto-Migration

```bash
# Start any downstream app
cd ~/apps/game-development
docker-compose up -d

# Check logs for migration messages
docker-compose logs -f

# Expected output:
# INFO - Running auto-migration check...
# INFO - Checking for critical schema updates...
# INFO - ✓ Dashboard tables already exist
# INFO - ✓ Auto-migration completed
```

### Test Dashboard Widgets

1. Access the app: `http://localhost:PORT`
2. Navigate to **Dashboards**
3. Click **Edit Dashboard** or create new dashboard
4. Click **Add Widget**
5. Select widget type and configure
6. Click **Save Widget**
7. Widget should be added successfully ✓

### Verify Schema

```bash
# Check if tables exist
sqlite3 data/homebrew.db "SELECT name FROM sqlite_master WHERE type='table' AND name='Dashboard';"

# Check migration history
sqlite3 data/homebrew.db "SELECT * FROM schema_migrations ORDER BY applied_at DESC LIMIT 5;"
```

## Architecture Improvements

### Before

```
Multiple Databases
├── app.db (Dashboard ✓)
├── template.db (Dashboard ✓)
├── homebrew.db (Dashboard ✗)
├── tracker.db (Dashboard ✗)
└── entries.db (Dashboard ✗)

Migration Files
├── migrations/ (old location)
└── app/migrations/ (new location)

Migration Process: Manual, error-prone
Tracking: None or inconsistent
```

### After

```
All Databases Have Consistent Schema
├── app.db (Dashboard ✓, Tracked ✓)
├── template.db (Dashboard ✓, Tracked ✓)
├── homebrew.db (Dashboard ✓, Tracked ✓)
├── tracker.db (Dashboard ✓, Tracked ✓)
└── entries.db (Dashboard ✓, Tracked ✓)

Unified Migration System
├── Auto-migration on startup
├── Manual tool for batch operations
└── Single source of truth for schema

Migration Tracking: Comprehensive
Status: Fully automated and reliable
```

## Files Changed/Created

### New Files

1. **`app/utils/auto_migrate.py`** - Auto-migration system
   - Runs on app startup
   - Applies critical migrations inline
   - Migration tracking

2. **`scripts/migrate_all_databases.py`** - Unified migration tool
   - Command-line interface
   - Batch database operations
   - Comprehensive logging

3. **`docs/bug-fixes/DATABASE_SCHEMA_ALIGNMENT.md`** - This documentation

### Modified Files

1. **`app/__init__.py`** - Integrated auto-migration into app startup
   - Added import for auto_migrate
   - Calls migration check after database initialization
   - Graceful error handling

## Maintenance Notes

### Adding New Migrations

When adding new framework features that require schema changes:

1. **Option A: Add to auto_migrate.py** (recommended for critical tables)
   ```python
   # In apply_critical_migrations() method
   migration_name = "add_new_feature_table.py"
   if not self.is_migration_applied(migration_name):
       if not self.check_table_exists('NewFeatureTable'):
           # Create table SQL here
           cursor.execute('''CREATE TABLE...''')
           conn.commit()
           self.record_migration(migration_name, success=True)
   ```

2. **Option B: Create standalone migration file** (for complex migrations)
   - Place in `app/migrations/`
   - Follow the template in `app/migrations/_migration_template.py`
   - Will be picked up by auto-migration and unified tool

### Migration Best Practices

1. **Always use CREATE TABLE IF NOT EXISTS** - Safe for re-runs
2. **Record migrations after success** - Prevents duplicate runs
3. **Check table existence before creating** - Skip unnecessary work
4. **Use descriptive migration names** - Easy to identify purpose
5. **Test in development first** - Validate before deployment
6. **Keep migrations small** - Easier to debug and rollback

## Troubleshooting

### Dashboard Widgets Still Not Working

1. **Check logs**:
   ```bash
   docker-compose logs | grep -i migration
   ```

2. **Verify tables exist**:
   ```bash
   sqlite3 data/yourapp.db ".tables" | grep Dashboard
   ```

3. **Check migration tracking**:
   ```bash
   sqlite3 data/yourapp.db "SELECT * FROM schema_migrations;"
   ```

4. **Manual migration**:
   ```bash
   python scripts/migrate_all_databases.py --database yourapp.db
   ```

### Migration Fails on Startup

- Check database file permissions
- Verify database is not corrupted: `sqlite3 data/yourapp.db "PRAGMA integrity_check;"`
- Check available disk space
- Review error logs in `logs/app_errors.log`

### Old Migration Files Conflicting

The unified tool handles both old (`migrations/`) and new (`app/migrations/`) locations, automatically deduplicating by filename.

## Summary

This solution provides a **robust, automated, and maintainable** approach to database schema management across all downstream apps. The framework now:

- ✅ Automatically applies schema updates
- ✅ Tracks migration history  
- ✅ Handles multiple databases gracefully
- ✅ Works with zero configuration for downstream apps
- ✅ Provides tools for manual intervention when needed
- ✅ Maintains backward compatibility
- ✅ Enables dashboard widgets in all apps

**The systemic issue of schema misalignment has been resolved at the framework level.**
