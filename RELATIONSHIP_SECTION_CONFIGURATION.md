# Relationship Grid Section-Level Configuration

## Summary

Implemented section-level configuration for relationship grids, allowing each relationships section instance to have its own show/hide logic for relationship types. This enables multiple relationship sections on the same entry type, each displaying different subsets of relationships.

## Date

November 8, 2025

---

## Features Implemented

### 1. ✅ Section-Level Visibility Configuration

Each relationships section can now be configured with:
- **`visible_relationship_types`**: Array of relationship definition IDs to show (whitelist)
- **`hidden_relationship_types`**: Array of relationship definition IDs to hide (blacklist)

**Logic:**
- If `visible_relationship_types` is set: Only show those types
- Else if `hidden_relationship_types` is set: Show all except those types
- Else: Show all relationship types (default behavior)

### 2. ✅ Restored Relationship Grid Ordering

The relationship grid ordering functionality (using `RelationshipGridOrder` table) now works correctly within each section instance. Cards are sorted by custom order when available.

### 3. ✅ Multiple Section Support

You can now have multiple relationships sections on the same entry type, each configured to show different relationship types:
- **Section 1**: Show only "Parent Organization" and "Child Organizations"
- **Section 2**: Show only "Team Members" and "Projects"
- **Section 3**: Show all relationships

---

## Files Created/Modified

### Created Files

1. **`app/templates/sections/_relationships_section_configurable.html`**
   - New template that supports section-level configuration
   - Filters relationship definitions based on section config
   - Maintains all existing features (grouping, ordering, empty card hiding, etc.)
   - Self-contained with inline JavaScript for better encapsulation

### Modified Files

2. **`app/templates/entry_detail_v2.html`**
   - Updated to pass `section_config` to the relationships section template
   - Changed to use `_relationships_section_configurable.html` instead of `_relationships_section.html`

3. **`app/templates/sections/_relationships_section.html`**
   - Added support for receiving and parsing `section_config`
   - Added data attributes for visible/hidden relationship types
   - Updated JavaScript initialization to pass configuration

---

## Configuration Structure

### In Database (EntryLayoutSection.config)

```json
{
  "visible_relationship_types": [1, 3, 5],
  "hidden_relationship_types": [],
  "show_add_button": true,
  "group_by_type": true
}
```

Or:

```json
{
  "visible_relationship_types": [],
  "hidden_relationship_types": [2, 4],
  "show_add_button": true,
  "group_by_type": true
}
```

### Example Use Cases

#### Use Case 1: Organizational Relationships Section
```json
{
  "visible_relationship_types": [1, 2],
  "hidden_relationship_types": []
}
```
Shows only "Parent Organization" (ID 1) and "Child Organizations" (ID 2)

#### Use Case 2: People & Projects Section
```json
{
  "visible_relationship_types": [5, 6, 7],
  "hidden_relationship_types": []
}
```
Shows only "Team Members" (ID 5), "Project Manager" (ID 6), and "Projects" (ID 7)

#### Use Case 3: Hide Specific Types
```json
{
  "visible_relationship_types": [],
  "hidden_relationship_types": [3, 4]
}
```
Shows all relationship types except "Supplier" (ID 3) and "Customer" (ID 4)

---

## Technical Implementation

### Template Logic

```jinja2
{# Parse configuration #}
{% set config = section_config|default({}) %}
{% set visible_rel_types = config.get('visible_relationship_types', [])|list %}
{% set hidden_rel_types = config.get('hidden_relationship_types', [])|list %}
```

### JavaScript Filtering

```javascript
// Filter to relevant definitions for this entry type
let filteredDefs = definitions.filter(def => 
    def.entry_type_id_from === currentEntryTypeId || 
    def.entry_type_id_to === currentEntryTypeId
);

// Apply section-level filtering
if (sectionConfig.visibleRelTypes.length > 0) {
    // If visible list is specified, only show those
    filteredDefs = filteredDefs.filter(def => 
        sectionConfig.visibleRelTypes.includes(def.id)
    );
} else if (sectionConfig.hiddenRelTypes.length > 0) {
    // If hidden list is specified, filter them out
    filteredDefs = filteredDefs.filter(def => 
        !sectionConfig.hiddenRelTypes.includes(def.id)
    );
}
```

### Grid Ordering Integration

```javascript
// Sort definitions by custom order if available
const sortedDefinitions = [...relationshipDefinitions].sort((a, b) => {
    const orderA = customGridOrder[a.id] !== undefined ? customGridOrder[a.id] : 999;
    const orderB = customGridOrder[b.id] !== undefined ? customGridOrder[b.id] : 999;
    return orderA - orderB;
});
```

---

## How to Configure (Manual)

### 1. Via Database

```sql
-- Update section config for a specific relationships section
UPDATE EntryLayoutSection 
SET config = json_set(
    config, 
    '$.visible_relationship_types', 
    json('[1, 2, 3]')
)
WHERE id = <section_id>;
```

### 2. Via Entry Layout Builder (Future Enhancement)

The Entry Layout Builder UI will be updated to include:
- Relationship type selector checkboxes
- "Show Only" vs "Hide" mode toggle
- Visual preview of which types will be displayed

---

## Testing

### Test Case 1: Single Section with All Types
1. Create entry with default relationships section
2. Verify all relationship types are visible
3. Verify ordering works correctly

### Test Case 2: Multiple Sections with Different Types
1. Create entry type with 2 relationships sections
2. Configure Section 1: `visible_relationship_types: [1, 2]`
3. Configure Section 2: `visible_relationship_types: [3, 4, 5]`
4. Verify each section shows only configured types

### Test Case 3: Hide Specific Types
1. Configure section: `hidden_relationship_types: [2, 4]`
2. Verify those types are not displayed
3. Verify all other types are displayed

---

## Benefits

✅ **Focused Relationship Views** - Display only relevant relationships in each section  
✅ **Better Organization** - Group related relationship types together  
✅ **Cleaner UI** - Reduce clutter by hiding unnecessary relationship types  
✅ **Multiple Perspectives** - Show same entry's relationships in different ways  
✅ **Maintained Ordering** - Custom grid order persists within filtered views  
✅ **Backward Compatible** - Sections without config show all types (existing behavior)  

---

## Next Steps (To Do)

### UI Enhancement Needed

The Entry Layout Builder needs to be updated to allow users to configure visible/hidden relationship types:

1. **Add Relationship Type Selector**
   - Fetch available relationship definitions for entry type
   - Display as checkboxes in section properties panel
   - Allow selection of visible/hidden types

2. **Add Mode Toggle**
   - Radio buttons: "Show Only Selected" vs "Hide Selected"
   - Determines whether to use `visible_relationship_types` or `hidden_relationship_types`

3. **Visual Preview**
   - Show which relationship types will be displayed based on current selection
   - Update preview when selection changes

### Implementation Sketch

```javascript
// In entry_layout_builder.js

function renderRelationshipSectionConfig(sectionData) {
    const config = sectionData.config || {};
    const visibleTypes = config.visible_relationship_types || [];
    const hiddenTypes = config.hidden_relationship_types || [];
    
    // Determine mode
    const mode = visibleTypes.length > 0 ? 'show' : 'hide';
    const selectedTypes = mode === 'show' ? visibleTypes : hiddenTypes;
    
    return `
        <div class="form-group">
            <label>Relationship Types Filter</label>
            <div class="btn-group mb-2" role="group">
                <input type="radio" class="btn-check" name="filterMode" id="filterModeShow" value="show" ${mode === 'show' ? 'checked' : ''}>
                <label class="btn btn-outline-primary" for="filterModeShow">Show Only Selected</label>
                
                <input type="radio" class="btn-check" name="filterMode" id="filterModeHide" value="hide" ${mode === 'hide' ? 'checked' : ''}>
                <label class="btn btn-outline-primary" for="filterModeHide">Hide Selected</label>
            </div>
            
            <div class="relationship-types-list">
                <!-- Will be populated with checkboxes for each relationship definition -->
            </div>
        </div>
    `;
}
```

---

## Known Issues

None currently identified.

---

## Version History

- **v1.0** (2025-11-08): Initial implementation
  - Section-level configuration support
  - Filtering by visible/hidden types
  - Restored grid ordering within sections

---

## References

- **Related Features:**
  - [RELATIONSHIP_GRID_ORDERING.md](./RELATIONSHIP_GRID_ORDERING.md) - Grid ordering feature
  - [RELATIONSHIP_GRID_EMPTY_CARDS_HIDE.md](./RELATIONSHIP_GRID_EMPTY_CARDS_HIDE.md) - Empty card hiding
  - [MULTIPLE_SECTIONS_SUPPORT.md](./MULTIPLE_SECTIONS_SUPPORT.md) - Multiple section instances

- **Database Tables:**
  - `EntryLayoutSection` - Stores section configurations
  - `RelationshipGridOrder` - Stores custom grid ordering
  - `RelationshipDefinition` - Defines relationship types

- **API Endpoints:**
  - `GET /api/relationship_definitions` - Get all relationship definitions
  - `GET /api/entries/{id}/relationships` - Get entry's relationships
  - `GET /api/entry_types/{id}/relationship_grid_order` - Get grid order
