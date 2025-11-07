# Tab Assignment Fix - November 8, 2025

## Issue
When adding a section from the palette in the Layout Builder, the section was not being assigned to the currently active tab. All sections were defaulting to the 'main' tab regardless of which tab the user was viewing.

## Root Cause
Two issues were identified:

1. **Frontend:** The `addSectionFromPalette()` function in `entry_layout_builder.js` was not passing the `tab_id` when creating a new section via the API.

2. **Backend:** The `add_section()` method in `entry_layout_service.py` was not including `tab_id` and `tab_order` columns in the INSERT statement.

## Solution

### Changes Made

#### 1. Frontend (`app/static/js/entry_layout_builder.js`)

**Added tab_id to section creation:**
```javascript
body: JSON.stringify({
    section_type: sectionType,
    title: sectionTemplate.default_title,
    width: sectionTemplate.default_width,
    height: sectionTemplate.default_height,
    is_collapsible: sectionTemplate.is_collapsible,
    config: sectionTemplate.default_config,
    tab_id: activeTab,  // NEW: Add to currently active tab
    tab_order: 999      // NEW: Add at the end
})
```

**Improved notification message:**
```javascript
const currentTabObj = currentTabs.find(t => t.tab_id === activeTab);
const tabLabel = currentTabObj ? currentTabObj.tab_label : activeTab;
showNotification(`Section "${sectionTemplate.default_title}" added to ${tabLabel} tab`, 'success');
```

**Added safety check for active tab:**
```javascript
// Ensure active tab still exists, otherwise default to 'main'
const tabExists = currentTabs.some(t => t.tab_id === activeTab);
if (!tabExists && currentTabs.length > 0) {
    activeTab = currentTabs[0].tab_id || 'main';
}
```

#### 2. Backend (`app/services/entry_layout_service.py`)

**Updated INSERT statement:**
```python
cursor.execute("""
    INSERT INTO EntryLayoutSection (
        layout_id, section_type, title, position_x, position_y,
        width, height, is_visible, is_collapsible, default_collapsed,
        config, display_order, tab_id, tab_order  # NEW: Added tab_id and tab_order
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
    layout_id,
    section_data['section_type'],
    section_data.get('title', ''),
    section_data.get('position_x', 0),
    section_data.get('position_y', 0),
    section_data.get('width', 12),
    section_data.get('height', 2),
    section_data.get('is_visible', 1),
    section_data.get('is_collapsible', 1),
    section_data.get('default_collapsed', 0),
    json.dumps(section_data.get('config', {})),
    section_data.get('display_order', 0),
    section_data.get('tab_id', 'main'),  # NEW: Default to 'main' tab
    section_data.get('tab_order', 0)     # NEW: Tab order
))
```

## Testing

### How to Test

1. **Open Layout Builder:**
   - Navigate to Manage Entry Types
   - Click "Configure Layout" for any entry type

2. **Create a New Tab:**
   - Enable Edit Mode
   - Click "+ New Tab"
   - Name it (e.g., "Test Tab")

3. **Switch to New Tab:**
   - Click on the newly created tab

4. **Add a Section:**
   - Click any section from the palette (e.g., "Notes")
   - Section should appear in the grid
   - Notification should say: "Section 'Notes' added to Test Tab tab"

5. **Verify:**
   - Switch to "Overview" tab - the section should NOT appear there
   - Switch back to "Test Tab" - the section SHOULD appear there
   - Save layout and refresh - section should remain on the correct tab

### Expected Behavior

✅ **Before Fix:**
- Sections always added to 'main' tab
- Had to manually reassign via properties panel

✅ **After Fix:**
- Sections added to currently active tab
- Notification shows which tab the section was added to
- Can immediately see the section in the grid
- Active tab preserved after reload

## Files Modified

1. `app/static/js/entry_layout_builder.js`
   - Added `tab_id` and `tab_order` to section creation
   - Improved notification message
   - Added active tab validation

2. `app/services/entry_layout_service.py`
   - Updated `add_section()` to include `tab_id` and `tab_order`

## Impact

- **Improved UX:** Users can now add sections directly to the tab they're viewing
- **Less Friction:** No need to manually reassign sections after adding them
- **Better Feedback:** Clear notification showing which tab the section was added to
- **Backward Compatible:** Sections without tab_id still default to 'main'

## Deployment

Changes deployed via Docker rebuild:
```bash
docker compose up --build -d
```

No database migration required (tab columns already exist from previous migration).

---

**Status:** ✅ Fixed and Deployed
**Priority:** High (UX Issue)
**Complexity:** Low
**Testing:** Manual testing recommended
