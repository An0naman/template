# 🧪 Testing Guide: Hierarchy Tab Feature

## Quick Test Checklist

### ✅ Basic Functionality

1. **Navigate to Entry Detail V2**
   - Go to any entry: `/entry/<id>/v2`
   - Scroll to "Related Records" section

2. **Verify Tab Structure**
   - [ ] Two tabs are visible: "Grouped View" and "Hierarchy View"
   - [ ] "Grouped View" has list icon (📋)
   - [ ] "Hierarchy View" has sitemap icon (🌲)
   - [ ] "Grouped View" is active by default

3. **Test Hierarchy Tab Activation**
   - [ ] Click "Hierarchy View" tab
   - [ ] Loading spinner appears briefly
   - [ ] Tree structure loads or empty state appears

### ✅ Hierarchy Tree Display

4. **Test with Parent-Child Relationships**
   - Find entry with parent-child relationships
   - Click "Hierarchy View" tab
   - Verify:
     - [ ] Tree structure is visible
     - [ ] Parent entries show with "Parent" badge
     - [ ] Current entry shows with "Current" badge
     - [ ] Entry type icons are visible and colored
     - [ ] Status badges appear

5. **Test Tree Interactions**
   - [ ] Click chevron (▼) to collapse node with children
   - [ ] Chevron rotates to right-facing (▶)
   - [ ] Children disappear with smooth animation
   - [ ] Click chevron (▶) to expand node
   - [ ] Chevron rotates to down-facing (▼)
   - [ ] Children appear with smooth animation

6. **Test Entry Links**
   - [ ] Click any entry title in tree
   - [ ] New tab opens with that entry's detail page
   - [ ] URL is correct: `/entry/<id>/v2`

### ✅ Empty States

7. **Test Empty Hierarchy**
   - Find entry with no parent-child relationships
   - Click "Hierarchy View" tab
   - Verify:
     - [ ] Empty state message appears
     - [ ] Icon (🌲) is visible
     - [ ] Message says "No hierarchical relationships found"
     - [ ] Subtitle mentions parent-child relationships

### ✅ Error Handling

8. **Test Network Error (Optional)**
   - Disable network or stop API
   - Click "Hierarchy View" tab
   - Verify:
     - [ ] Error message appears
     - [ ] "Retry" button is visible
     - [ ] Clicking retry attempts to reload

### ✅ Visual Styling

9. **Test Light Mode**
   - Ensure light mode is active
   - View hierarchy tree
   - Verify:
     - [ ] Current entry has blue highlight
     - [ ] Parent entry has cyan highlight
     - [ ] Hover effects work on nodes
     - [ ] Text is readable
     - [ ] Icons have correct colors

10. **Test Dark Mode**
    - Switch to dark mode
    - View hierarchy tree
    - Verify:
      - [ ] Current entry has blue highlight (darker)
      - [ ] Parent entry has cyan highlight (darker)
      - [ ] Hover effects work on nodes
      - [ ] Text is readable in dark theme
      - [ ] Icons have correct colors

### ✅ Tab Switching

11. **Test Tab Navigation**
    - [ ] Switch to "Hierarchy View" - content loads
    - [ ] Switch back to "Grouped View" - cards are still there
    - [ ] Switch to "Hierarchy View" again - no reload (cached)
    - [ ] Both tabs maintain their state

### ✅ Performance

12. **Test Lazy Loading**
    - Open entry detail page
    - Check Network tab in browser DevTools
    - Verify:
      - [ ] Hierarchy API call is NOT made on page load
      - [ ] Click "Hierarchy View" tab
      - [ ] NOW hierarchy API call is made
      - [ ] Subsequent tab activations don't call API again

13. **Test Large Hierarchies**
    - Find entry with many children (if available)
    - Click "Hierarchy View" tab
    - Verify:
      - [ ] Tree renders without lag
      - [ ] Expand/collapse is smooth
      - [ ] Tree is limited to 3 levels deep

### ✅ Responsive Design

14. **Test on Mobile**
    - Resize browser to mobile width (< 768px)
    - View hierarchy tree
    - Verify:
      - [ ] Tree is readable on small screen
      - [ ] Tabs stack properly
      - [ ] Touch targets are large enough
      - [ ] Indentation is reduced appropriately

### ✅ Browser Compatibility

15. **Test in Different Browsers**
    - [ ] Chrome/Edge - All features work
    - [ ] Firefox - All features work
    - [ ] Safari - All features work
    - [ ] Mobile browsers - All features work

## Test Scenarios

### Scenario 1: Project Management
**Setup**: Create project → tasks → subtasks structure

1. Create entry: "Website Redesign" (type: Project)
2. Create entry: "Design Phase" (type: Task)
3. Create relationship: Design Phase → child of → Website Redesign
4. Create entry: "Create Mockups" (type: Subtask)
5. Create relationship: Create Mockups → child of → Design Phase

**Test**:
- Navigate to "Design Phase" entry
- Click "Hierarchy View" tab
- Expected result:
  ```
  ▼ Website Redesign [Parent]
    ▼ Design Phase [Current]
      ▶ Create Mockups
  ```

### Scenario 2: Organization Structure
**Setup**: Create company → department → employee structure

1. Create entry: "Acme Corp" (type: Organization)
2. Create entry: "Engineering Dept" (type: Department)
3. Create relationship: Engineering Dept → child of → Acme Corp
4. Create entry: "John Doe" (type: Employee)
5. Create relationship: John Doe → child of → Engineering Dept

**Test**:
- Navigate to "Engineering Dept" entry
- Click "Hierarchy View" tab
- Expected result:
  ```
  ▼ Acme Corp [Parent]
    ▼ Engineering Dept [Current]
      ▶ John Doe
  ```

### Scenario 3: No Hierarchical Relationships
**Setup**: Entry with only non-hierarchical relationships

1. Create entry: "Task A" (type: Task)
2. Create entry: "Task B" (type: Task)
3. Create relationship: Task A → related to → Task B (not parent-child)

**Test**:
- Navigate to "Task A" entry
- Click "Hierarchy View" tab
- Expected result: Empty state message

### Scenario 4: Deep Hierarchy (3+ levels)
**Setup**: Create 4+ level deep structure

1. Create: Level 1 → Level 2 → Level 3 → Level 4 → Level 5

**Test**:
- Navigate to Level 3
- Click "Hierarchy View" tab
- Expected result: Tree limited to 3 levels (API max_depth)

## Common Issues & Solutions

### Issue: Hierarchy tab is empty but relationships exist
**Solution**: Check if relationships are parent-child type (contains "Parent", "Contains", or "Has" in label)

### Issue: Tree doesn't expand/collapse
**Solution**: Check browser console for JavaScript errors, verify event listeners are attached

### Issue: Current entry not highlighted
**Solution**: Verify entry ID matches, check CSS classes are applied

### Issue: Links don't work
**Solution**: Check if `/entry/{id}/v2` route exists, verify entry IDs are correct

### Issue: Loading spinner stuck
**Solution**: Check API endpoint is accessible, verify network connection

### Issue: Styling broken in dark mode
**Solution**: Verify dark mode theme classes, check CSS variable values

## Browser DevTools Checks

### Console
Look for:
- ✅ "Initializing relationships section for entry: X"
- ✅ No JavaScript errors
- ✅ Successful API calls to `/api/entries/{id}/relationships/hierarchy`

### Network Tab
Verify:
- ✅ Hierarchy API call returns 200 status
- ✅ Response contains valid JSON
- ✅ Call only made when hierarchy tab is clicked (lazy loading)

### Elements Tab
Check:
- ✅ Tab structure exists in DOM
- ✅ Tree nodes have correct classes
- ✅ CSS styles are applied
- ✅ Event listeners attached to toggle buttons

## Success Criteria

✅ All checklist items pass
✅ All test scenarios work as expected
✅ No console errors
✅ Smooth animations
✅ Responsive on all devices
✅ Works in all major browsers
✅ No performance issues

## Reporting Issues

If you find bugs, please report with:
1. Browser and version
2. Steps to reproduce
3. Expected behavior
4. Actual behavior
5. Screenshot (if visual issue)
6. Console errors (if any)

---

**Happy Testing! 🎉**
