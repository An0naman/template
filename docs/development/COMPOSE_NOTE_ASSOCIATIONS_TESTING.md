# Compose Note - Entry Associations Testing Checklist

## Prerequisites
- Docker container rebuilt with latest changes
- Entry with at least 2-3 related entries (different types if possible)
- Google Gemini API key configured

## Test Cases

### ✅ Test 1: AI Proactively Suggests Entry Links
**Steps:**
1. Navigate to an entry with related entries (e.g., a Recipe with Ingredient relationships)
2. Activate "Compose Note" Quick Action
3. Request: "Create a technical note about the preparation process"
4. Observe AI response

**Expected Result:**
- AI mentions related entries in note content
- `associated_entry_ids` array contains relevant entry IDs
- Preview shows: "🔗 Associated Entries:" with actual entry names and types
- Example: "• Flour (Ingredient)" instead of "2 entries will be linked"

---

### ✅ Test 2: User Explicitly Mentions Entries
**Steps:**
1. Activate "Compose Note"
2. Request: "Create a note documenting this. Reference the [entry name] and [entry name] entries."
3. Replace [entry name] with actual related entry titles

**Expected Result:**
- AI finds matching entries from related entries list
- Preview displays both entries with their types
- Clicking "Apply Note" creates associations in database

---

### ✅ Test 3: Multiple Entry Types
**Steps:**
1. Use an entry related to multiple entry types (e.g., Recipe → Equipment + Ingredients)
2. Request: "Document everything used in this process"

**Expected Result:**
- Preview shows entries grouped by mention order
- Different entry types clearly labeled
- Example: "• Oven (Equipment) • Flour (Ingredient)"

---

### ✅ Test 4: No Related Entries
**Steps:**
1. Navigate to an entry with NO related entries
2. Activate "Compose Note"
3. Request: "Create a general note"

**Expected Result:**
- No "🔗 Associated Entries:" section appears
- Note composer works normally
- No errors in console

---

### ✅ Test 5: Invalid Entry ID Handling
**Steps:**
1. Manually test API with invalid entry ID: `fetch('/api/entries/99999')`
2. Check preview rendering with mixed valid/invalid IDs

**Expected Result:**
- Preview shows: "• Entry ID 99999 (not found)"
- Valid entries still display correctly
- No JavaScript errors

---

### ✅ Test 6: Conversation Refinement with Associations
**Steps:**
1. Activate "Compose Note"
2. Request: "Create a note about the ingredients"
3. After preview, say: "Also include the equipment entry"
4. Observe updated preview

**Expected Result:**
- AI maintains previous associations
- Adds new entry to `associated_entry_ids`
- Preview updates with combined list

---

### ✅ Test 7: Welcome Message Shows Entry Linking
**Steps:**
1. Activate "Compose Note" Quick Action
2. Read welcome message

**Expected Result:**
- Bullet point: "**Link to related entries across your app** 🔗"
- Example usage: "Mention related entries to link them"
- Tip: "I'll actively look for opportunities to link..."

---

### ✅ Test 8: Preview Loading States
**Steps:**
1. Activate "Compose Note"
2. Request a note that will have associations
3. Watch preview render

**Expected Result:**
- Initially shows: "Loading entry names..."
- Quickly updates with actual entry names
- No flash of wrong content

---

### ✅ Test 9: Large Number of Associations
**Steps:**
1. Create an entry with 10+ related entries
2. Request: "Create a comprehensive note referencing all related items"

**Expected Result:**
- Preview handles long list gracefully
- All entries fetched and displayed
- No performance issues

---

### ✅ Test 10: Apply Note Creates Associations
**Steps:**
1. Complete any test that generates associations
2. Click "Apply Note"
3. Navigate to the newly created note
4. Check the relationship grid or database

**Expected Result:**
- Note appears in both entries' relationship views
- `note_relationships` table has correct entries
- Can navigate between linked entries

---

## Database Verification Queries

### Check Note Associations
```sql
SELECT 
    n.id,
    n.note_title,
    e.id as related_entry_id,
    e.title as related_entry_title,
    et.singular_label as entry_type
FROM notes n
JOIN note_relationships nr ON n.id = nr.note_id
JOIN entries e ON nr.related_entry_id = e.id
JOIN entry_types et ON e.entry_type_id = et.id
WHERE n.id = <note_id>;
```

### Count Associations by Entry
```sql
SELECT 
    e.title,
    COUNT(nr.note_id) as note_count
FROM entries e
LEFT JOIN note_relationships nr ON e.id = nr.related_entry_id
GROUP BY e.id, e.title;
```

---

## Browser Console Checks

### No JavaScript Errors
```javascript
// Should see no errors related to:
- fetchAssociatedEntryNames
- renderNotePreview
- Fetch API calls to /api/entries/{id}
```

### Network Tab Verification
```
Check for:
1. POST /api/ai/chat (with chat_history)
2. GET /api/entries/X (for each associated entry)
3. POST /api/entries/{id}/notes (when applying)
```

---

## Performance Benchmarks

### Entry Name Fetching
- **Target**: < 500ms for 5 entries
- **Max Acceptable**: < 2s for 10 entries
- **Method**: Parallel Promise.all() fetching

### Preview Rendering
- **Target**: < 100ms after data received
- **Includes**: HTML generation + DOM update

---

## Regression Testing

Ensure these existing features still work:

- ✅ File attachments upload and display
- ✅ URL bookmarks in notes
- ✅ Wikipedia link generation
- ✅ Markdown formatting (bold, headers, bullets)
- ✅ Conversation history maintained
- ✅ Note type selection
- ✅ Cancel and restart conversation

---

## Edge Cases to Test

1. **Rapid Requests**: Send multiple compose requests quickly
2. **Large File + Associations**: Upload 5MB file + link 10 entries
3. **Special Characters**: Entry names with emojis, quotes, HTML
4. **Concurrent Sessions**: Two browser tabs composing notes simultaneously
5. **Network Interruption**: Disconnect during entry fetch

---

## User Acceptance Criteria

- [ ] User can see which entries will be linked BEFORE applying note
- [ ] Entry names are human-readable (not just IDs)
- [ ] Entry types provide context (Ingredient, Equipment, etc.)
- [ ] AI proactively suggests relevant entry links
- [ ] User can refine associations through conversation
- [ ] Preview loads quickly (< 1 second for typical case)
- [ ] Feature works with all note types
- [ ] Graceful degradation if entry fetch fails

---

## Known Limitations

1. **No Inline Search**: Cannot search for entries not already related
2. **No Preview Click**: Entry names in preview are not clickable
3. **No Grouping**: Entries shown in flat list, not grouped by type
4. **Manual Mention**: User must mention entry names explicitly (AI doesn't auto-suggest from unrelated entries)

---

## Success Metrics

- **Adoption**: % of notes created with associations increases
- **Accuracy**: AI correctly identifies mentioned entries > 90%
- **Performance**: Average preview load time < 500ms
- **Errors**: < 1% of entry fetches fail
- **User Satisfaction**: Positive feedback on entry linking visibility
