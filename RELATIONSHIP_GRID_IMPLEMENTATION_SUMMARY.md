# Relationship Grid Features - Implementation Summary

## Date: November 8, 2025

---

## Features Implemented

### ✅ 1. Section-Level Visibility Configuration

Each relationships section can now filter which relationship types are displayed using configuration stored in the `EntryLayoutSection.config` field.

**Configuration Options:**
- `visible_relationship_types`: Array of relationship definition IDs to show (whitelist)
- `hidden_relationship_types`: Array of relationship definition IDs to hide (blacklist)

**Logic:**
- If `visible_relationship_types` is set and non-empty: Only show those types
- Else if `hidden_relationship_types` is set and non-empty: Show all except those types  
- Else: Show all relationship types (default behavior)

**Use Cases:**
- Multiple relationship sections on same entry type, each showing different subsets
- Focused views (e.g., "Organizational Relationships", "Team & Projects", "Business Partners")
- Hide irrelevant relationship types to reduce clutter

---

### ✅ 2. Relationship Grid Ordering (Restored)

The drag-and-drop reordering functionality now works correctly within each section instance.

**Features:**
- **Reorder Button**: Appears when there are 2+ relationship types
- **Drag Handles**: Visual grip icons appear in reorder mode
- **Drag & Drop**: Smooth reordering with visual feedback
- **Auto-Save**: Order is saved to database automatically
- **Entry Type Level**: Order applies to all entries of the same type
- **Persistent**: Uses `RelationshipGridOrder` table

**How to Use:**
1. Click "Reorder" button in section header
2. Drag handles (⋮⋮) appear on left side of each card
3. Click and drag cards to reorder
4. Order is saved automatically
5. Click "Done" to exit reorder mode

**Technical:**
- Order stored in `RelationshipGridOrder` table
- Keyed by `entry_type_id` and `relationship_definition_id`
- Applied during card rendering via sorting

---

## Files Created

### 1. `/app/templates/sections/_relationships_section_configurable.html`

New template that combines:
- Section-level configuration support
- Relationship type filtering
- Grid ordering functionality  
- Empty card hiding
- All features from _relationships_section_v2.html

**Key Features:**
- Self-contained with inline JavaScript
- Supports multiple instances with unique section IDs
- Filters definitions before rendering
- Sorts by custom grid order

---

## Files Modified

### 1. `/app/templates/entry_detail_v2.html`

Changed relationships section include from:
```jinja2
{% include 'sections/_relationships_section.html' %}
```

To:
```jinja2
{% with section_id=section.id, section_config=section.config %}
    {% include 'sections/_relationships_section_configurable.html' %}
{% endwith %}
```

This passes the section configuration to the template.

---

### 2. `/app/templates/sections/_relationships_section.html`

Updated to receive and parse `section_config`:
- Added config parsing for visible/hidden types
- Added data attributes to container
- Updated JavaScript initialization to pass config

(Note: This file is now superseded by `_relationships_section_configurable.html`)

---

## Documentation Created

### 1. `RELATIONSHIP_SECTION_CONFIGURATION.md`

Complete technical documentation covering:
- Feature overview
- Configuration structure
- Implementation details
- Testing procedures
- Benefits and use cases
- Next steps (UI in layout builder)

### 2. `RELATIONSHIP_SECTION_CONFIG_QUICKSTART.md`

User-friendly guide covering:
- How to configure sections manually via SQL
- Example use cases with SQL snippets
- Multiple sections setup
- Verification queries
- Troubleshooting

---

## How It Works

### Template Flow

1. **Entry Detail Page Loads**
   ```
   entry_detail_v2.html
   └─ Includes _relationships_section_configurable.html
      └─ Passes: section_id, section_config
   ```

2. **Template Parses Config**
   ```jinja2
   {% set visible_rel_types = config.get('visible_relationship_types', []) %}
   {% set hidden_rel_types = config.get('hidden_relationship_types', []) %}
   ```

3. **JavaScript Loads**
   - Fetches all relationship definitions
   - Filters by entry type
   - **Applies section-level filtering**
   - Fetches custom grid order
   - **Sorts by grid order**
   - Renders cards

### Filtering Logic (JavaScript)

```javascript
// Filter to relevant definitions for this entry type
let filteredDefs = definitions.filter(def => 
    def.entry_type_id_from === currentEntryTypeId || 
    def.entry_type_id_to === currentEntryTypeId
);

// Apply section-level filtering
if (sectionConfig.visibleRelTypes.length > 0) {
    filteredDefs = filteredDefs.filter(def => 
        sectionConfig.visibleRelTypes.includes(def.id)
    );
} else if (sectionConfig.hiddenRelTypes.length > 0) {
    filteredDefs = filteredDefs.filter(def => 
        !sectionConfig.hiddenRelTypes.includes(def.id)
    );
}
```

### Ordering Logic (JavaScript)

```javascript
// Sort definitions by custom order
const sortedDefinitions = [...relationshipDefinitions].sort((a, b) => {
    const orderA = customGridOrder[a.id] !== undefined ? customGridOrder[a.id] : 999;
    const orderB = customGridOrder[b.id] !== undefined ? customGridOrder[b.id] : 999;
    return orderA - orderB;
});
```

---

## Configuration Examples

### Example 1: Show Only Organizational Relationships

```json
{
  "visible_relationship_types": [1, 2],
  "hidden_relationship_types": []
}
```

### Example 2: Hide Specific Types

```json
{
  "visible_relationship_types": [],
  "hidden_relationship_types": [3, 4]
}
```

### Example 3: Default (Show All)

```json
{
  "visible_relationship_types": [],
  "hidden_relationship_types": []
}
```

---

## Database Schema

### EntryLayoutSection

The `config` field (TEXT/JSON) now supports:

```sql
config = json({
    'visible_relationship_types': [1, 2, 3],  -- Optional: Show only these
    'hidden_relationship_types': [4, 5],      -- Optional: Hide these
    'show_add_button': true,                  -- Existing
    'group_by_type': true                     -- Existing
})
```

### RelationshipGridOrder

Stores custom ordering per entry type:

```sql
CREATE TABLE RelationshipGridOrder (
    id INTEGER PRIMARY KEY,
    entry_type_id INTEGER NOT NULL,
    relationship_definition_id INTEGER NOT NULL,
    display_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(entry_type_id, relationship_definition_id)
);
```

---

## API Endpoints Used

### Get Relationship Definitions
```
GET /api/relationship_definitions
```
Returns all relationship definitions

### Get Entry Relationships
```
GET /api/entries/{id}/relationships
```
Returns relationships for a specific entry

### Get Grid Order
```
GET /api/entry_types/{id}/relationship_grid_order
```
Returns custom ordering for an entry type

### Save Grid Order
```
POST /api/entry_types/{id}/relationship_grid_order
Body: { "order": [{"definition_id": 1, "order": 0}, ...] }
```
Saves custom ordering for an entry type

---

## Testing Checklist

- [x] ✅ Single section with all relationship types
- [x] ✅ Single section with visible_relationship_types filter
- [x] ✅ Single section with hidden_relationship_types filter
- [x] ✅ Multiple sections with different filters
- [x] ✅ Grid ordering (drag and drop)
- [x] ✅ Grid ordering persists after page reload
- [x] ✅ Grid ordering applies to all entries of same type
- [x] ✅ Empty card hiding
- [ ] ⏳ Add relationship functionality
- [ ] ⏳ Delete relationship functionality
- [ ] ⏳ Edit relationship quantity/unit

---

## Known Issues

None currently identified.

---

## Next Steps

### 1. Entry Layout Builder UI

Add UI to configure visible/hidden relationship types:
- [ ] Fetch available relationship definitions for entry type
- [ ] Display checkboxes in section properties panel
- [ ] Add "Show Only" vs "Hide" mode toggle
- [ ] Save configuration to section.config
- [ ] Live preview of which types will be displayed

### 2. Complete CRUD Operations

Implement the placeholder functions:
- [ ] `openAddRelationshipModal()` - Full modal implementation
- [ ] `deleteRelationship()` - With confirmation and refresh
- [ ] Edit quantity/unit inline

### 3. Hierarchy View

Extend filtering to hierarchy view tab:
- [ ] Filter tree nodes by section configuration
- [ ] Maintain full tree structure with filtered nodes

---

## Benefits

✅ **Focused Views** - Display only relevant relationships  
✅ **Better Organization** - Group related types together  
✅ **Cleaner UI** - Reduce clutter  
✅ **Multiple Perspectives** - Different views of same data  
✅ **Custom Ordering** - Arrange by importance  
✅ **Entry Type Consistency** - Same order for all entries  
✅ **Backward Compatible** - Default shows all types  

---

## References

- [RELATIONSHIP_SECTION_CONFIGURATION.md](./RELATIONSHIP_SECTION_CONFIGURATION.md) - Full technical docs
- [RELATIONSHIP_SECTION_CONFIG_QUICKSTART.md](./RELATIONSHIP_SECTION_CONFIG_QUICKSTART.md) - Quick start guide
- [RELATIONSHIP_GRID_ORDERING.md](./RELATIONSHIP_GRID_ORDERING.md) - Original ordering feature
- [RELATIONSHIP_GRID_EMPTY_CARDS_HIDE.md](./RELATIONSHIP_GRID_EMPTY_CARDS_HIDE.md) - Empty card hiding

---

## Version History

- **v1.0** (2025-11-08): Initial implementation
  - Section-level configuration support
  - Filtering by visible/hidden types
  - Restored grid ordering functionality
  - Drag and drop reordering
  - Auto-save on reorder
