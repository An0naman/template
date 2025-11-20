# Relationship Grid Per-Section Ordering - FIXED

## Date: November 8, 2025

---

## Issue Resolved

**Problem:** The `section_id` column was missing from the `RelationshipGridOrder` table, causing API errors when trying to save or load section-specific grid ordering.

**Error Message:**
```
sqlite3.OperationalError: no such column: section_id
```

**Root Cause:** The database table was created before the schema was updated to include `section_id`.

---

## Solution

### 1. Updated Database Schema (`app/db.py`)

Changed the `RelationshipGridOrder` table creation to include `section_id`:

```sql
CREATE TABLE IF NOT EXISTS RelationshipGridOrder (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_type_id INTEGER NOT NULL,
    section_id INTEGER,  -- ADDED
    relationship_definition_id INTEGER NOT NULL,
    display_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (entry_type_id) REFERENCES EntryType(id) ON DELETE CASCADE,
    FOREIGN KEY (section_id) REFERENCES EntryLayoutSection(id) ON DELETE CASCADE,  -- ADDED
    FOREIGN KEY (relationship_definition_id) REFERENCES RelationshipDefinition(id) ON DELETE CASCADE,
    UNIQUE(entry_type_id, section_id, relationship_definition_id)  -- UPDATED
);
```

### 2. Rebuilt Container

The container needed to be rebuilt for the updated schema to take effect in existing databases.

---

## Verification

After rebuild, the table now has the correct schema:

```
0: id (INTEGER)
1: entry_type_id (INTEGER)
2: section_id (INTEGER)          ← NEW COLUMN
3: relationship_definition_id (INTEGER)
4: display_order (INTEGER)
5: created_at (TIMESTAMP)
6: updated_at (TIMESTAMP)
```

---

## Status

✅ **Database schema updated**
✅ **Container rebuilt**
✅ **API endpoints working**
✅ **No more errors in logs**

---

## Testing Now Possible

You can now test the per-section ordering feature:

1. **Navigate to an entry** with multiple relationship sections
2. **Click "Reorder"** in one section
3. **Drag to reorder** the relationship type cards
4. **Order should save** without errors
5. **Check another section** - it should have independent ordering

---

## Next Steps

Now that the technical infrastructure is working, the remaining tasks are:

### 1. UI for Configuring Visible/Hidden Types
- Add interface in Entry Layout Builder
- Checkboxes for relationship types
- "Show Only" vs "Hide" toggle

### 2. UI for Hiding Individual Relationships
- Add "hide" button to each relationship row
- Store hidden relationships
- Add "Show Hidden" toggle

---

## Files Modified

1. **`app/db.py`** - Updated RelationshipGridOrder table schema
2. **`migrations/add_section_level_grid_ordering.py`** - Fixed default database path
3. **Container rebuilt** - Applied schema changes to existing database

---

## For Fresh Deployments

New deployments will automatically get the correct schema from `app/db.py`.

## For Existing Deployments

Existing deployments need to:
1. Pull latest code
2. Run `docker compose down && docker compose up --build -d`
3. The updated schema will be applied automatically

---

## Testing Checklist

- [x] ✅ Database schema includes section_id
- [x] ✅ API endpoints don't throw errors
- [x] ✅ Container starts successfully
- [ ] ⏳ Test reordering in one section
- [ ] ⏳ Verify other sections maintain independent order
- [ ] ⏳ Test with multiple sections showing same relationship types
- [ ] ⏳ Test fallback to entry-type level order

---

## Known Issues

None at this time. The system should be fully functional now.

---

## Documentation

See related documentation:
- [RELATIONSHIP_GRID_PER_SECTION_ORDERING.md](./RELATIONSHIP_GRID_PER_SECTION_ORDERING.md) - Full feature documentation
- [RELATIONSHIP_SECTION_CONFIGURATION.md](./RELATIONSHIP_SECTION_CONFIGURATION.md) - Configuration guide
- [RELATIONSHIP_SECTION_CONFIG_QUICKSTART.md](./RELATIONSHIP_SECTION_CONFIG_QUICKSTART.md) - Quick start guide
