# Relationship Section-Level Preferences Implementation

## Date
November 8, 2025

## Summary
Refactored relationship section preferences (filters and hidden cards) from **per-entry-instance** storage to **section-definition-level** storage. This means configuration applies to all entries of the same type, not individual entry instances.

---

## Problem Statement

### Previous Behavior (WRONG)
- **Filter Preferences:** Stored per user, per section **instance** (unique to each entry)
  - Example: Entry #123's "Suppliers" section had different filters than Entry #456's "Suppliers" section
- **Hidden Cards:** Stored in localStorage per section **instance**
  - Example: Hiding "Past Suppliers" in Entry #123 didn't hide it in Entry #456
- **Result:** Users had to configure the same settings repeatedly for every entry of the same type

### New Behavior (CORRECT)
- **Filter Preferences:** Stored per user, per **section definition** (entry_type + section from section_order)
  - Example: All "Product" entries share the same filter config for their "Suppliers" section
- **Hidden Cards:** Stored in database per **section definition**
  - Example: Hiding "Past Suppliers" in one Product entry hides it in ALL Product entries
- **Result:** Configure once, applies everywhere for that entry type

---

## Implementation Details

### Database Schema

#### New Table: `section_relationship_preferences`

```sql
CREATE TABLE section_relationship_preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_type_id INTEGER NOT NULL,
    section_id INTEGER NOT NULL,  -- References section_order.id
    relationship_definition_id INTEGER NOT NULL,
    is_hidden BOOLEAN DEFAULT 0,
    filter_status_category TEXT,
    filter_specific_states TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (entry_type_id) REFERENCES entry_types (id) ON DELETE CASCADE,
    FOREIGN KEY (section_id) REFERENCES section_order (id) ON DELETE CASCADE,
    FOREIGN KEY (relationship_definition_id) REFERENCES relationship_definitions (id) ON DELETE CASCADE,
    UNIQUE(entry_type_id, section_id, relationship_definition_id)
);

CREATE INDEX idx_section_rel_prefs_lookup 
ON section_relationship_preferences(entry_type_id, section_id);

CREATE INDEX idx_section_rel_prefs_relationship 
ON section_relationship_preferences(relationship_definition_id);
```

**Key Points:**
- `entry_type_id` + `section_id` + `relationship_definition_id` = Unique constraint
- `section_id` references `section_order.id` (the section **definition**, not instance)
- Cascading deletes ensure cleanup when entry types/sections are removed

---

### API Endpoints

#### GET `/api/section_relationship_preferences`

**Query Parameters:**
- `entry_type_id` (required): The entry type ID
- `section_id` (required): The section definition ID from `section_order`

**Response:**
```json
[
  {
    "relationship_definition_id": 123,
    "is_hidden": false,
    "filter_status_category": "",
    "filter_specific_states": "active,available"
  },
  {
    "relationship_definition_id": 456,
    "is_hidden": true,
    "filter_status_category": "",
    "filter_specific_states": ""
  }
]
```

#### POST `/api/section_relationship_preferences`

**Request Body:**
```json
{
  "entry_type_id": 5,
  "section_id": 45,
  "relationship_definition_id": 123,
  "is_hidden": false,
  "filter_status_category": "",
  "filter_specific_states": "active,available"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Preference saved successfully"
}
```

**Behavior:**
- Creates new preference if doesn't exist
- Updates existing preference (INSERT OR REPLACE logic)
- Only updates fields that are provided in request

#### DELETE `/api/section_relationship_preferences/<relationship_definition_id>`

**Query Parameters:**
- `entry_type_id` (required)
- `section_id` (required)

**Response:**
```json
{
  "success": true,
  "message": "Preference deleted successfully"
}
```

---

### Frontend Changes

#### Template Variables

**Both Templates Now Require:**
```jinja2
{% with section_id=section.id, section_config=section.config %}
  {% include 'sections/_relationships_section_configurable.html' %}
{% endwith %}
```

**JavaScript Constants:**
```javascript
const entryTypeId = {{ entry.entry_type_id }};
const sectionId = {{ section_id|default('null') }};  // Section definition ID
const sectionUniqueId = '{{ section_unique_id }}';   // For DOM IDs (entry_id + section_id)
```

**Key Distinction:**
- `sectionId`: Section **definition** ID (from `section_order`) - used for API calls
- `sectionUniqueId`: Unique DOM identifier (entry ID + section ID) - used for element IDs

#### Updated Functions

##### Filter Functions

**`saveFilterPreference(definitionId)`**
```javascript
async function saveFilterPreference(definitionId) {
    if (!sectionId) {
        console.error('Section ID is required for saving preferences');
        return;
    }
    
    const selectedValues = /* ... get from multiselect ... */;
    
    const preference = {
        entry_type_id: entryTypeId,
        section_id: sectionId,  // Section DEFINITION ID
        relationship_definition_id: parseInt(definitionId),
        filter_status_category: '',
        filter_specific_states: selectedValues
    };
    
    await fetch('/api/section_relationship_preferences', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(preference)
    });
    
    showNotification('Filter preference saved for all entries of this type', 'success');
}
```

**`loadFilterPreferences()`**
```javascript
async function loadFilterPreferences() {
    if (!sectionId) return;
    
    const response = await fetch(
        `/api/section_relationship_preferences?entry_type_id=${entryTypeId}&section_id=${sectionId}`
    );
    const preferences = await response.json();
    
    preferences.forEach(pref => {
        // Apply filter to UI
        const card = container.querySelector(`[data-definition-id="${pref.relationship_definition_id}"]`);
        if (card && pref.filter_specific_states) {
            // ... select the saved filter values ...
        }
        applyFilters(pref.relationship_definition_id);
    });
}
```

##### Hide/Show Functions

**`hideCard(definitionId)`**
```javascript
async function hideCard(definitionId) {
    if (!sectionId) return;
    
    const preference = {
        entry_type_id: entryTypeId,
        section_id: sectionId,
        relationship_definition_id: parseInt(definitionId),
        is_hidden: true
    };
    
    await fetch('/api/section_relationship_preferences', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(preference)
    });
    
    // Hide in UI
    const card = container.querySelector(`[data-definition-id="${definitionId}"]`);
    if (card) {
        card.classList.add('manually-hidden-card');
        card.style.display = 'none';
    }
    
    updateHiddenCardsToggle();
    showNotification('Relationship type hidden for all entries of this type', 'info');
}
```

**`unhideCard(definitionId)`**
```javascript
async function unhideCard(definitionId) {
    if (!sectionId) return;
    
    const preference = {
        entry_type_id: entryTypeId,
        section_id: sectionId,
        relationship_definition_id: parseInt(definitionId),
        is_hidden: false
    };
    
    await fetch('/api/section_relationship_preferences', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(preference)
    });
    
    // Show in UI
    const card = container.querySelector(`[data-definition-id="${definitionId}"]`);
    if (card) {
        card.classList.remove('manually-hidden-card');
        card.style.display = 'block';
        removeUnhideButton(card);
    }
    
    updateHiddenCardsToggle();
    showNotification('Relationship type unhidden for all entries of this type', 'success');
}
```

**`applyHiddenCardsOnLoad()`**
```javascript
async function applyHiddenCardsOnLoad() {
    if (!sectionId) return;
    
    const response = await fetch(
        `/api/section_relationship_preferences?entry_type_id=${entryTypeId}&section_id=${sectionId}`
    );
    const preferences = await response.json();
    
    preferences.forEach(pref => {
        if (pref.is_hidden) {
            const card = container.querySelector(`[data-definition-id="${pref.relationship_definition_id}"]`);
            if (card) {
                card.classList.add('manually-hidden-card');
                card.style.display = 'none';
            }
        }
    });
    
    updateHiddenCardsToggle();
}
```

---

## Files Modified

### Backend

1. **`migrations/add_section_relationship_preferences.py`** ✨ NEW
   - Creates `section_relationship_preferences` table
   - Creates indexes for performance

2. **`app/api/relationships_api.py`**
   - Added `api_get_section_relationship_preferences()` endpoint
   - Added `api_save_section_relationship_preferences()` endpoint
   - Added `api_delete_section_relationship_preference()` endpoint

### Frontend

3. **`app/templates/entry_detail_v2.html`**
   - Line 558: Added `section_config` to fallback template include
   - Both tabbed and fallback modes now pass `section_id` and `section_config`

4. **`app/templates/sections/_relationships_section_configurable.html`**
   - Added `entryTypeId` and `sectionId` constants
   - Updated `saveFilterPreference()` to use new API
   - Updated `loadFilterPreferences()` to use new API
   - Updated `hideCard()` to use SQL instead of localStorage
   - Updated `unhideCard()` to use SQL instead of localStorage
   - Updated `applyHiddenCardsOnLoad()` to load from SQL
   - Removed all localStorage references

5. **`app/templates/sections/_relationships_section_v2.html`**
   - Added `entryTypeId` and `sectionId` constants
   - Updated `saveFilterPreference()` to use new API
   - Updated `loadFilterPreferences()` to use new API
   - (Note: v2 template may not have had hide/show functionality originally)

---

## Migration Path

### For Existing Installations

**Old Data:**
- Filter preferences in `user_preferences` table with keys like `"section_id:def_id"`
- Hidden cards in browser localStorage (per device)

**New System:**
- Preferences in `section_relationship_preferences` table
- Old data **not automatically migrated** (fresh start)

**User Impact:**
- Users will need to re-configure filters and hidden cards
- But configuration will now apply to all entries of that type
- One-time inconvenience for long-term benefit

**If Migration Is Needed:**
```sql
-- Example migration from old to new (would need custom logic)
INSERT INTO section_relationship_preferences 
(entry_type_id, section_id, relationship_definition_id, filter_specific_states)
SELECT 
    et.id as entry_type_id,
    so.id as section_id,
    -- Parse from old user_preferences.preferences JSON
FROM user_preferences up
JOIN section_order so ON ...
WHERE up.pref_key LIKE 'relationship_filter_preferences';
```

---

## Testing Checklist

- [x] ✅ Migration creates table successfully
- [x] ✅ Indexes created correctly
- [ ] ⏳ Save filter preference API works
- [ ] ⏳ Load filter preferences API works
- [ ] ⏳ Filter preferences apply to all entries of same type
- [ ] ⏳ Hide card API works
- [ ] ⏳ Unhide card API works
- [ ] ⏳ Hidden state applies to all entries of same type
- [ ] ⏳ Hidden state persists across sessions
- [ ] ⏳ "Show Hidden" toggle works correctly
- [ ] ⏳ No JavaScript errors in browser console
- [ ] ⏳ Both tabbed and non-tabbed layouts work
- [ ] ⏳ Multiple sections on same entry work independently

---

## Key Benefits

### Before
❌ Configure filters separately for each entry  
❌ Hidden cards stored in localStorage (per browser)  
❌ Settings don't sync across devices  
❌ Tedious to maintain consistency  

### After
✅ Configure once per entry type  
✅ Settings stored in database  
✅ Settings sync across all devices  
✅ Consistent experience across all entries of same type  

---

## User Workflow Example

### Scenario: Product Entry Type with "Suppliers" Section

**Step 1:** User opens Product #123
- Sees "Suppliers" relationship section
- Has relationship types: "Current Suppliers", "Past Suppliers", "Potential Suppliers"

**Step 2:** User configures section
- Hides "Past Suppliers" (clicks hide button)
- Filters "Current Suppliers" to show only "Active" status
- Clicks "Save Filter" button

**Step 3:** User opens Product #456
- "Past Suppliers" is already hidden
- "Current Suppliers" already filtered to "Active"
- No configuration needed!

**Step 4:** User opens Product #789 on different computer
- Same configuration automatically applied
- Works because it's stored in database, not localStorage

---

## Future Enhancements

### Potential Improvements

1. **User-specific vs Team-wide Preferences**
   - Currently per-user
   - Could add flag for team-wide defaults

2. **Preference Templates/Presets**
   - Save named configuration sets
   - Quick-apply common patterns

3. **Bulk Configuration UI**
   - Configure all sections for an entry type at once
   - Import/export configurations

4. **Audit Log**
   - Track who changed what preference when
   - Helpful for team collaboration

---

## Troubleshooting

### "Section ID not available" Console Warning
**Cause:** `section_id` not passed to template  
**Fix:** Ensure `entry_detail_v2.html` passes `section_id` in `{% with %}` block

### Preferences Not Saving
**Cause:** Missing `entry_type_id` or `section_id`  
**Check:**
- Browser console for JavaScript errors
- Backend logs for API errors
- Verify migration ran successfully

### Preferences Not Loading
**Cause:** Wrong section_id being used  
**Check:**
- JavaScript console shows correct `entryTypeId` and `sectionId`
- API response contains expected preferences
- Filter/hidden state applied in `loadFilterPreferences()` / `applyHiddenCardsOnLoad()`

### Changes Not Applying to Other Entries
**Cause:** Using wrong API endpoint or section ID  
**Verify:**
- Using `/api/section_relationship_preferences` (new) not `/api/relationship_filter_preferences` (old)
- `sectionId` is section **definition** ID, not instance ID

---

## Related Documentation
- [RELATIONSHIP_SECTIONS_COMPLETE_IMPLEMENTATION.md](./RELATIONSHIP_SECTIONS_COMPLETE_IMPLEMENTATION.md) - Previous multi-section work
- [RELATIONSHIP_FILTER_SCOPE_FIX.md](./RELATIONSHIP_FILTER_SCOPE_FIX.md) - Filter scoping fix
- [RELATIONSHIP_MULTIPLE_SECTIONS_UNIQUE_ID_FIX.md](./RELATIONSHIP_MULTIPLE_SECTIONS_UNIQUE_ID_FIX.md) - Unique ID implementation

---

## Version History
- **2025-11-08**: Initial implementation
  - Database migration
  - API endpoints
  - Frontend refactoring
  - localStorage → SQL migration
