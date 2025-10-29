# Framework Migration Support - Implementation Complete

**Date:** October 29, 2025  
**Feature:** Automatic Database Migration Support for All Docker App Instances  
**Status:** ✅ Complete

---

## Overview

The framework now includes **comprehensive database migration support** for all Docker app instances. When you update an app, database migrations are automatically applied, ensuring all instances stay in sync with the latest schema changes.

This update was triggered by the implementation of **relationship-based template sharing** (`add_entry_level_template_sharing.py` migration), but the solution is **generic** and supports all future migrations.

---

## What Was Implemented

### 1. Enhanced Update Script (`app-instance-template/update.sh`)

**Changes:**
- Added **Step 5: Run database migrations** after container start
- Automatically detects all migration files in `/app/migrations/`
- Runs new migrations, skips already-applied ones
- Reports migration count and status
- Continues gracefully if no migrations exist

**Example Output:**
```
Step 5: Running database migrations...
  Running migration: add_entry_level_template_sharing.py
    ↳ Applied successfully
✓ Applied 1 new migration(s)
```

### 2. Standalone Migration Runner (`app-instance-template/run-migrations.sh`)

**New file with features:**
- ✅ Creates automatic backup before running migrations
- ✅ Runs all pending migrations from `/app/migrations/`
- ✅ Shows detailed progress for each migration
- ✅ Skips already-applied migrations
- ✅ Handles errors with rollback guidance
- ✅ Provides migration summary report
- ✅ Can be run independently of updates

**Usage:**
```bash
cd ~/apps/my-app
./run-migrations.sh
```

### 3. Updated Documentation

#### **docs/framework/DEPLOYMENT_GUIDE.md**

Added new section: **Database Migrations**
- Explanation of what migrations are
- How automatic migrations work
- Manual migration execution
- Migration safety features (backups, idempotency)
- Checking migration status
- Current migrations list
- Troubleshooting guide

#### **docs/framework/UPDATE_GUIDE.md**

Enhanced sections:
- **Update process** now shows migration step in output
- **Migration Handling During Updates** - detailed explanation
- **Manual Migration After Update** - standalone execution
- **Rollback Procedures** - updated with migration-specific rollback options
- **Rollback Decision Matrix** - when to use which rollback method

#### **app-instance-template/README.md**

Major enhancements:
- **Database Migrations** section added
- Explanation of migration system
- Automatic vs manual execution
- Safety features and backups
- Current migrations list
- Updated **File Structure** to show migration backups
- Updated **Updating** section with migration details
- Enhanced **Rollback** instructions

---

## How It Works

### For End Users (App Instance Owners)

**Update Process (Automated):**
```bash
cd ~/apps/my-app
./update.sh
```

The script now:
1. Creates backup (as before)
2. Pulls new image (as before)
3. Restarts container (as before)
4. **🆕 Runs migrations automatically**
5. Verifies health (as before)

**No manual intervention required!** Migrations "just work" ✅

### For Framework Developers

**Adding New Migrations:**
1. Create migration file in `migrations/` directory
2. Migration should be idempotent (safe to run multiple times)
3. Migration should check if already applied and skip if so
4. Commit and push to framework
5. All app instances will auto-apply on next update

**Example Migration Structure:**
```python
def migrate():
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if already applied
    cursor.execute("PRAGMA table_info(TableName)")
    if 'new_column' in columns:
        print("Migration already applied")
        return
    
    # Apply migration
    cursor.execute("ALTER TABLE TableName ADD COLUMN new_column TEXT")
    conn.commit()
    print("Migration applied successfully")
```

---

## Migration Safety Features

### 1. Automatic Backups

**Two levels of backups:**

**Update Backups:**
- Created by `update.sh` before any changes
- Located in app root: `backup-YYYYMMDD-HHMMSS.tar.gz`
- Contains full data directory
- Use for: Complete rollback after failed update

**Migration Backups:**
- Created by `run-migrations.sh` before running migrations
- Located in: `migration-backups/db-before-migration-*.tar.gz`
- Contains database only
- Use for: Quick database-only rollback

### 2. Idempotent Execution

- Migrations can be run multiple times safely
- Each migration checks if already applied
- Skips if changes already exist
- No duplicate data or schema conflicts

### 3. Error Handling

- Failed migrations stop the process
- Clear error messages displayed
- Backup location shown for rollback
- Container continues running (old schema)
- Can retry after fixing issue

### 4. Detailed Logging

- Shows each migration being run
- Reports success/skip/failure for each
- Provides summary at end
- Saves output for troubleshooting

---

## Rollback Procedures

### Full Rollback (Code + Database)

```bash
docker-compose down
tar -xzf backup-20251029-143022.tar.gz
docker-compose up -d
```

### Database-Only Rollback (Keep New Code)

```bash
docker-compose down
tar -xzf migration-backups/db-before-migration-20251029-150000.tar.gz
docker-compose up -d
```

**⚠️ Warning:** Only use database-only rollback if you're sure the new code is compatible with old schema.

### Version Rollback (Use Old Image)

```bash
# Edit .env
VERSION=v1.1.0

docker-compose pull
docker-compose down
docker-compose up -d
```

---

## Testing

### Test Migration System

**1. Create test app:**
```bash
mkdir ~/apps/migration-test
cd ~/apps/migration-test
cp -r /path/to/template/app-instance-template/* .
cp .env.example .env
# Edit .env: APP_NAME=migration-test, PORT=9001
docker-compose up -d
```

**2. Run migration manually:**
```bash
./run-migrations.sh
```

**Expected output:**
```
Database Migration Runner
==========================

App Name: migration-test

Step 1: Creating database backup...
✓ Backup created: migration-backups/db-before-migration-20251029-150000.tar.gz

Step 2: Running database migrations...

[1] add_entry_level_template_sharing.py
    ↳ Applied successfully

==========================
Migration Summary
==========================
Total migrations found: 1
Applied: 1
Skipped: 0

✓ All migrations completed successfully
```

**3. Run again (should skip):**
```bash
./run-migrations.sh
```

**Expected output:**
```
[1] add_entry_level_template_sharing.py
    ↳ Already applied / Skipped
...
Applied: 0
Skipped: 1
```

**4. Test update script:**
```bash
./update.sh
```

Should show migration step with migrations skipped.

---

## Migration Compatibility

### Backward Compatibility

- Existing apps without migrations: **✅ Works**
  - Migration step detects no migrations and skips
  - No errors, no issues
  
- Apps with old update.sh: **✅ Works**
  - Will work but won't auto-run migrations
  - Can use `run-migrations.sh` manually
  - Should update to new update.sh

### Forward Compatibility

- New migrations: **✅ Auto-detected**
  - Framework adds migration → all apps detect it on next update
  - No code changes needed in app instances
  - Just run `./update.sh` as normal

---

## Current Migrations

### 1. add_entry_level_template_sharing.py

**Purpose:** Enable relationship-based milestone template sharing

**Changes:**
- Adds `source_entry_id` column to `TemplateRelationshipSharing` table
- Updates UNIQUE constraint to include new column
- Preserves existing data (sets NULL for old records)

**Required for:** Milestone template sharing feature

**Documentation:** [RELATIONSHIP_TEMPLATE_SHARING_UPDATE.md](../RELATIONSHIP_TEMPLATE_SHARING_UPDATE.md)

---

## File Changes Summary

### New Files
- `app-instance-template/run-migrations.sh` *(executable, 200+ lines)*

### Modified Files
- `app-instance-template/update.sh` *(added migration step)*
- `app-instance-template/README.md` *(added migration documentation)*
- `docs/framework/DEPLOYMENT_GUIDE.md` *(added migration section)*
- `docs/framework/UPDATE_GUIDE.md` *(enhanced with migration details)*

### Total Changes
- **1 new file**
- **4 files modified**
- **~500 lines of new documentation**
- **~100 lines of new code**

---

## Benefits

### For App Instance Owners

✅ **Zero manual work** - Migrations run automatically  
✅ **Automatic backups** - Safety built-in  
✅ **Clear feedback** - Know what changed  
✅ **Easy rollback** - If something goes wrong  
✅ **No downtime** - Migrations run during update  

### For Framework Developers

✅ **Easy to add migrations** - Just add Python file  
✅ **Reliable deployment** - All apps stay in sync  
✅ **No coordination needed** - Apps update on their own schedule  
✅ **Safe iteration** - Can test migrations before release  
✅ **Clear documentation** - Users know what's happening  

---

## Next Steps for App Instance Owners

### For Existing Apps

**Option 1: Update to new scripts (Recommended)**

```bash
cd ~/apps/my-app

# Backup current scripts
cp update.sh update.sh.old

# Copy new scripts from template
cp /path/to/template/app-instance-template/update.sh .
cp /path/to/template/app-instance-template/run-migrations.sh .
chmod +x update.sh run-migrations.sh

# Test
./run-migrations.sh
```

**Option 2: Keep old scripts, run migrations manually**

```bash
cd ~/apps/my-app

# Copy just the migration runner
cp /path/to/template/app-instance-template/run-migrations.sh .
chmod +x run-migrations.sh

# After each update:
docker-compose pull
docker-compose up -d
./run-migrations.sh
```

### For New Apps

Just use the template as normal - migration support is built-in! ✅

```bash
mkdir ~/apps/new-app
cd ~/apps/new-app
cp -r /path/to/template/app-instance-template/* .
cp .env.example .env
# Configure and run
docker-compose up -d
```

---

## Support

If you encounter issues:

1. **Check logs:** `docker-compose logs`
2. **Review migration output:** Re-run `./run-migrations.sh` for details
3. **Check backups:** `ls -lh backup-*.tar.gz migration-backups/`
4. **Restore if needed:** `tar -xzf backup-*.tar.gz`
5. **Report issues:** Open GitHub issue with migration output

---

## Conclusion

All Docker app instances now have:
- ✅ Automatic migration support
- ✅ Safe, tested update process
- ✅ Comprehensive documentation
- ✅ Easy rollback options
- ✅ Ready for future schema changes

**No manual intervention required for database migrations!** 🎉

---

**End of Implementation Summary**
