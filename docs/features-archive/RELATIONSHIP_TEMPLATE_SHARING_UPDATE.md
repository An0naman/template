# Relationship-Based Template Sharing - Database Update Guide

**Date:** October 29, 2025  
**Feature:** Milestone Template Sharing via Parent Entries  
**Impact:** Database schema changes required

---

## Overview

This update introduces **relationship-based template sharing**, allowing milestone templates to be shared between entries that have a common "parent" entry in their relationships, rather than just sharing by entry type.

### Example Use Case:
- Entry 85 (template) and Entry 94 (consumer) both link to Recipe 93 via a "uses recipe" relationship
- Entry 85 can share its milestone template via Recipe 93
- Entry 94 can discover and import Entry 85's template because they share the same parent
- Entry 84, which links to a different recipe, **cannot** see Entry 85's template

---

## Database Migration Required

### Migration: Add `source_entry_id` Column

**File:** `migrations/add_entry_level_template_sharing.py`

This migration adds the `source_entry_id` column to the `TemplateRelationshipSharing` table to track which parent entry is being used for sharing.

**SQL Changes:**
```sql
ALTER TABLE TemplateRelationshipSharing 
ADD COLUMN source_entry_id INTEGER REFERENCES Entry(id);
```

**To Apply Migration:**

```bash
# Method 1: Run migration script directly
docker exec template python migrations/add_entry_level_template_sharing.py

# Method 2: Run SQL manually inside container
docker exec template python -c "
import sqlite3
conn = sqlite3.connect('/app/data/homebrew.db')
cursor = conn.cursor()
cursor.execute('ALTER TABLE TemplateRelationshipSharing ADD COLUMN source_entry_id INTEGER REFERENCES Entry(id)')
conn.commit()
conn.close()
print('✅ Migration complete: Added source_entry_id column')
"
```

**Verify Migration:**
```bash
docker exec template python -c "
import sqlite3
conn = sqlite3.connect('/app/data/homebrew.db')
cursor = conn.cursor()
cursor.execute('PRAGMA table_info(TemplateRelationshipSharing)')
columns = [row[1] for row in cursor.fetchall()]
print('Columns:', columns)
if 'source_entry_id' in columns:
    print('✅ Migration successful')
else:
    print('❌ Migration needed')
"
```

---

## Code Changes Summary

### 1. API Endpoint Updates

#### **File:** `app/api/milestone_template_api.py`

**Lines 61-84:** Fixed milestone data retrieval
- **Changed:** Table name from `State` to `EntryState`
- **Changed:** Column name from `sequence_number` to `order_position`
- **Added:** Milestone data to API response (milestones array, total_days)

**Before:**
```python
JOIN State s ON esm.target_state_id = s.id
# ... sequence_number
```

**After:**
```python
JOIN EntryState es ON esm.target_state_id = es.id
# ... order_position
```

**API Response Enhanced:**
```json
{
  "entry_id": 85,
  "template_name": "dsds",
  "milestone_count": 3,
  "milestones": [
    {
      "id": 1,
      "order_position": 0,
      "duration_days": 3,
      "target_state_id": 45,
      "target_state_name": "Primary Ferment",
      "target_state_color": "#8ff0a4"
    }
  ],
  "total_days": 10
}
```

#### **File:** `app/api/milestone_template_api.py`

**Lines 500-540:** Fixed SQL column names in GET endpoint
- **Changed:** `rd.source_label` → `rd.label_from_side`
- **Changed:** `rd.target_label` → `rd.label_to_side`

**Lines 544+:** Discovery query now uses `source_entry_id`
```sql
WHERE trs.source_entry_id = ? AND trs.relationship_definition_id = ?
```

#### **File:** `app/api/relationships_api.py`

**Lines 158-210:** Enhanced relationship data
- **Added:** `source_entry_id`, `source_title`
- **Added:** `target_entry_id`, `target_title`

This allows JavaScript to identify which entry is the "parent" in the relationship.

---

### 2. JavaScript Updates

#### **File:** `app/static/js/milestone_templates.js`

**Lines 160-170:** Template object structure
- **Added:** `milestones` array from API response
- **Added:** `total_days` from API response
- **Added:** `owner_type_label` for display consistency

**Lines 545-548:** Template card rendering
- **Fixed:** `data-template-id` to handle both `template_entry_id` and `entry_id`

**Lines 618-631:** Template selection
- **Fixed:** Search logic to check both property names

**Lines 665-680:** Template import
- **Fixed:** Template ID extraction to handle both property names

**Lines 604-627:** Timeline rendering with debug logging
- **Added:** Console logs for troubleshooting (can be removed after deployment)

---

### 3. UI Behavior Changes

#### Template Configuration Modal
- Relationship dropdown now shows parent entries (the linking record)
- Can select multiple parent entries per relationship type
- Configuration saved with `source_entry_id` tracking

#### Template Browser Modal
- Templates discovered via shared parent entries
- Visual milestone preview with colored timeline bars
- Shows template source entry and relationship path
- Import button enabled after template selection

#### Discovery Logic
- **Removed:** Type-based template discovery fallback
- **Enforced:** Only relationship-based sharing (explicit authorization)

---

## Deployment Checklist

### For Each Instance/Database:

- [ ] **1. Backup Database**
  ```bash
  docker exec template cp /app/data/homebrew.db /app/data/homebrew.db.backup-$(date +%Y%m%d)
  ```

- [ ] **2. Pull Latest Code**
  ```bash
  cd /path/to/template
  git pull origin main
  ```

- [ ] **3. Run Database Migration**
  ```bash
  docker exec template python migrations/add_entry_level_template_sharing.py
  ```

- [ ] **4. Verify Migration**
  ```bash
  # Check that source_entry_id column exists
  docker exec template python -c "
  import sqlite3
  conn = sqlite3.connect('/app/data/homebrew.db')
  cursor = conn.cursor()
  cursor.execute('PRAGMA table_info(TemplateRelationshipSharing)')
  print([row[1] for row in cursor.fetchall()])
  "
  ```

- [ ] **5. Rebuild Container**
  ```bash
  docker compose up --build -d
  ```

- [ ] **6. Test Template Sharing**
  - Create/configure a template with relationship sharing
  - Verify parent entry selection works
  - Verify template discovery on related entries
  - Verify milestone preview displays correctly
  - Test import functionality

- [ ] **7. Monitor Logs**
  ```bash
  docker logs template --tail 100 -f
  ```
  - Watch for SQL errors (table/column not found)
  - Verify API endpoints return 200 OK

---

## Troubleshooting

### Issue: 500 Error - "no such table: State"
**Solution:** Your database uses `EntryState` table. This is already fixed in the code update.

### Issue: 500 Error - "no such column: sequence_number"
**Solution:** Your database uses `order_position` column. This is already fixed in the code update.

### Issue: 500 Error - "no such column: source_entry_id"
**Solution:** Run the database migration to add this column.

### Issue: Milestone preview blank/not displaying
**Symptoms:** Modal shows "3 milestones" badge but no visual timeline
**Solution:** 
1. Check browser console for errors
2. Verify API returns `milestones` array and `total_days`
3. Rebuild container to get latest JavaScript changes

### Issue: Import button unresponsive
**Symptoms:** Clicking import does nothing
**Solution:** 
1. Check that template card has correct `data-template-id`
2. Verify JavaScript fixes for property name handling
3. Rebuild container

### Issue: Templates appearing on wrong entries
**Symptoms:** Entry sees templates it shouldn't have access to
**Solution:** 
1. Check that type-based discovery is disabled in JavaScript
2. Verify `source_entry_id` is saved in configuration
3. Check discovery query uses correct parent entry ID

---

## Verification Tests

### Test 1: Parent-Based Sharing
1. Entry A has milestones, marked as template
2. Entry B and Entry C both link to Parent Entry P
3. Entry A configures sharing via Parent P
4. **Expected:** Entry B and C can see Entry A's template
5. Entry D links to different parent
6. **Expected:** Entry D cannot see Entry A's template

### Test 2: Milestone Preview
1. Open template browser on entry with shared templates
2. Select relationship dropdown
3. Select parent entry
4. **Expected:** Template card shows:
   - Template name and description
   - Milestone count badge
   - Visual colored timeline with bars for each milestone
   - Total duration in days
   - Source entry name

### Test 3: Template Import
1. Select a template from browser
2. **Expected:** Import options section appears
3. Choose Replace or Append mode
4. Click Import Template button
5. **Expected:** Success notification, page reloads with new milestones

### Test 4: Configuration Persistence
1. Configure template sharing with multiple parent entries
2. Save configuration
3. Close modal
4. Reopen template configuration modal
5. **Expected:** 
   - Relationship dropdown pre-selected
   - Checkboxes for selected parents are checked
   - Configuration displayed correctly

---

## Rollback Plan

If issues occur after deployment:

### Option 1: Restore Database Backup
```bash
docker exec template cp /app/data/homebrew.db.backup-YYYYMMDD /app/data/homebrew.db
docker compose restart
```

### Option 2: Revert Code Changes
```bash
git revert <commit-hash>
docker compose up --build -d
```

### Option 3: Remove source_entry_id Column
**Note:** This will lose all parent-based sharing configurations
```bash
docker exec template python -c "
import sqlite3
conn = sqlite3.connect('/app/data/homebrew.db')
cursor = conn.cursor()

# SQLite doesn't support DROP COLUMN directly, need to recreate table
cursor.execute('''
    CREATE TABLE TemplateRelationshipSharing_backup AS 
    SELECT id, template_entry_id, relationship_definition_id, created_at 
    FROM TemplateRelationshipSharing
''')
cursor.execute('DROP TABLE TemplateRelationshipSharing')
cursor.execute('''
    CREATE TABLE TemplateRelationshipSharing (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        template_entry_id INTEGER NOT NULL,
        relationship_definition_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (template_entry_id) REFERENCES Entry(id) ON DELETE CASCADE,
        FOREIGN KEY (relationship_definition_id) REFERENCES RelationshipDefinition(id) ON DELETE CASCADE,
        UNIQUE(template_entry_id, relationship_definition_id)
    )
''')
cursor.execute('INSERT INTO TemplateRelationshipSharing SELECT * FROM TemplateRelationshipSharing_backup')
cursor.execute('DROP TABLE TemplateRelationshipSharing_backup')
conn.commit()
"
```

---

## Files Modified

### Database Migrations:
- `migrations/add_entry_level_template_sharing.py` (NEW)

### Python Backend:
- `app/api/milestone_template_api.py` (MODIFIED - critical fixes)
- `app/api/relationships_api.py` (MODIFIED - enhanced data)

### JavaScript Frontend:
- `app/static/js/milestone_templates.js` (MODIFIED - multiple fixes)

### Documentation:
- This file (NEW)

---

## Schema Reference

### TemplateRelationshipSharing Table (After Migration)

```sql
CREATE TABLE TemplateRelationshipSharing (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_entry_id INTEGER NOT NULL,
    relationship_definition_id INTEGER NOT NULL,
    source_entry_id INTEGER,  -- NEW COLUMN
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (template_entry_id) REFERENCES Entry(id) ON DELETE CASCADE,
    FOREIGN KEY (relationship_definition_id) REFERENCES RelationshipDefinition(id) ON DELETE CASCADE,
    FOREIGN KEY (source_entry_id) REFERENCES Entry(id) ON DELETE CASCADE,
    UNIQUE(template_entry_id, relationship_definition_id, source_entry_id)
);
```

**Columns:**
- `id`: Primary key
- `template_entry_id`: Entry that is being shared as a template
- `relationship_definition_id`: Type of relationship (e.g., "uses recipe")
- `source_entry_id`: **NEW** - The parent entry through which sharing occurs
- `created_at`: Timestamp of configuration

---

## Support

If you encounter issues during deployment:

1. **Check logs:** `docker logs template --tail 100`
2. **Verify migration:** Check that `source_entry_id` column exists
3. **Test API:** Visit `/api/entries/<id>/milestone-template` in browser
4. **Console logs:** Check browser console for JavaScript errors
5. **Database backup:** Always create backup before migration

---

## Notes

- **Breaking Change:** Existing template sharing configurations will need to be reconfigured to specify parent entries
- **Data Migration:** Existing `TemplateRelationshipSharing` records will have `source_entry_id = NULL` until reconfigured
- **Backward Compatibility:** Type-based template discovery is now disabled to enforce proper authorization
- **Performance:** No significant impact - queries use indexed columns
- **Security:** Enhanced - templates only visible to explicitly authorized entries

---

**End of Update Document**
