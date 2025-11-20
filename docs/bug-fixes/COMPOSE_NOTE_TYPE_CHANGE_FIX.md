# Compose Note - Note Type Change Fix

## Issue
User reported that when trying to discuss changing the note type during the conversation, the AI was not able to change it.

## Root Cause
The AI prompt had two issues that made it reluctant to change note types:

1. **Vague refinement instruction**: When a current draft existed, the prompt said:
   ```
   User wants to refine this draft. Apply their requested changes while keeping the structure.
   ```
   The phrase "while keeping the structure" made the AI think it shouldn't change the note type.

2. **No explicit note type change instructions**: The prompt didn't have specific rules about honoring note type change requests.

## Solution

### 1. Enhanced Refinement Instructions
**Before:**
```python
**User wants to refine this draft. Apply their requested changes while keeping the structure.**
```

**After:**
```python
**User wants to refine this draft. Apply their requested changes.**
- If they ask to change note type, update the note_type field to match their request
- If they ask to modify content, update note_text accordingly
- If they want to add/remove links or associations, update those fields
- You can change ANY aspect of the note based on user feedback
```

### 2. Added Critical Rules for Note Type
Added a new dedicated section in the prompt:

```python
CRITICAL RULES FOR NOTE TYPE:
- When user asks to change note type (e.g., "make this a Recipe note", "change to Technical"), UPDATE the note_type field
- Note type changes should be honored immediately - don't keep the old type
- Available types are listed above - choose from that list ONLY
- If user says "change type to X" or "make this a X note", set note_type to "X" (if it's in the available list)
- In refinement conversations, note_type can change as easily as any other field
```

### 3. Updated Reasoning Guidelines
Enhanced the reasoning section to include:
```python
- Mention in reasoning if you changed the note type based on user request
```

## Files Changed
- `app/services/ai_service.py` - Enhanced `compose_note()` method prompt

## Usage Examples

### Example 1: Direct Type Change Request
**Initial Note:** Type = "General"
```
User: "Change this to a Technical note"
```
**Expected Result:**
- AI updates `note_type` to "Technical"
- Keeps existing content
- Mentions in reasoning: "Changed note type from General to Technical as requested"

### Example 2: Type Change with Content Update
```
User: "Make this a Recipe note and add cooking instructions"
```
**Expected Result:**
- AI updates `note_type` to "Recipe"
- Adds cooking instructions to `note_text`
- Mentions both changes in reasoning

### Example 3: Type Suggestion During Creation
```
User: "Create a note documenting the troubleshooting steps"
AI: Proposes note_type = "Technical" (appropriate for troubleshooting)

User: "Actually, make it a Log entry instead"
```
**Expected Result:**
- AI updates `note_type` to "Log"
- Adjusts content style if needed
- Honors user preference over initial suggestion

### Example 4: Invalid Type Request
```
User: "Change this to a FunkyNote type"
```
**Expected Result:**
- AI responds that "FunkyNote" is not in available types
- Lists available types
- Asks user to choose from valid options

## Testing Scenarios

### Test 1: Simple Type Change
1. Compose a note (gets type "General")
2. Say: "Change to Recipe"
3. Verify: note_type updates to "Recipe"

### Test 2: Type Change Mid-Conversation
1. Compose a note
2. Refine content 2-3 times
3. Say: "Actually change the type to Technical"
4. Verify: Type changes without losing previous refinements

### Test 3: Type Change with Other Modifications
1. Compose a note
2. Say: "Change to Log and add today's date to the title"
3. Verify: Both type AND title are updated

### Test 4: Case Insensitivity
1. Compose a note
2. Say: "make this a RECIPE note" (uppercase)
3. Verify: AI matches to "Recipe" type correctly

### Test 5: Implied Type Change
1. Compose a note about troubleshooting
2. Say: "Add more technical details and format as a tech note"
3. Verify: AI infers "Technical" note type

## Validation Checklist

After rebuilding Docker container:

- [ ] Can change note type during initial composition
- [ ] Can change note type after previewing once
- [ ] Can change note type multiple times in same conversation
- [ ] Type changes don't lose other modifications (content, links, associations)
- [ ] Invalid type names are handled gracefully
- [ ] AI reasoning mentions type changes
- [ ] Preview updates immediately with new type badge

## Technical Details

### AI Prompt Structure
```
1. Entry context
2. Available note types (listed explicitly)
3. Related entries
4. Conversation history
5. Current draft (if exists)
6. Refinement instructions ← ENHANCED
7. Attachment context
8. JSON response format
9. Critical rules for URLs
10. Critical rules for entry associations
11. Critical rules for note type ← NEW
12. Other important rules
```

### Conversation State
The `chat_history` array maintains context:
```javascript
[
  {role: 'user', content: 'Create a technical note'},
  {role: 'assistant', content: 'I've composed a note...'},
  {role: 'user', content: 'Change to Recipe'},  // This request now works
  {role: 'assistant', content: 'I've updated...'}
]
```

## Benefits

1. **User Control**: Users can change their mind about note type at any stage
2. **Natural Conversation**: No need to cancel and restart for type changes
3. **Flexibility**: Combine type changes with content updates in one request
4. **Clear Feedback**: AI mentions type changes in reasoning

## Related Issues

This fix also improves:
- Changing any field during refinement (not just note type)
- AI's willingness to make structural changes
- Clarity about what can be modified in conversation

## Performance Impact
- No performance impact
- Same number of API calls
- Slightly longer prompt (negligible token increase)

## Backward Compatibility
✅ Fully backward compatible
- Existing compose workflows unchanged
- New capabilities added without breaking old behavior
- No database changes required

## Future Enhancements

Potential improvements:
1. **Type Suggestions**: AI could suggest better type based on content
2. **Type Validation**: Frontend could show available types in dropdown
3. **Type History**: Show which types were tried during composition
4. **Smart Defaults**: Learn user's preferred types over time
