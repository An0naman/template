# Compose Note - Editable Preview Feature

## Overview
Enhanced the note preview to allow direct editing of title and content before applying the note, giving users the ability to make quick tweaks without going through the conversation again.

## Changes Made

### File: `app/templates/sections/_ai_assistant_section.html`

#### 1. Made Title Editable
**Before:**
```html
<h5 class="mb-1">${noteProposal.note_title || 'Untitled Note'}</h5>
```

**After:**
```html
<h5 class="mb-1 editable-title" contenteditable="true" 
    data-field="note_title"
    style="border: 1px dashed transparent; padding: 4px; border-radius: 4px;"
    onfocus="this.style.borderColor='#0d6efd'; this.style.backgroundColor='#fff';"
    onblur="this.style.borderColor='transparent'; this.style.backgroundColor='transparent'; updateNoteField('note_title', this.textContent);"
>${noteProposal.note_title || 'Untitled Note'}</h5>
```

#### 2. Made Content Editable
**Before:**
```html
<div class="mt-2 p-2 border rounded bg-light" style="white-space: normal;">
    ${formattedContent}
</div>
```

**After:**
```html
<div class="mt-2 p-2 border rounded bg-light editable-content" contenteditable="true"
    data-field="note_text"
    style="white-space: normal; min-height: 100px; border: 1px dashed transparent !important;"
    onfocus="this.style.borderColor='#0d6efd'; this.style.backgroundColor='#fff';"
    onblur="this.style.borderColor='transparent'; this.style.backgroundColor='#f8f9fa'; updateNoteField('note_text', this.innerHTML);"
>${formattedContent}</div>
```

#### 3. Added Visual Hint
```html
<small class="text-muted d-block mb-1"><i class="fas fa-pencil-alt"></i> Click to edit</small>
```

#### 4. New Helper Function: `updateNoteField()`
```javascript
function updateNoteField(field, value) {
    if (!currentNoteProposal) return;
    
    if (field === 'note_title') {
        currentNoteProposal.note_title = value.trim();
    } else if (field === 'note_text') {
        // Convert HTML back to markdown-like format
        currentNoteProposal.note_text = value
            .replace(/<br\s*\/?>/gi, '\n')
            .replace(/<\/p>/gi, '\n\n')
            .replace(/<p>/gi, '')
            .replace(/<strong>(.*?)<\/strong>/gi, '**$1**')
            .replace(/<h6>(.*?)<\/h6>/gi, '### $1\n')
            .replace(/<h5>(.*?)<\/h5>/gi, '## $1\n')
            .replace(/<h4>(.*?)<\/h4>/gi, '# $1\n')
            .replace(/<\/?ul>/gi, '')
            .replace(/<li>(.*?)<\/li>/gi, '- $1\n')
            .replace(/<[^>]+>/g, '')
            .trim();
    }
}
```

## Features

### Visual Feedback
- **Dashed Border**: Appears on focus to indicate editability
- **Background Change**: White background when editing, gray when not
- **Border Color**: Blue border on focus (Bootstrap primary color)
- **Pencil Icon**: Visual hint "Click to edit"

### Editing Behavior
- **Title Editing**: 
  - Click to edit
  - Plain text editing
  - Updates `currentNoteProposal.note_title` on blur
  
- **Content Editing**:
  - Click to edit
  - Rich text editing (preserves HTML formatting)
  - Converts HTML back to markdown on blur
  - Updates `currentNoteProposal.note_text`

### HTML to Markdown Conversion
When you edit the content, it intelligently converts HTML back to markdown:
- `<br>` → `\n` (line breaks)
- `<strong>` → `**text**` (bold)
- `<h4-h6>` → `# ## ###` (headers)
- `<li>` → `- ` (bullets)
- Strips other HTML tags

## User Experience

### Before Fix
```
AI: "Here's your note..."
User: "Change 'yeast' to 'Yeast'"
AI: [Regenerates entire note]
User: "Now capitalize 'Wine'"
AI: [Regenerates again]
```

### After Fix
```
AI: "Here's your note..."
User: [Clicks title, edits directly]
User: [Clicks content, fixes typo]
User: [Clicks Apply Note]
✅ Done in seconds!
```

## Use Cases

### 1. Quick Typo Fixes
```
AI: "Black Berry Wine"
You: [Edit to] "Blackberry Wine"
```

### 2. Capitalization
```
AI: "using yeast and bentonite"
You: [Edit to] "Using Yeast and Bentonite"
```

### 3. Adding Details
```
AI: "Temperature: 68°F"
You: [Edit to] "Temperature: 68°F (ideal range)"
```

### 4. Removing Content
```
AI: "This is a very comprehensive detailed note..."
You: [Delete] "very comprehensive"
```

### 5. Reformatting
```
AI: "First step, Second step, Third step"
You: [Edit to]
     "- First step
      - Second step  
      - Third step"
```

## Benefits

1. **Speed**: No need to regenerate note for minor tweaks
2. **Control**: Direct editing gives full control
3. **Efficiency**: One-click apply after edits
4. **Flexibility**: Edit as much or as little as needed
5. **Natural**: Familiar contenteditable interface

## Technical Details

### ContentEditable
- Uses native browser `contenteditable` attribute
- No additional libraries required
- Works on all modern browsers

### State Management
- Updates `currentNoteProposal` object in real-time
- Changes persist through preview refreshes
- Applied note reflects all edits

### Formatting Preservation
- Maintains rich text formatting during editing
- Converts back to markdown for storage
- Preserves bold, headers, bullets, line breaks

## Limitations

### Current Limitations
1. **No Undo**: Browser's native undo only (Ctrl+Z)
2. **No Formatting Toolbar**: Raw contenteditable (but preserves existing formatting)
3. **Note Type**: Not editable (need to ask AI to change)
4. **Associations**: Not editable (would need complex UI)
5. **URL Bookmarks**: Not editable in preview

### Future Enhancements
Could add:
- Formatting toolbar (bold, italic, headers)
- Note type dropdown selector
- URL bookmark editor
- Entry association selector
- Undo/Redo buttons
- Word count display

## Examples

### Example 1: Title Edit
```html
Before: "Blackberry wine observations"
After:  "Blackberry Wine #1 - Initial Observations"
```

### Example 2: Content Edit
```html
Before: "The wine is very sweet. It needs aging."
After:  "The wine is **very sweet**. 
         
         **Next Steps:**
         - Age for 2 more weeks
         - Re-test gravity"
```

### Example 3: Formatting Enhancement
```html
Before: "Ingredients: Blackberry Juice, Molasses, Yeast"
After:  "**Ingredients:**
         - Blackberry Juice
         - Blackstrap Molasses  
         - Lavin EC-1118 Yeast"
```

## Testing Checklist

- [x] Title editing works
- [x] Content editing works
- [x] Visual feedback on focus/blur
- [x] Changes persist when applying note
- [x] HTML to markdown conversion works
- [x] No errors in console
- [x] Apply Note creates note with edits
- [x] Works with existing formatting
- [x] Works with multiple edits
- [x] Works with cut/paste

## Accessibility

### Keyboard Navigation
- Tab to title → Enter to edit
- Tab to content → Enter to edit
- Tab to Apply Note button
- Escape to blur (browser default)

### Screen Readers
- `contenteditable="true"` is announced
- Focus/blur states are clear
- "Click to edit" hint provides guidance

## Browser Compatibility

✅ Chrome/Edge (Chromium)
✅ Firefox
✅ Safari
✅ Mobile browsers (with virtual keyboard)

## Performance

- **No impact**: Uses native browser features
- **Instant**: No API calls during editing
- **Lightweight**: No additional JavaScript libraries

## Related Files

- `app/templates/sections/_ai_assistant_section.html` - Preview rendering
- `app/api/notes_api.py` - Note creation endpoint (unchanged)
- `COMPOSE_NOTE_QUICK_ACTION.md` - Main feature docs

## Summary

This enhancement makes the Compose Note feature more user-friendly by allowing direct editing of AI-generated content. Users can now:
1. Click on title or content
2. Make edits directly
3. Click "Apply Note"
4. Done!

No more back-and-forth conversations for minor tweaks! 🎉
