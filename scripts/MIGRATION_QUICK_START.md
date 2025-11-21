# Database Migration Scripts - Quick Reference

## Immediate Fix for Dashboard Widgets

If downstream apps can't add widgets to dashboards, run:

```bash
cd /path/to/template
python scripts/fix_dashboard_tables.py
```

This creates the missing Dashboard and DashboardWidget tables in all databases.

**Status:** ✅ Tested and working - Created tables in 3 databases

## Scripts Available

### 1. fix_dashboard_tables.py
**Quick fix for missing Dashboard tables**
- No dependencies required
- Safe to run multiple times
- Creates migration tracking
- Handles permissions gracefully

### 2. migrate_all_databases.py
**Comprehensive migration tool**
```bash
# Preview changes
python scripts/migrate_all_databases.py --dry-run

# Apply all migrations
python scripts/migrate_all_databases.py

# Specific database only
python scripts/migrate_all_databases.py --database homebrew.db
```

### 3. test_auto_migration.py
**Test the auto-migration system**
```bash
python scripts/test_auto_migration.py
```

## Auto-Migration System

The framework now automatically applies schema updates on startup via `app/utils/auto_migrate.py`.

**Zero configuration required for downstream apps!**

## Documentation

- **User Guide:** `DASHBOARD_WIDGET_FIX.md`
- **Technical Details:** `docs/bug-fixes/DATABASE_SCHEMA_ALIGNMENT.md`
- **Implementation Summary:** `docs/bug-fixes/DATABASE_SCHEMA_ALIGNMENT_SUMMARY.md`
- **Full Script Documentation:** See existing `scripts/README.md`

## Verification

Check database status:
```bash
sqlite3 data/yourapp.db "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'Dashboard%';"
```

Should return:
```
Dashboard
DashboardWidget
```

## Support

Issues? Check:
1. Logs: `docker-compose logs -f`
2. Permissions: `ls -la data/*.db`
3. Migration history: `sqlite3 data/app.db "SELECT * FROM schema_migrations;"`

---
**Last Updated:** November 21, 2025  
**Status:** ✅ All databases aligned and working
