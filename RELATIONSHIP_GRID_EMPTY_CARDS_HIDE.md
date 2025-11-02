# Relationship Grid Enhancement: Hide Empty Cards

## Summary
Enhanced the relationship grids in the V2 entry page to automatically hide relationship type cards that have no relationships, making the interface cleaner. Added a toggle button to show/hide empty cards when needed.

## Visual Overview

```
┌─────────────────────────────────────────────────────────┐
│ 🔗 Related Records              [👁️ Show Empty]        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ ╔═══════════════════════════════════════════════════╗ │
│ ║ Parent Organization                        [+ Add] ║ │
│ ╠═══════════════════════════════════════════════════╣ │
│ ║ • Acme Corp                           [Edit][Del]  ║ │
│ ╚═══════════════════════════════════════════════════╝ │
│                                                         │
│ ╔═══════════════════════════════════════════════════╗ │
│ ║ Team Members (3)                       [+ Add]     ║ │
│ ╠═══════════════════════════════════════════════════╣ │
│ ║ • John Doe                            [Edit][Del]  ║ │
│ ║ • Jane Smith                          [Edit][Del]  ║ │
│ ║ • Bob Johnson                         [Edit][Del]  ║ │
│ ╚═══════════════════════════════════════════════════╝ │
│                                                         │
│ [Hidden: 5 empty relationship types]                   │
│                                                         │
└─────────────────────────────────────────────────────────┘

Click "Show Empty" →

┌─────────────────────────────────────────────────────────┐
│ 🔗 Related Records              [🚫👁️ Hide Empty]      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ ╔═══════════════════════════════════════════════════╗ │
│ ║ Parent Organization                        [+ Add] ║ │
│ ╠═══════════════════════════════════════════════════╣ │
│ ║ • Acme Corp                           [Edit][Del]  ║ │
│ ╚═══════════════════════════════════════════════════╝ │
│                                                         │
│ ╔═══════════════════════════════════════════════════╗ │
│ ║ Team Members (3)                       [+ Add]     ║ │
│ ╠═══════════════════════════════════════════════════╣ │
│ ║ • John Doe                            [Edit][Del]  ║ │
│ ║ • Jane Smith                          [Edit][Del]  ║ │
│ ║ • Bob Johnson                         [Edit][Del]  ║ │
│ ╚═══════════════════════════════════════════════════╝ │
│                                                         │
│ ╔═══════════════════════════════════════════════════╗ │ ← Faded
│ ║ Subsidiaries                           [+ Add]     ║ │
│ ╠═══════════════════════════════════════════════════╣ │
│ ║ No relationships yet. Click "Add" to create one.   ║ │
│ ╚═══════════════════════════════════════════════════╝ │
│                                                         │
│ ... (4 more empty types shown)                         │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Changes Made

### File Modified
- `app/templates/sections/_relationships_section_v2.html`

### Features Implemented

#### 1. Auto-Hide Empty Relationship Cards
- Empty relationship type cards (those with 0 relationships) are now hidden by default
- Only cards with actual relationships are displayed initially
- Makes the interface much cleaner, especially for entries with many possible relationship types

#### 2. Toggle Button for Empty Cards
- Added a "Show Empty" / "Hide Empty" button in the section header
- Button only appears when there are empty cards to show/hide
- Clicking toggles visibility of all empty relationship cards
- Icon changes between eye (👁️) and eye-slash (🚫👁️) based on state
- Smooth fade-in/fade-out animations when toggling

#### 3. Visual Distinction
- Empty cards have a slightly different background color when shown
- Helps distinguish between cards with data and empty placeholders
- Respects dark mode theme

### Technical Details

#### CSS Changes
```css
/* Empty relationship cards styling - smooth transitions */
.empty-relationship-card {
    opacity: 0;
    max-height: 0;
    overflow: hidden;
    margin-bottom: 0;
    transition: opacity 0.3s ease, max-height 0.3s ease, margin-bottom 0.3s ease;
}

/* Visual distinction for empty cards when shown */
.empty-relationship-card .card-header {
    background-color: var(--bs-light);
    opacity: 0.8;
}
```

#### JavaScript Logic
1. **Detection**: When rendering cards, detects which ones have 0 relationships
2. **Classification**: Adds `empty-relationship-card` class to empty cards
3. **Hide by Default**: Sets `display: none` inline style on empty cards initially
4. **Toggle Function**: Global function that shows/hides all empty cards with animation
5. **Button Visibility**: Shows toggle button only when there are empty cards

#### Animation Details
- Smooth fade transition (300ms)
- Height animation for better visual flow
- Prevents layout jumps with max-height constraint

## User Experience

### Before
- All relationship type cards shown, even with "No relationships yet" message
- Cluttered interface with many empty cards
- Hard to focus on actual relationships

### After
- Only cards with relationships shown by default
- Clean, focused interface
- Optional visibility of empty cards via toggle button
- Easy to add new relationships by showing empty cards

## Usage

1. **View Entry**: Open any entry detail page (V2 layout)
2. **See Active Relationships**: Only relationship types with data are shown
3. **Add New Relationship Type**: Click "Show Empty" button to reveal all possible relationship types
4. **Hide Again**: Click "Hide Empty" to return to clean view

## Benefits

✅ Cleaner, less cluttered interface  
✅ Focus on actual relationships  
✅ Easy discovery of new relationship opportunities  
✅ Smooth animations enhance UX  
✅ Theme-aware styling  
✅ No breaking changes to existing functionality  

## Bug Fix

### Issue
Initial deployment had a scope error: `hasEmptyCards is not defined`

### Fix
Added `let hasEmptyCards = false;` declaration inside the `renderRelationshipCards` function at line 282.

## Testing Checklist

- [ ] Empty cards hidden by default on page load
- [ ] Toggle button only appears when empty cards exist
- [ ] Toggle button shows/hides empty cards correctly
- [ ] Button text and icon update appropriately
- [ ] Smooth animations when toggling
- [ ] Empty cards visually distinct when shown
- [ ] Works in light and dark themes
- [ ] Can still add relationships to previously hidden cards
- [ ] Filter functionality still works on all cards
- [ ] No console errors

## Future Enhancements

- Remember user preference for showing/hiding empty cards (localStorage)
- Per-relationship-type collapse/expand
- Quick-add button in collapsed view
- Badge count showing number of hidden empty cards
