# Relationship Grid Per-Section Ordering - Update

## Date: November 8, 2025 (Updated)

---

## ✅ What Was Fixed

### 1. Grid Ordering Now Per-Section (Not Per-Entry-Type)

**Previous Behavior:**
- Grid ordering was saved at entry-type level
- All relationship sections for that entry type shared the same order
- Reordering in one section affected all other sections

**New Behavior:**
- Grid ordering is saved at section level
- Each relationship section has its own independent order
- Reordering in one section only affects that specific section
- Falls back to entry-type level order if no section-specific order exists

---

## Database Changes

### RelationshipGridOrder Table Updated

Added `section_id` column to support per-section ordering:

**Old Schema:**
```sql
CREATE TABLE RelationshipGridOrder (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_type_id INTEGER NOT NULL,
    relationship_definition_id INTEGER NOT NULL,
    display_order INTEGER NOT NULL DEFAULT 0,
    UNIQUE(entry_type_id, relationship_definition_id)
);
```

**New Schema:**
```sql
CREATE TABLE RelationshipGridOrder (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_type_id INTEGER NOT NULL,
    section_id INTEGER,  -- NEW: References EntryLayoutSection
    relationship_definition_id INTEGER NOT NULL,
    display_order INTEGER NOT NULL DEFAULT 0,
    UNIQUE(entry_type_id, section_id, relationship_definition_id)
);
```

**Key Changes:**
- Added `section_id` column (nullable)
- Updated UNIQUE constraint to include `section_id`
- Added foreign key to `EntryLayoutSection`

**Backward Compatibility:**
- Old entries have `section_id = NULL` (entry-type level)
- New entries have specific `section_id` (section level)
- Section-specific order overrides entry-type level order

---

## API Changes

### New Endpoints

#### 1. Get Section Grid Order
```http
GET /api/sections/{section_id}/relationship_grid_order
```

**Returns:**
```json
{
  "1": 0,
  "2": 1,
  "3": 2
}
```

**Logic:**
1. Try to get section-specific order (where `section_id` matches)
2. If none found, fall back to entry-type level order (where `section_id IS NULL`)
3. Return empty object if no order configured

#### 2. Save Section Grid Order
```http
POST /api/sections/{section_id}/relationship_grid_order
Content-Type: application/json

{
  "order": [
    {"definition_id": 1, "order": 0},
    {"definition_id": 2, "order": 1}
  ]
}
```

**Returns:**
```json
{
  "success": true,
  "message": "Section grid order saved successfully"
}
```

### Updated Endpoints

#### Modified: Save Entry-Type Grid Order
```http
POST /api/entry_types/{entry_type_id}/relationship_grid_order
```

**Changes:**
- Now saves with `section_id = NULL` (entry-type level)
- Only deletes entries where `section_id IS NULL`
- Preserves section-specific orders

---

## Template Changes

### _relationships_section_configurable.html

**Load Order:**
```javascript
// OLD: Load entry-type level order
const orderResponse = await fetch(`/api/entry_types/${currentEntryTypeId}/relationship_grid_order`);

// NEW: Load section-specific order
const orderResponse = await fetch(`/api/sections/{{ section_id }}/relationship_grid_order`);
```

**Save Order:**
```javascript
// OLD: Save to entry-type level
const response = await fetch(`/api/entry_types/${currentEntryTypeId}/relationship_grid_order`, {
    method: 'POST',
    body: JSON.stringify({ order: orderList })
});

// NEW: Save to section level
const response = await fetch(`/api/sections/{{ section_id }}/relationship_grid_order`, {
    method: 'POST',
    body: JSON.stringify({ order: orderList })
});
```

**Notification Update:**
```javascript
// OLD: Shows "Grid order saved for all entries of this type"
showNotification('Grid order saved for all entries of this type', 'success');

// NEW: Shows "Grid order saved for this section"
showNotification('Grid order saved for this section', 'success');
```

---

## Files Modified

### 1. `/migrations/add_section_level_grid_ordering.py`
- **New file**: Migration to add `section_id` column
- Handles table recreation with new schema
- Preserves existing data (sets `section_id = NULL`)
- Creates appropriate indexes

### 2. `/app/db.py`
- Updated `RelationshipGridOrder` table creation
- Added `section_id` column to schema
- Updated UNIQUE constraint
- Added foreign key to `EntryLayoutSection`

### 3. `/app/api/relationships_api.py`
- Added `get_section_relationship_grid_order()` endpoint
- Added `save_section_relationship_grid_order()` endpoint
- Updated `save_relationship_grid_order()` to preserve section orders

### 4. `/app/templates/sections/_relationships_section_configurable.html`
- Changed API endpoint from entry-type to section level
- Updated fetch URLs for load and save
- Updated success messages

---

## How It Works Now

### Ordering Hierarchy

```
1. Check for section-specific order (section_id = X)
   ↓ If not found
2. Check for entry-type level order (section_id = NULL)
   ↓ If not found
3. Use default order (by definition ID)
```

### Example Scenario

**Entry Type: Organization**

**Section 1 (ID: 10): "Organizational Structure"**
- Visible Types: [Parent Organization, Child Organizations]
- Custom Order: Child Organizations (0), Parent Organization (1)

**Section 2 (ID: 11): "Business Partners"**
- Visible Types: [Suppliers, Customers]  
- Custom Order: Customers (0), Suppliers (1)

**Result:**
- Section 1 shows Children first, then Parent
- Section 2 shows Customers first, then Suppliers
- Each section maintains its own independent order
- Reordering in Section 1 doesn't affect Section 2

---

## Migration Path

### For Existing Deployments

1. **Backup Database**
   ```bash
   docker compose exec template sqlite3 data/database.db ".backup data/database_backup.db"
   ```

2. **Pull Latest Code**
   ```bash
   git pull
   ```

3. **Rebuild Container**
   ```bash
   docker compose down
   docker compose up --build -d
   ```

4. **Verify**
   - Check that existing grid orders still work
   - Test reordering in different sections
   - Confirm sections maintain independent orders

### Data Migration

**Existing entries** in `RelationshipGridOrder`:
- Have `section_id = NULL`
- Apply to all sections of that entry type (backward compatible)

**New entries** will have specific `section_id`:
- Apply only to that section
- Override entry-type level order for that section

---

## Testing Checklist

- [x] ✅ Section-specific ordering works
- [x] ✅ Multiple sections can have different orders
- [x] ✅ Reordering in one section doesn't affect others
- [x] ✅ API endpoints return correct data
- [x] ✅ Save persists to database correctly
- [x] ✅ Fallback to entry-type level works
- [ ] ⏳ Verify with fresh database
- [ ] ⏳ Verify with existing data migration

---

## Still To Implement

### 1. Filter Configuration UI

Currently, visible/hidden relationship types must be configured via SQL. Need to add UI in Entry Layout Builder:

```javascript
// Planned UI elements:
- Checkbox list of available relationship types
- "Show Only" vs "Hide" toggle
- Live preview of visible types
- Save button to update section.config
```

### 2. Hide Individual Relationships

Currently can only hide/show entire relationship types. Need ability to hide specific relationship instances:

- Add "hide" button to each relationship row
- Store hidden relationships in separate table or config
- Filter out hidden relationships when rendering
- Provide "Show Hidden" toggle

---

## Benefits of Per-Section Ordering

✅ **Independent Sections** - Each section can have its own logical order  
✅ **Context-Appropriate** - Order by importance within each context  
✅ **Multiple Perspectives** - Same data, different organizations  
✅ **No Conflicts** - Changes don't affect other sections  
✅ **Backward Compatible** - Old orders still work (entry-type level)  
✅ **Flexible** - Can use entry-type level or section level as needed  

---

## Example Use Cases

### Use Case 1: Priority-Based Sections

**Section A: "Critical Relationships"**
```
1. Primary Contact
2. Emergency Contact
3. Legal Representative
```

**Section B: "All Contacts" (Alphabetical)**
```
1. Emergency Contact
2. Legal Representative  
3. Primary Contact
```

### Use Case 2: Workflow-Based Sections

**Section A: "Production Flow"**
```
1. Suppliers
2. Manufacturers
3. Distributors
4. Customers
```

**Section B: "Financial View"**
```
1. Customers
2. Distributors
3. Suppliers
4. Manufacturers
```

---

## Known Issues

None currently identified.

---

## References

- Original Implementation: [RELATIONSHIP_GRID_ORDERING.md](./RELATIONSHIP_GRID_ORDERING.md)
- Configuration Guide: [RELATIONSHIP_SECTION_CONFIGURATION.md](./RELATIONSHIP_SECTION_CONFIGURATION.md)
- Quick Start: [RELATIONSHIP_SECTION_CONFIG_QUICKSTART.md](./RELATIONSHIP_SECTION_CONFIG_QUICKSTART.md)

---

## Version History

- **v1.0** (2025-11-08): Initial section configuration support
- **v1.1** (2025-11-08): Per-section ordering (this update)
