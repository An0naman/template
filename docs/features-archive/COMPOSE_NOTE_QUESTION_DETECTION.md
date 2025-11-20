# Compose Note - Question Detection Fix

## Issue
When users ask questions like "Can you see the previous notes and attachments?" while in Note Composer mode, the AI tries to CREATE a note about viewing notes instead of recognizing it's a question that should be answered conversationally.

## Example Problem

**User**: "Can you see the previous notes and attachments"

**AI Response (Wrong)**:
```json
{
  "note_type": "General",
  "note_title": "Previous Notes and Attachments",
  "note_text": "Yes, I can see previous notes. You can view them in the Notes section below..."
}
```

**Expected Behavior**: AI should recognize this is a QUESTION, not a NOTE REQUEST, and guide the user to ask in general chat mode.

## Root Cause

The Note Composer mode is designed to CREATE notes, so any user input is interpreted as a note creation request. The AI lacks context clues to distinguish between:
- **Questions** → Answer conversationally
- **Note Requests** → Create note structure

## Solution

### 1. Enhanced Context (ai_service.py)

Added information about existing notes to help AI understand context:

```python
**Entry Context:**
- Title: {context['title']}
- Type: {context['entry_type']}
- Status: {context['status']}
- Description: {context['description']}
+ Existing Notes: {context.get('total_notes', 0)} notes already exist
+ Recent Notes: {', '.join([n['title'] for n in context.get('recent_notes', [])[:3]])} (most recent 3)
```

### 2. Critical Rules for Question Detection

Added explicit rules in the AI prompt:

```python
**CRITICAL: When NOT to create a note:**
- If user is asking a QUESTION about existing notes/data (e.g., "Can you see...", "What are...", "Show me...")
- If user wants to VIEW information, not CREATE a note
- If user is exploring/understanding the data

**In these cases, respond with:**
{
  "reasoning": "User is asking a question, not requesting note creation...",
  "error": "This appears to be a question rather than a note creation request. Please exit note composer mode and ask your question in the general chat, or tell me what note you'd like to create."
}

**When TO create a note:**
- User explicitly asks to "create", "write", "compose", "document", "add", "record" a note
- User describes what should be in a new note
- User provides content for documentation
```

### 3. Frontend Error Handling

Updated frontend to gracefully handle question detection:

```javascript
} else if (data.error) {
    // Handle special case where AI detects this is a question, not a note request
    const errorMessage = data.error;
    chatHistory.push({
        role: 'user',
        content: userPrompt
    });
    chatHistory.push({
        role: 'assistant',
        content: errorMessage
    });
    addMessageToChat('assistant', errorMessage);
```

## How It Works Now

### Scenario 1: User Asks a Question

**User**: "Can you see the previous notes?"

**AI Detects**: This is a question (keywords: "Can you", "see")

**AI Response**:
```json
{
  "error": "This appears to be a question rather than a note creation request. Please exit note composer mode and ask your question in the general chat, or tell me what note you'd like to create."
}
```

**Frontend**: Displays the error message conversationally, maintains chat history

### Scenario 2: User Requests a Note

**User**: "Create a note documenting today's tasting"

**AI Detects**: This is a note request (keywords: "Create", "documenting")

**AI Response**:
```json
{
  "note_type": "Taste Report",
  "note_title": "Tasting Notes - [Date]",
  "note_text": "...",
  "associated_entry_ids": [...]
}
```

**Frontend**: Renders note preview as usual

## Question Detection Keywords

### Triggers for "Question" Detection:
- "Can you see..."
- "What are..."
- "Show me..."
- "Do you have..."
- "Where is..."
- "How many..."
- "Tell me about..."
- "Explain..."
- "What..."
- "Which..."

### Triggers for "Note Creation":
- "Create..."
- "Write..."
- "Compose..."
- "Document..."
- "Add a note..."
- "Record..."
- "Make a note..."
- "I want to document..."

## Benefits

1. **Prevents Confusion**: Users no longer create unwanted notes by accident
2. **Better UX**: Clear guidance on how to use Note Composer vs General Chat
3. **Maintains Context**: Chat history preserved even when redirecting
4. **Flexible**: Can still create notes about viewing data if explicitly requested

## Edge Cases

### Edge Case 1: Ambiguous Request
**User**: "Notes about the ingredients"

**AI Interpretation**: Could be either:
- "Show me existing notes about ingredients" (question)
- "Create a note about the ingredients" (note request)

**Solution**: AI uses context (chat history, previous messages) to determine intent

### Edge Case 2: Follow-up Questions
**User**: "Create a taste report"
**AI**: [Shows preview]
**User**: "Can you see what yeast I used?"

**AI Interpretation**: This is a follow-up QUESTION in context of creating a note, so it should answer the question AND incorporate the info into the note

### Edge Case 3: Meta Questions
**User**: "How do I attach files?"

**AI Response**: Should provide help, not create a note

## User Guidance

When AI detects a question, it provides clear guidance:

```
"This appears to be a question rather than a note creation request. 

To view existing notes and attachments:
1. Exit note composer mode (click the exit button or type 'exit')
2. Look at the Notes section below this chat
3. Or ask your question in general chat mode

Or, if you want to CREATE a note, please tell me what you'd like to document."
```

## Testing Scenarios

### Test 1: Direct Question
```
User: "Can you see the previous notes?"
Expected: Error message with guidance
```

### Test 2: Note Request
```
User: "Create a note about today's observations"
Expected: Note preview
```

### Test 3: Viewing Request
```
User: "Show me the attachments"
Expected: Error message with guidance
```

### Test 4: Ambiguous
```
User: "Notes on fermentation"
Expected: AI asks for clarification or creates note based on context
```

### Test 5: Explicit Note About Viewing
```
User: "Create a note explaining how to view attachments"
Expected: Note preview (user explicitly said "create")
```

## Files Modified

1. **app/services/ai_service.py**
   - Added existing notes count to context
   - Added recent notes list to context
   - Added CRITICAL RULES for question detection
   - Enhanced error response structure

2. **app/templates/sections/_ai_assistant_section.html**
   - Reordered error handling to check `data.error` first
   - Added conversational error display
   - Maintains chat history even on error

## Alternative Approaches Considered

### Approach 1: Mode Switching
Automatically exit Note Composer mode when question detected
- **Pros**: User gets answer immediately
- **Cons**: Disruptive, loses context

### Approach 2: Dual Response
Answer question AND show note preview
- **Pros**: Flexible
- **Cons**: Confusing UI, unclear intent

### Approach 3: Confirmation Prompt
Ask "Did you mean to create a note or ask a question?"
- **Pros**: Clear intent
- **Cons**: Extra step, annoying

**Chosen**: Guidance message (Approach in this fix)
- **Pros**: Clear, helpful, preserves context
- **Cons**: Requires user action

## Future Enhancements

1. **Smart Mode Switching**: Automatically switch modes and answer
2. **Intent Confidence**: Show "Did you mean..." if unsure
3. **Quick Actions**: "Answer this question" button in error message
4. **Learning**: Track which questions users ask in Note Composer mode
5. **Context Menu**: Right-click to "Ask as question" vs "Create note about"

## Related Documentation

- `COMPOSE_NOTE_QUICK_ACTION.md` - Main feature docs
- `COMPOSE_NOTE_IMPLEMENTATION_SUMMARY.md` - Technical details
- `COMPOSE_NOTE_COMPLETE_FIX.md` - All fixes summary

## Status

✅ **Implemented and Deployed**
- Question detection rules added
- Frontend error handling updated
- User guidance messages included
- Testing recommended before full rollout
