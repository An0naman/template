# URL Handling Fix - Compose Note Quick Action

## Issue
When users requested links to external resources (like Wikipedia pages or product pages), the AI was generating fake/placeholder URLs instead of either:
1. Using URLs explicitly provided by the user, or
2. Leaving the url_bookmarks empty if no URL was provided

## Example Problem
```
User: "I want a link to a wiki page for ingredient X"
AI: [Creates note with url_bookmarks: [{"friendly_name": "Ingredient X Wiki", "url": "https://example.com/wiki/ingredient-x"}]]
Result: Fake URL that doesn't work
```

## Solution Implemented

### 1. Updated AI Prompt with Critical Rules

Added explicit instructions in the `compose_note()` method prompt:

```python
CRITICAL RULES FOR URL BOOKMARKS:
- ONLY include URLs if the user explicitly provided them in their message
- DO NOT generate, invent, or suggest fake/placeholder URLs
- DO NOT use example.com or placeholder URLs
- If user asks for a link but didn't provide the actual URL, leave url_bookmarks EMPTY []
- If user wants to link to another entry, use associated_entry_ids instead of url_bookmarks
- Real URLs only - if you're not certain the URL is real and working, don't include it
```

### 2. Updated Welcome Message

Modified the Note Composer welcome message to guide users:

```javascript
- Add links and bookmarks (if you provide URLs)  // Updated
...
- Provide URLs to include (e.g., "Add a link to https://example.com")  // Added
...
💡 **Tip**: If you want to include web links, provide the actual URLs in your message!  // Added
```

## Expected Behavior Now

### Scenario 1: User Provides URL
```
User: "Create a note about our API with a link to https://docs.example.com/api"
AI: [Creates note with url_bookmarks: [{"friendly_name": "API Documentation", "url": "https://docs.example.com/api"}]]
Result: ✅ Real URL included
```

### Scenario 2: User Mentions Link Without URL
```
User: "Create a note with a link to the ingredient wiki"
AI: [Creates note with url_bookmarks: []]
AI reasoning: "User requested a link but didn't provide the URL. They can add it later."
Result: ✅ No fake URL, user can add it manually later
```

### Scenario 3: User Wants to Link Another Entry
```
User: "Create a note and link it to the Ingredient X entry"
AI: [Creates note with associated_entry_ids: [123]]
AI reasoning: "Linked to Ingredient X entry (ID: 123) from related entries."
Result: ✅ Uses entry associations instead of URL bookmarks
```

### Scenario 4: User Provides Multiple URLs
```
User: "Add links to https://wikipedia.org/Hops and https://example.com/product/123"
AI: [Creates note with url_bookmarks: [
    {"friendly_name": "Wikipedia - Hops", "url": "https://wikipedia.org/Hops"},
    {"friendly_name": "Product Page", "url": "https://example.com/product/123"}
]]
Result: ✅ Both real URLs included
```

## User Guidance

### How to Add Links

**Option 1: Provide URL in Request**
```
"Create a progress note with a link to https://github.com/project/pr/123"
```

**Option 2: Multi-step (if you don't have URL handy)**
```
User: "Create a progress note"
AI: [Generates note without URLs]
User: "Add a link to https://github.com/project/pr/123"
AI: [Updates note with the URL]
```

**Option 3: Link to Related Entries Instead**
```
"Create a note and associate it with the Recipe entry"
```

## Technical Details

**Files Modified:**
- `app/services/ai_service.py` - Updated prompt in `compose_note()` method
- `app/templates/sections/_ai_assistant_section.html` - Updated welcome message

**Prompt Engineering:**
- Emphasized "CRITICAL RULES" to make instructions stand out
- Used negative instructions (DO NOT) to prevent unwanted behavior
- Provided specific examples of what to avoid
- Added reasoning requirement to explain decisions

**User Experience:**
- Clearer guidance in welcome message
- Users know to provide URLs explicitly
- No more broken fake links in notes
- Can still add URLs manually later if needed

## Benefits

1. **No More Fake URLs**: AI won't generate placeholder links
2. **Clear Expectations**: Users know what to provide
3. **Better UX**: Users can add links later if they don't have them handy
4. **Correct Associations**: Guides users to use entry associations when appropriate
5. **Maintains Flexibility**: Users can provide URLs at any point in the conversation

## Testing Recommendations

Test the following scenarios:

1. **Request with explicit URL**:
   - "Create a note with link to https://example.com"
   - Verify URL is included correctly

2. **Request mentioning link without URL**:
   - "Create a note with a wikipedia link"
   - Verify url_bookmarks is empty []
   - Check reasoning mentions missing URL

3. **Request with multiple URLs**:
   - "Add links to https://site1.com and https://site2.com"
   - Verify both URLs are included

4. **Request for entry link**:
   - "Link this note to Entry X"
   - Verify uses associated_entry_ids, not url_bookmarks

5. **Follow-up to add URL**:
   - Initial: "Create progress note"
   - Follow-up: "Add link to https://example.com"
   - Verify URL is added in refinement

## Edge Cases Handled

- ❌ User says "add a link" without URL → Empty url_bookmarks
- ❌ AI wants to suggest a URL → Doesn't include it
- ✅ User provides partial URL (http://...) → Included as-is
- ✅ User provides multiple URLs in one message → All included
- ✅ User wants entry association → Uses associated_entry_ids
- ✅ User adds URL in follow-up → Updates note with URL

---

**Status**: Implemented and deployed ✅

**Next Steps**: Monitor user behavior to see if additional guidance is needed
