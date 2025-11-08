# Relationship Sections - Complete Multi-Section Implementation

## Date
November 8, 2025

## Summary
Completed full implementation of multiple relationship sections with independent filtering, section-specific preferences, and manual hide/show functionality. This enables entries to have multiple relationship sections, each showing different relationship types with their own filters and configurations.

---

## Issues Resolved

### 1. **Filter Scoping Issue** (RELATIONSHIP_FILTER_SCOPE_FIX.md)
**Problem:** When multiple relationship sections existed on the same page, filters from one section would interfere with filters in other sections.

**Solution:** Changed all DOM query operations to be scoped to the specific section's container using `getElementById('groupedViewContainer' + sectionUniqueId)` instead of global `document.querySelector()`.

### 2. **Duplicate Element IDs** (RELATIONSHIP_MULTIPLE_SECTIONS_UNIQUE_ID_FIX.md)
**Problem:** Multiple relationship sections on the same entry had identical HTML element IDs, causing JavaScript to always target the first section.

**Solution:** Created unique section identifiers by combining entry ID and section ID (`section_unique_id = entry.id ~ '_' ~ section_id`), ensuring each section has unique DOM element IDs.

### 3. **Missing Filters in Additional Sections**
**Problem:** State/status filter dropdowns were not appearing in relationship sections.

**Solution:** Added complete filter functionality to `_relationships_section_configurable.html` template, including:
- Multi-select state filter dropdown
- Filter save/load functionality
- State loading per relationship definition
- CSS styling for multi-select dropdowns

### 4. **Global Filter Preferences**
**Problem:** Filter preferences were saved globally per relationship definition, causing all sections showing the same relationship type to share the same filter.

**Solution:** Updated the filter preference API to include `section_id`, storing preferences with keys like `"section_id:definition_id"` for section-specific preferences.

### 5. **No Ability to Hide Relationship Types**
**Problem:** Users couldn't hide specific relationship types within a section without removing them from the configuration.

**Solution:** Implemented hide/show functionality using localStorage with:
- Hide button on each relationship card
- "Show Hidden" toggle button
- Unhide button on hidden cards when viewing
- Section-specific hidden card storage

---

## Files Modified

### Backend

#### 1. `app/api/relationships_api.py`
**GET /api/relationship_filter_preferences**
- Added `section_id` query parameter for filtering preferences
- Updated to return section-specific preferences with format `"section_id:def_id"`
- Maintains backward compatibility with global preferences

**POST /api/relationship_filter_preferences**
- Added `section_id` to request payload
- Stores preferences with section-specific keys when `section_id` is provided
- Falls back to global keys for backward compatibility

### Frontend

#### 2. `app/templates/entry_detail_v2.html`
**Changes:**
- Updated relationship section include to pass `section_id`:
  ```jinja2
  {% with section_id=section.id %}{% include 'sections/_relationships_section_v2.html' %}{% endwith %}
  ```

#### 3. `app/templates/sections/_relationships_section_v2.html`
**Major Changes:**
- Added `section_unique_id` variable combining entry ID and section ID
- Updated all element IDs to use `section_unique_id`
- Updated JavaScript to use `sectionUniqueId` constant
- Updated all `getElementById()` calls for proper scoping
- Updated filter save/load to include `section_id`

**Key Functions Updated:**
- `loadRelationships()` - Uses unique section ID
- `renderRelationshipCards()` - Scoped to section container
- `applyFilters()` - Scoped to section container
- `loadStatesForDefinition()` - Scoped to section container
- `saveFilterPreference()` - Includes section_id in payload
- `loadFilterPreferences()` - Filters by section_id
- `attachEventListeners()` - Scoped to section container
- All toggle functions - Use unique section IDs

#### 4. `app/templates/sections/_relationships_section_configurable.html`
**Major Additions:**

**Filter Functionality:**
- Added multi-select state filter dropdown to card headers
- Added save filter button
- Implemented `applyFilters()` function with multi-select support
- Implemented `loadStatesForDefinition()` for dynamic state loading
- Implemented `saveFilterPreference()` with section_id
- Implemented `loadFilterPreferences()` with section filtering
- Updated `attachEventListeners()` to handle filters

**Hide/Show Functionality:**
- Added hide button (`btn-hide-card`) to card headers
- Added "Show Hidden" toggle button in section header
- Implemented `hideCard()` - Hides card and stores in localStorage
- Implemented `unhideCard()` - Unhides card and removes from storage
- Implemented `toggleHiddenCards()` - Shows/hides all hidden cards temporarily
- Implemented `addUnhideButton()` - Adds unhide button to visible hidden cards
- Implemented `removeUnhideButton()` - Removes unhide button
- Implemented `updateHiddenCardsToggle()` - Shows/hides toggle button
- Implemented `applyHiddenCardsOnLoad()` - Applies hidden state on page load

**CSS Additions:**
```css
/* Multi-select dropdown styling */
.relationship-state-filter[multiple] {
    background-image: url("data:image/svg+xml...");
    background-repeat: no-repeat;
    background-position: right 0.75rem center;
    background-size: 16px 12px;
    padding-right: 2.25rem;
    overflow-y: auto;
}

.relationship-state-filter[multiple]:focus {
    height: auto !important;
    max-height: 400px;
    min-height: 31px;
}

.relationship-type-card .card-header {
    position: relative;
    z-index: 10;
}
```

**Row Rendering:**
- Updated `renderRelationshipRow()` to include status data attributes:
  - `data-status-category` - "active" or "inactive"
  - `data-status` - Lowercase status name

---

## Technical Implementation

### Section-Specific Identifiers

**Jinja2 Template:**
```jinja2
{% set section_unique_id = entry.id ~ '_' ~ (section_id|default('default')) %}
```

**JavaScript:**
```javascript
const entryId = {{ entry.id }};
const sectionId = '{{ section_id|default("default") }}';
const sectionUniqueId = '{{ section_unique_id }}';
```

### Filter Preferences Storage

**Format:**
```json
{
  "45:123": {                    // Section 45, Definition 123
    "status_category": "",
    "specific_state": "active,available"
  },
  "52:123": {                    // Section 52, Definition 123
    "status_category": "",
    "specific_state": "inactive,completed"
  },
  "123": {                       // Global preference (backward compat)
    "status_category": "",
    "specific_state": "active"
  }
}
```

### Hidden Cards Storage (localStorage)

**Key Format:** `hiddenCards_{sectionUniqueId}`

**Value Format:**
```json
[123, 456, 789]  // Array of hidden definition IDs
```

### API Endpoints

**GET /api/relationship_filter_preferences**
```
Query Parameters:
  - section_id (optional): Filter preferences by section

Response:
[
  {
    "relationship_definition_id": 123,
    "section_id": "45",
    "status_category": "",
    "specific_state": "active,available"
  }
]
```

**POST /api/relationship_filter_preferences**
```
Request Body:
{
  "relationship_definition_id": 123,
  "section_id": "45",
  "status_category": "",
  "specific_state": "active,available"
}

Response:
{
  "success": true
}
```

---

## Features

### 1. ✅ Multiple Sections Per Entry
- Each entry can have unlimited relationship sections
- Each section can be configured independently
- Sections have unique IDs and don't interfere with each other

### 2. ✅ Section-Specific Filters
- Each section has its own state/status filters
- Filters are saved per section, not globally
- Multi-select support for filtering by multiple states
- Visual feedback with dropdown arrow

### 3. ✅ Section-Specific Filter Preferences
- Filter preferences saved to database with section ID
- Each section loads only its own preferences
- Preferences persist across sessions
- API returns only relevant preferences per section

### 4. ✅ Hide/Show Relationship Types
- Users can hide specific relationship types within a section
- Hidden cards stored in localStorage per section
- "Show Hidden" button appears when cards are hidden
- Unhide button on cards when viewing hidden ones
- Hide state persists across page reloads
- Independent per section (same relationship type can be hidden in one section, visible in another)

### 5. ✅ Proper DOM Scoping
- All DOM queries scoped to section container
- Event listeners only attach to elements within their section
- No cross-section interference
- Valid HTML with no duplicate IDs

### 6. ✅ Backward Compatibility
- Global preferences still work (section_id = null)
- Old sections without section_id still function
- API handles both old and new preference formats

---

## User Experience

### Filter Workflow
1. User opens entry with multiple relationship sections
2. Each section loads with independent filters
3. User selects filter criteria (Ctrl+Click for multiple)
4. Filter applies only to that section
5. User clicks save button to persist preference
6. Preference saved with section ID
7. On next visit, filter automatically restored for that section

### Hide/Show Workflow
1. User clicks hide button (eye-slash icon) on relationship card
2. Card immediately hidden
3. "Show Hidden" button appears in section header
4. User clicks "Show Hidden" to temporarily view hidden cards
5. Hidden cards appear with green "Unhide" button
6. User clicks "Unhide" to permanently restore card
7. Card becomes visible again, hide state removed

---

## Testing Checklist

- [x] ✅ Multiple sections on same entry load correctly
- [x] ✅ Each section has unique element IDs
- [x] ✅ Filters appear in all sections
- [x] ✅ Filters work independently per section
- [x] ✅ Filter preferences save per section
- [x] ✅ Filter preferences load correctly per section
- [x] ✅ Same relationship type can have different filters in different sections
- [x] ✅ Hide button hides cards
- [x] ✅ "Show Hidden" button appears when cards are hidden
- [x] ✅ "Show Hidden" toggles visibility correctly
- [x] ✅ Unhide button restores cards permanently
- [x] ✅ Hidden state persists across page reloads
- [x] ✅ Hidden state is section-specific
- [x] ✅ No JavaScript errors in console
- [x] ✅ No duplicate ID warnings

---

## Known Limitations

1. **Hide functionality uses localStorage**
   - Hidden cards stored in browser localStorage, not database
   - Won't sync across devices/browsers
   - If localStorage is cleared, hidden cards become visible
   - This is by design for quick temporary hiding

2. **Filter preferences stored globally per user**
   - Preferences stored in user preferences table
   - All sections in JSON blob (could be moved to dedicated table if needed)

---

## Future Enhancements

### Potential Improvements
1. **Database-backed hide functionality**
   - Store hidden cards in database table
   - Sync across devices
   - User-specific and section-specific

2. **Section-specific relationship ordering**
   - Currently ordering is per entry type
   - Could be made section-specific

3. **Bulk hide/show operations**
   - Select multiple cards to hide at once
   - Hide all empty cards button
   - Show only favorites feature

4. **Filter templates**
   - Save named filter presets
   - Quick-apply common filter combinations
   - Share filters across sections

---

## Related Documentation
- [RELATIONSHIP_FILTER_SCOPE_FIX.md](./RELATIONSHIP_FILTER_SCOPE_FIX.md) - Filter scoping fix
- [RELATIONSHIP_MULTIPLE_SECTIONS_UNIQUE_ID_FIX.md](./RELATIONSHIP_MULTIPLE_SECTIONS_UNIQUE_ID_FIX.md) - Unique ID fix
- [RELATIONSHIP_SECTION_CONFIGURATION.md](./RELATIONSHIP_SECTION_CONFIGURATION.md) - Section configuration
- [RELATIONSHIP_STATE_FILTER_V2_UPDATE.md](./RELATIONSHIP_STATE_FILTER_V2_UPDATE.md) - Filter implementation
- [MULTIPLE_SECTIONS_SUPPORT.md](./MULTIPLE_SECTIONS_SUPPORT.md) - Multiple sections feature

---

## Version History
- **2025-11-08**: Complete implementation with all features
  - Filter scoping fix
  - Unique section IDs
  - Section-specific filter preferences
  - Hide/show functionality
  - Full multi-section support
