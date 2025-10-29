# AI Chatbot Feature for Entries

## Overview
Added a context-aware AI chatbot feature to entry detail pages that provides intelligent assistance about each entry.

## Changes Made

### 1. Backend API (`app/api/ai_api.py`)
- **New Endpoint**: `/api/ai/entry-chat` (POST)
  - Accepts: `entry_id`, `message`, `is_first_message`
  - Returns: AI-generated response with entry context
  - Checks AI availability and returns helpful error messages

### 2. AI Service (`app/services/ai_service.py`)
- **New Method**: `_gather_entry_context(entry_id)`
  - Collects comprehensive entry information:
    - Basic details (title, description, type, status, creation date)
    - Time metrics (days active, days until/overdue from end date)
    - Notes count by type and recent notes preview
    - Related entries and relationships
    - Sensor data statistics (if applicable)
    - Project description from system parameters
  
- **New Method**: `chat_about_entry(entry_id, user_message, is_first_message)`
  - Builds context-rich prompt for AI
  - Generates intelligent responses based on entry data
  - Provides greeting and highlights for first message
  - Handles errors gracefully

### 3. Frontend UI (`app/templates/entry_detail.html`)
- **New Section**: AI Assistant collapsible section in entry detail page
  - Located below the Notes section
  - Features:
    - Status indicator showing AI availability
    - Chat message container with 400px height
    - Input field with send and clear buttons
    - Enter key support for sending messages
    - Visual distinction between user and AI messages
    - Typing indicator animation
    - Themed styling that respects dark/light mode

### 4. JavaScript Functionality
- **Functions Added**:
  - `checkAIAvailability()` - Checks if Gemini API is configured
  - `sendAIMessage()` - Sends user message to backend
  - `addMessageToChat(type, text)` - Renders messages in chat UI
  - `addTypingIndicator()` / `removeTypingIndicator()` - Shows AI "thinking"
  - `clearAIChat()` - Resets chat to initial state
  - `escapeHtml(text)` - Prevents XSS attacks

## How It Works

### First Message Behavior
When a user starts a chat (first message), the AI:
1. Reads the system parameter `project_description` to understand the application context
2. Gathers all entry details (age, status, relationships, notes, sensor data)
3. Provides a brief, friendly greeting
4. Highlights important aspects (e.g., overdue dates, recent activity)
5. Offers to help with questions

### Subsequent Messages
For follow-up messages, the AI:
- Maintains context about the entry
- Answers specific questions
- Provides insights based on the entry's data
- Helps users understand relationships and patterns

## Entry Context Provided to AI

The AI receives:
- **Entry Basics**: Title, description, type, status
- **Entry Type Description**: Explanation of what this entry type represents
- **Timeline**: Creation date, days active, intended/actual end dates
- **Activity**: Note counts by type, recent note previews
- **Relationships**: Related entries with relationship types AND their descriptions
- **Sensor Data**: 
  - Basic: Sensor type statistics and reading counts (always provided)
  - Detailed (on-demand): Full statistics including average, min, max, median, std dev, recent readings
  - Smart parsing: Handles values with units (e.g., "24.05C", "75%", "1013hPa")
- **System Context**: Project description from system parameters

## UI Features

1. **Status Indicator**: Shows if AI is ready or needs configuration
2. **Chat Interface**: Clean, modern chat UI with message bubbles
3. **User Messages**: Right-aligned, blue background
4. **AI Messages**: Left-aligned, light background with robot icon
5. **Typing Animation**: Three-dot animation while AI generates response
6. **Error Handling**: Clear error messages if AI is unavailable
7. **Responsive Design**: Works on mobile and desktop
8. **Theme Support**: Respects dark/light mode settings

## Docker Compatibility

The feature is fully compatible with Docker deployment:
- No additional dependencies required (uses existing `google-generativeai` package)
- Configuration via environment variable: `GEMINI_API_KEY`
- Can also be configured via system parameters in the UI
- No changes needed to `Dockerfile` or `docker-compose.yml`

## Bug Fixes Applied

### Issue 1: sqlite3.Row object has no attribute 'get'
**Fix**: Convert `sqlite3.Row` objects to dictionaries before accessing with `.get()` method
```python
entry_dict = dict(entry)  # Convert Row to dict
context['status'] = entry_dict.get('status', 'active')  # Now works!
```

### Issue 2: no such table: Relationship
**Fix**: Updated query to use correct table name `EntryRelationship` instead of `Relationship`
```sql
-- Old (incorrect):
FROM Relationship r WHERE r.entry_id = ?

-- New (correct):
FROM EntryRelationship er WHERE er.source_entry_id = ?
```

Also updated the relationship structure to match the actual schema:
- `source_entry_id` instead of `entry_id`
- `target_entry_id` instead of `related_entry_id`
- Join with `RelationshipDefinition` to get relationship name

## Configuration

### Option 1: Environment Variable (Recommended for Docker)
```yaml
# In docker-compose.yml
environment:
  - GEMINI_API_KEY=your_api_key_here
```

### Option 2: System Parameters (UI)
1. Go to Settings → System Configuration
2. Set "Gemini API Key" parameter
3. Optionally set "Gemini Model Name" (defaults to `gemini-1.5-flash`)
4. Set "Project Description" to customize AI context

## Testing

To test the feature:
1. Ensure Gemini API key is configured
2. Navigate to any entry detail page
3. Click "Start Chat" in the AI Assistant section
4. Send a message like "Tell me about this entry"
5. AI should respond with context-aware information

## Example Interactions

**User**: "Tell me about this entry"
**AI**: "This is the 'Project Alpha' entry, which is a Development type. Development entries are used for tracking software projects. It was created 45 days ago and is currently active. You have 12 notes (8 General, 3 Progress Updates, 1 Meeting Note) and it's related to 3 other entries..."

**User**: "How many days until the deadline?"
**AI**: "Based on the intended end date, you have 15 days remaining until the deadline..."

**User**: "What are the recent notes about?"
**AI**: "Your most recent notes include: 1) A progress update from yesterday discussing... 2) A general note from 3 days ago about..."

**User**: "What's the average temperature?"
**AI**: "Looking at the temperature sensor data, the average is 23.45°C. The readings range from 20.10°C to 26.80°C, with a median of 23.20°C. Recent readings show: 24.05°C, 23.80°C, 23.50°C..."

**User**: "Tell me about the related Server-01 entry"
**AI**: "Server-01 is a Hardware entry that's related to this project as 'Depends on'. It's a production server hosting the application backend with 32GB RAM and running Ubuntu 22.04..."

## Benefits

1. **Context-Aware Help**: AI knows everything about the entry including:
   - Entry type descriptions
   - Related entry descriptions
   - Detailed sensor statistics with timestamps
2. **No Conversation Storage**: Each message is stateless, no database clutter
3. **Intelligent Insights**: AI can:
   - Calculate dates and time differences
   - Summarize relationships with context
   - Analyze sensor data (averages, trends, min/max)
   - Parse sensor values with units (24.05C, 75%, etc.)
4. **On-Demand Data**: Fetches detailed sensor statistics only when needed
5. **Easy to Use**: Simple chat interface, no learning curve
6. **Flexible**: Works with any entry type and customizable system description
7. **Secure**: HTML escaping prevents XSS, API key stored safely

## Future Enhancements

Potential improvements:
- Add conversation history (optional persistent storage)
- Support for file analysis (read attached documents)
- Suggested actions (e.g., "Create a related entry", "Add a note")
- Voice input/output
- Export chat conversations
- Multi-language support
