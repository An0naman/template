# Testing Guide: Relationships Section V2

## 🚀 Quick Start

### 1. Prerequisites
- Database with entries and relationships
- Entry types configured
- Relationship definitions created

### 2. Access the V2 Page
Navigate to any entry using the V2 route:
```
http://localhost:5000/entry/<entry_id>/v2
```

For example:
```
http://localhost:5000/entry/1/v2
```

---

## 🧪 Test Scenarios

### Test 1: Basic Display
**Goal:** Verify section renders correctly

1. Open entry with relationships
2. Scroll to "Related Records" section
3. ✅ Check: Section header shows with count badge
4. ✅ Check: Tabs show with counts (Outgoing, Incoming, Hierarchy)
5. ✅ Check: Default tab (Outgoing) is active

### Test 2: Outgoing Relationships
**Goal:** Test outgoing relationships tab

1. Click "Outgoing" tab (should be active by default)
2. ✅ Check: Relationships are grouped by type
3. ✅ Check: Each group shows:
   - Group title with icon
   - Count badge
   - List of relationships
4. ✅ Check: Each relationship card shows:
   - Entry type badge with color
   - Relationship type with arrow icon
   - Entry title as clickable link
   - Status badge
   - Quantity/unit (if applicable)
   - Delete button

**Actions:**
- Click entry title → Opens in new tab
- Hover over card → Shadow effect
- Click delete → Confirmation dialog appears

### Test 3: Incoming Relationships
**Goal:** Test incoming relationships tab

1. Click "Incoming" tab
2. ✅ Check: Tab activates and content loads
3. ✅ Check: Shows relationships where current entry is the target
4. ✅ Check: Uses appropriate relationship labels (label_to_side)
5. ✅ Check: Arrow icons show left direction (←)
6. ✅ Check: Grouped by type like outgoing

**Edge Case:**
- Entry with no incoming relationships → Shows empty state

### Test 4: Hierarchy View
**Goal:** Test tree hierarchy display

1. Click "Hierarchy" tab
2. ✅ Check: Loading spinner appears
3. ✅ Check: AJAX call to `/api/entries/<id>/relationships/hierarchy`
4. ✅ Check: Tree structure renders
5. ✅ Check: Current entry has "Current" badge
6. ✅ Check: Parent entries have "Parent" badge
7. ✅ Check: Indentation increases with depth
8. ✅ Check: Toggle buttons appear for nodes with children

**Actions:**
- Click toggle button → Children collapse/expand
- Click entry title → Opens in new tab
- Icons show entry type with color

**Edge Cases:**
- Entry with no hierarchy → Shows empty state
- Deep hierarchy (3+ levels) → Limited to max depth
- Circular relationships → Prevented by visited set

### Test 5: Empty States
**Goal:** Test empty state displays

1. Find/create entry with NO relationships
2. Open in V2
3. ✅ Check: Empty state shows:
   - Icon
   - "No Relationships Yet" heading
   - Helpful message
   - "Add First Relationship" button

### Test 6: Add Relationship Modal
**Goal:** Test modal functionality

1. Click "Add Relationship" button
2. ✅ Check: Modal opens
3. ✅ Check: Shows current entry name
4. ✅ Check: Relationship definition dropdown loads
5. ✅ Check: Related entry dropdown available
6. ✅ Check: "Create new entry" checkbox works

**Actions:**
- Select relationship type → Entry selector updates
- Check "Create new entry" → Shows new entry fields
- Select definition with quantity → Shows quantity/unit fields
- Click "Add Relationship" → Submits and reloads page

### Test 7: Delete Relationship
**Goal:** Test delete functionality

1. Click delete button (trash icon) on any relationship
2. ✅ Check: Confirmation dialog appears
3. ✅ Check: Shows entry title in confirmation
4. Click "OK"
5. ✅ Check: Card fades out with animation
6. ✅ Check: Page reloads after 1 second
7. ✅ Check: Relationship is removed
8. ✅ Check: Counts update on tabs

### Test 8: Responsive Design
**Goal:** Test mobile layout

1. Open browser dev tools (F12)
2. Toggle device toolbar (Ctrl+Shift+M)
3. Select mobile device or resize to < 768px width
4. ✅ Check: Section header stacks vertically
5. ✅ Check: Tabs remain horizontal but compressed
6. ✅ Check: Cards stack vertically
7. ✅ Check: Tree indentation reduces
8. ✅ Check: All buttons remain accessible

### Test 9: Dark Mode
**Goal:** Test theme support

1. Toggle dark mode in settings
2. ✅ Check: Section background adapts
3. ✅ Check: Text colors remain readable
4. ✅ Check: Borders use theme colors
5. ✅ Check: Cards have proper contrast
6. ✅ Check: Hover states work
7. ✅ Check: Badges remain visible

### Test 10: Performance
**Goal:** Test with large datasets

1. Create entry with 20+ relationships
2. Open in V2
3. ✅ Check: Page loads within 2 seconds
4. ✅ Check: Scrolling is smooth
5. ✅ Check: Tab switching is instant
6. ✅ Check: Hierarchy loads within 1 second
7. ✅ Check: No console errors

---

## 🔍 Console Checks

Open browser console (F12) and verify:

### On Page Load
```javascript
"Initializing relationships section for entry: 123"
```

### On Hierarchy Tab Click
```javascript
"Loading hierarchy for entry: 123"
// Followed by AJAX call to /api/entries/123/relationships/hierarchy
```

### On Delete
```javascript
"Deleting relationship: 456"
"Relationship deleted successfully"
```

### Check for Errors
No errors should appear. If you see:
- `TypeError` → Check JavaScript syntax
- `404` → Check API endpoint routes
- `500` → Check backend logic/database

---

## 🐛 Common Issues & Fixes

### Issue: Section Doesn't Appear
**Cause:** Section not visible in layout  
**Fix:** Go to Entry Layout Builder and enable "relationships" section

### Issue: Empty State Shows But Relationships Exist
**Cause:** Data not passed to template  
**Fix:** Check `relationships` dict in route handler, verify database has data

### Issue: Hierarchy Shows "Loading..." Forever
**Cause:** API endpoint failing  
**Fix:** 
1. Check `/api/entries/<id>/relationships/hierarchy` returns data
2. Check console for JavaScript errors
3. Verify `relationships-section.js` is loaded

### Issue: Cards Don't Display Correctly
**Cause:** CSS not loaded  
**Fix:** Verify `css/sections/relationships.css` is linked in `<head>`

### Issue: Delete Doesn't Work
**Cause:** JavaScript not initialized  
**Fix:** Check `initializeRelationshipsSection()` is called on page load

### Issue: Modal Doesn't Open
**Cause:** Modal HTML not included  
**Fix:** Verify `{% include 'modals/_add_relationship_modal.html' %}` in template

### Issue: Styling Looks Wrong
**Cause:** CSS variables not defined  
**Fix:** Ensure theme CSS is loaded with `{{ theme_css|safe }}`

---

## 📊 Database Verification

### Check Relationships Exist
```sql
SELECT * FROM EntryRelationship WHERE source_entry_id = 1;
SELECT * FROM EntryRelationship WHERE target_entry_id = 1;
```

### Check Relationship Definitions
```sql
SELECT * FROM RelationshipDefinition WHERE is_active = 1;
```

### Check Entry Types
```sql
SELECT id, name, singular_label, icon, color FROM EntryType;
```

---

## ✅ Success Criteria

Implementation is successful when:

- ✅ All three tabs (Outgoing, Incoming, Hierarchy) work
- ✅ Relationships display correctly with all metadata
- ✅ Grouping by type functions properly
- ✅ Tree view renders with correct indentation
- ✅ Add relationship modal opens and submits
- ✅ Delete relationship works with confirmation
- ✅ Empty states show helpful messages
- ✅ Mobile responsive layout works
- ✅ Dark mode styling is correct
- ✅ No console errors
- ✅ Page loads in < 2 seconds
- ✅ All links open in new tabs
- ✅ Counts on tabs are accurate

---

## 📸 Visual Checklist

Take screenshots of:
1. ✅ Outgoing tab with grouped relationships
2. ✅ Incoming tab with relationships
3. ✅ Hierarchy tab with tree structure
4. ✅ Empty state
5. ✅ Add relationship modal
6. ✅ Delete confirmation dialog
7. ✅ Mobile view
8. ✅ Dark mode

---

## 🎯 Quick Test Command

If using a test database, you can quickly verify with:

```bash
# Start the server
python run.py

# Open in browser
xdg-open http://localhost:5000/entry/1/v2

# Check browser console (F12)
# No errors should appear
```

---

## 📞 Troubleshooting Steps

1. **Check Server Logs**
   ```bash
   # Look for errors in terminal where Flask is running
   # Should see: "GET /entry/1/v2 200"
   ```

2. **Check Network Tab**
   - Open Dev Tools → Network
   - Look for API calls to `/api/entries/.../relationships/...`
   - Verify they return 200 status codes

3. **Check Elements Tab**
   - Verify `.relationships-section` exists in DOM
   - Check if CSS classes are applied correctly
   - Look for inline styles on cards

4. **Check Console Tab**
   - No red error messages
   - Initialization message should appear
   - AJAX responses should be logged

5. **Check Application Tab**
   - Verify no localStorage errors
   - Check if session is active

---

## 🎓 Test Data Setup

If you need to create test data:

```python
# In Python console or test script
from app import create_app, get_db

app = create_app()
with app.app_context():
    conn = get_db()
    cursor = conn.cursor()
    
    # Create test relationships
    cursor.execute("""
        INSERT INTO EntryRelationship 
        (source_entry_id, target_entry_id, relationship_type, quantity, unit)
        VALUES (1, 2, 1, 5, 'units')
    """)
    
    conn.commit()
```

---

**Happy Testing!** 🎉

Report any issues or unexpected behavior for further refinement.
