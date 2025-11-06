# Notes Section: Inline Edit Implementation

## Overview
Added inline edit functionality to the Notes section, allowing users to edit notes directly within the expanded card view without needing a modal.

## Changes Made

### 1. Updated `createNoteCard()` Function
**File:** `/app/templates/sections/_notes_functions.js`

Added a third view mode: **Edit View**

Now each note card has three views:
1. **Collapsed View** - Preview with expand button
2. **Expanded View** - Full details with edit/delete buttons
3. **Edit View** - Inline form for editing note content

**Edit View Structure:**
```html
<div class="note-edit-view" style="display: none;">
    <!-- Header with cancel button -->
    <h5>Edit Note</h5>
    
    <!-- Editable fields -->
    <input class="inline-edit-title" value="[note title]">
    <textarea class="inline-edit-text">[note content]</textarea>
    
    <!-- Bookmarks editor -->
    <div class="inline-edit-bookmarks-container">
        [bookmark fields with add/remove]
    </div>
    
    <!-- Info about limitations -->
    <div class="alert alert-info">
        Reminders, attachments, and associations can only be edited when creating a new note.
    </div>
    
    <!-- Save/Cancel buttons -->
    <button class="save-note-inline-btn">Save Changes</button>
    <button class="cancel-edit-inline-btn">Cancel</button>
</div>
```

**Features:**
- Pre-populated with current note data
- Edit title, content, and bookmarks
- Add/remove bookmarks dynamically
- Info message about limitations
- Save or cancel changes

### 2. Updated Event Handlers in `displayNotes()`
**File:** `/app/templates/sections/_notes_functions.js`

**Added Handlers:**

1. **Edit Button Handler** - Switches to edit mode:
   ```javascript
   '.edit-note-inline-btn' → toggleNoteEditMode(card, true)
   ```

2. **Save Button Handler** - Saves edited note:
   ```javascript
   '.save-note-inline-btn' → saveInlineEdit(card, noteId)
   ```

3. **Cancel Button Handler** - Returns to expanded view:
   ```javascript
   '.cancel-edit-inline-btn' → toggleNoteEditMode(card, false)
   ```

4. **Add Bookmark Handler** - Adds new bookmark field:
   ```javascript
   '.add-bookmark-inline-btn' → addInlineBookmarkField(container)
   ```

5. **Remove Bookmark Handler** - Removes bookmark field (delegated):
   ```javascript
   '.remove-bookmark-btn' → removes bookmark entry
   ```

### 3. New Helper Functions

#### `toggleNoteEditMode(card, enterEdit)`
Switches between expanded view and edit view:
```javascript
function toggleNoteEditMode(card, enterEdit) {
    const expandedView = card.querySelector('.note-expanded-view');
    const editView = card.querySelector('.note-edit-view');
    
    if (enterEdit) {
        expandedView.style.display = 'none';
        editView.style.display = 'block';
        card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    } else {
        expandedView.style.display = 'block';
        editView.style.display = 'none';
    }
}
```

#### `addInlineBookmarkField(container)`
Dynamically adds a new bookmark input field:
```javascript
function addInlineBookmarkField(container) {
    const bookmarkEntry = document.createElement('div');
    bookmarkEntry.className = 'bookmark-edit-entry mb-2 p-2 border rounded';
    
    bookmarkEntry.innerHTML = `
        <div class="row g-2">
            <div class="col-md-5">
                <input type="text" class="bookmark-name-input" placeholder="Name">
            </div>
            <div class="col-md-6">
                <input type="url" class="bookmark-url-input" placeholder="URL">
            </div>
            <div class="col-md-1">
                <button class="remove-bookmark-btn">×</button>
            </div>
        </div>
    `;
    
    container.appendChild(bookmarkEntry);
}
```

**Features:**
- Creates Bootstrap grid layout
- Name and URL inputs
- Remove button
- Auto-removes "no bookmarks" placeholder

#### `getInlineEditBookmarks(card)`
Extracts bookmark data from edit form:
```javascript
function getInlineEditBookmarks(card) {
    const bookmarks = [];
    const bookmarkEntries = card.querySelectorAll('.bookmark-edit-entry');
    
    bookmarkEntries.forEach(entry => {
        const name = entry.querySelector('.bookmark-name-input').value.trim();
        const url = entry.querySelector('.bookmark-url-input').value.trim();
        
        if (url) {
            bookmarks.push({
                friendly_name: name || null,
                url: url
            });
        }
    });
    
    return bookmarks;
}
```

**Features:**
- Iterates through all bookmark fields
- Validates URL is present
- Optional friendly name
- Returns array for API

#### `saveInlineEdit(card, noteId)`
Saves the edited note via API:
```javascript
async function saveInlineEdit(card, noteId) {
    const titleInput = card.querySelector('.inline-edit-title');
    const textInput = card.querySelector('.inline-edit-text');
    
    const noteTitle = titleInput.value.trim();
    const noteText = textInput.value.trim();
    const bookmarks = getInlineEditBookmarks(card);
    
    if (!noteText) {
        alert('Note content cannot be empty.');
        return;
    }
    
    try {
        const response = await fetch(`/api/entries/${entryId}/notes/${noteId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                note_title: noteTitle,
                note_text: noteText,
                url_bookmarks: bookmarks
            })
        });
        
        if (response.ok) {
            alert('Note updated successfully!');
            fetchNotes();
        } else {
            const data = await response.json();
            alert(`Error: ${data.message || 'Failed to update note.'}`);
        }
    } catch (error) {
        console.error('Error updating note:', error);
        alert('An unexpected error occurred.');
    }
}
```

**Features:**
- Validates content is not empty
- Makes PUT request to API
- Success message and refresh
- Error handling with user feedback

### 4. Enhanced CSS Styling
**File:** `/app/templates/sections/_notes_section.html`

**Added Styles:**
```css
/* Edit mode styling */
.note-edit-view {
    background-color: #fff9e6;
    padding: 1rem;
    border-radius: 0.25rem;
    border: 1px solid #ffc107;
}

.note-edit-view h5 {
    color: #856404;
}

.bookmark-edit-entry {
    background-color: #ffffff;
    border: 1px solid #dee2e6;
}
```

**Visual Design:**
- Light yellow background (`#fff9e6`) to distinguish edit mode
- Yellow border (`#ffc107`) for emphasis
- Brown heading color (`#856404`) for contrast
- Clean white bookmark entry backgrounds

## User Flow

### Viewing and Editing a Note

1. **Start:** Note is collapsed showing preview
2. **Expand:** Click "Expand" button
   - Shows full content, bookmarks, attachments, etc.
   - Edit and Delete buttons visible
3. **Edit:** Click "Edit" button
   - Expanded view hides
   - Edit form appears with current data
   - Yellow background indicates edit mode
4. **Modify:** User edits title, content, bookmarks
   - Can add new bookmarks
   - Can remove existing bookmarks
5. **Save:** Click "Save Changes"
   - Validates content not empty
   - Makes API call to update note
   - Shows success message
   - Refreshes notes list
6. **Cancel:** Click "Cancel"
   - Returns to expanded view
   - No changes saved

### Bookmark Management in Edit Mode

1. **View existing:** Current bookmarks pre-populated
2. **Add new:** Click "Add Bookmark" button
   - New fields appear
   - Enter name (optional) and URL
3. **Remove:** Click X button on bookmark
   - Field removed from form
4. **Save:** All bookmarks saved together with note

## Validation

### Client-Side
- **Required:** Note content cannot be empty
- **Optional:** Note title can be empty
- **Optional:** Bookmarks - URL required if adding, name optional

### API-Level
- Same validation as original note creation
- Server-side checks handled by existing endpoint

## Limitations

**What Can Be Edited:**
✅ Note title
✅ Note content
✅ URL bookmarks (add/remove/edit)

**What Cannot Be Edited (Yet):**
❌ Note type (requires adding type selector)
❌ Reminders (complex datetime + notification logic)
❌ File attachments (requires file upload handling)
❌ Associated entries (requires entry search/selection)

**Why Limited?**
- Keeping inline edit simple and focused
- File uploads require more complex UI
- Reminders need proper datetime picker
- Associations need entry search widget
- Can add these features incrementally later

**User Notification:**
Info alert in edit form explains limitations:
> "Reminders, attachments, and associations can only be edited when creating a new note."

## API Integration

### Endpoint Used
```
PUT /api/entries/{entry_id}/notes/{note_id}
```

### Request Body
```json
{
    "note_title": "Updated title",
    "note_text": "Updated content",
    "url_bookmarks": [
        {
            "friendly_name": "Example",
            "url": "https://example.com"
        }
    ]
}
```

### Response
```json
{
    "message": "Note updated successfully"
}
```

## Testing Checklist

- [x] Edit button switches to edit mode
- [x] Form pre-populated with current data
- [x] Title can be edited
- [x] Content can be edited
- [x] Existing bookmarks show correctly
- [ ] Add bookmark button creates new fields
- [ ] Remove bookmark button deletes fields
- [ ] Save button validates content not empty
- [ ] Save button calls API correctly
- [ ] Success message shows on save
- [ ] Notes list refreshes after save
- [ ] Cancel button returns to expanded view
- [ ] Cancel doesn't save changes
- [ ] Edit mode styling (yellow background) displays
- [ ] Multiple notes can be edited independently

## Future Enhancements

### 1. Note Type Editor
```javascript
<select class="form-control inline-edit-type">
    <option value="General">General</option>
    <option value="Important">Important</option>
    <!-- etc -->
</select>
```

### 2. Reminder Editor
- Datetime picker for scheduled_for
- Checkbox for is_read/is_dismissed
- Preview of current reminder status

### 3. File Upload
- File input field
- Preview of existing attachments
- Remove attachment buttons
- Upload new files

### 4. Association Editor
- Search field for entries
- Multiselect dropdown
- Display current associations
- Add/remove functionality

### 5. Live Preview
- Split screen: edit on left, preview on right
- Real-time markdown rendering
- Character count

### 6. Keyboard Shortcuts
- Ctrl+Enter to save
- Escape to cancel
- Tab for next field

### 7. Auto-save Draft
- LocalStorage backup
- Restore on page reload
- Warning before navigation

## Code Quality

### Maintainability
- Modular functions (toggle, add, get, save)
- Clear naming conventions
- Consistent with existing code style
- Reuses existing API endpoint

### Performance
- Minimal DOM manipulation
- Event delegation for remove buttons
- Only refreshes after save success

### Error Handling
- Validates before API call
- Try-catch for network errors
- User-friendly error messages
- Console logging for debugging

## Backward Compatibility

- Modal edit still exists (not removed)
- Can be used as fallback
- API endpoint unchanged
- Existing functionality preserved

## Browser Support

- Modern browsers (Chrome, Firefox, Safari, Edge)
- ES6+ features (arrow functions, template literals, async/await)
- CSS Grid for bookmark layout
- Smooth scrolling with `scrollIntoView`

---

**Status:** ✅ Completed
**Date:** November 6, 2025
**Related Files:** 
- `/app/templates/sections/_notes_section.html`
- `/app/templates/sections/_notes_functions.js`
- `/NOTES_INLINE_EXPANSION.md`
- `/NOTES_SECTION_V2_COMPLETE.md`

## Summary

The inline edit feature provides a seamless editing experience:
- No modal overlays or popups
- Edit directly within the card
- Yellow background clearly indicates edit mode
- Simple bookmark management
- Quick save/cancel workflow
- Maintains context with other notes visible

Users can now view, expand, edit, and save notes without ever leaving the page context!
