# Compose Note Quick Action - Feature Documentation

## Overview
The **Compose Note** Quick Action allows you to collaboratively create comprehensive notes with AI assistance. The AI helps you structure the note, suggest content, interpret attachments, and link to related entries.

## How to Use

### 1. Access the Quick Action
1. Open an entry detail page
2. Navigate to the AI Assistant section
3. Click the **Quick Actions** dropdown
4. Select **"Compose Note"**

### 2. Describe Your Note
The AI will greet you and ask what kind of note you want to create. You can:

- **Describe the purpose**: "Document today's progress on the project"
- **Specify a note type**: "Create a Technical note about the bug fix"
- **Share observations**: "Log the temperature readings from today"
- **Provide context**: "Note down the meeting discussion about timeline changes"

### 3. Attach Files (Optional)
While composing, you can upload files that the AI will interpret:

1. Click the **"Attach Files"** button that appears below the chat
2. Select one or multiple files
3. The AI will:
   - Read text files and consider their content
   - Note other file types for inclusion as attachments
   - Suggest incorporating file content into the note

**Supported file interpretation**: Text files (.txt, .md) are read and analyzed by AI

### 4. Review the Proposal
Once you provide enough context, the AI generates a complete note proposal showing:

- **Note Type**: Automatically selected from available types
- **Title**: A clear, descriptive title
- **Content**: Comprehensive note body (with markdown formatting)
- **Links/URLs**: Any relevant bookmarks mentioned
- **Associated Entries**: Related entries that should be linked
- **Attachments**: Files you've uploaded

### 5. Refine the Note
Don't like something? Just tell the AI:

- "Make the title more specific"
- "Add a link to the documentation"
- "Make the content more concise"
- "Change the note type to Observation"
- "Add more technical details"

The AI will update the proposal based on your feedback.

### 6. Apply the Note
When you're happy with the proposal:

1. Click **"Apply Note"** in the preview card
2. The note is created and added to the entry
3. All attachments are uploaded
4. Related entries are linked
5. The note appears in the Notes section

## Example Workflows

### Quick Progress Note
```
User: "Document today's progress"
AI: [Generates note with today's date, progress summary]
User: [Reviews and clicks Apply]
```

### Technical Documentation with Files
```
User: "Create a technical note about the API implementation"
[User uploads code files and documentation]
AI: [Reads files, generates structured technical note]
User: "Add a link to the GitHub PR"
AI: [Updates note with link]
User: [Applies the note]
```

### Meeting Notes with Associations
```
User: "Log the meeting discussion about Project X timeline"
AI: [Generates note, suggests associating with Project X entry]
User: "Also link to the Budget entry"
AI: [Updates associations]
User: [Applies the note]
```

## Features

### ✨ Intelligent Note Structuring
- AI selects the most appropriate note type
- Creates clear, scannable titles
- Organizes content with markdown formatting
- Suggests relevant links and associations

### 📎 Attachment Interpretation
- Text files are analyzed by AI
- Content can be incorporated into the note body
- All files are properly attached
- File metadata is preserved

### 🔗 Smart Associations
- AI identifies related entries
- Suggests linking to relevant entries
- Maintains relationship context
- Enables cross-entry navigation

### 🔄 Iterative Refinement
- Discuss changes conversationally
- Refine title, content, or structure
- Add or remove elements
- Multiple revision cycles supported

### 💾 Complete Integration
- Notes are fully integrated with the Notes section
- All features work (reminders, editing, deletion)
- Attachments are properly stored
- Searchable and filterable

## Tips

1. **Be Specific**: The more context you provide, the better the note
2. **Upload Early**: Attach files before or during the initial request
3. **Iterate**: Don't expect perfection on the first try - refine as needed
4. **Use Natural Language**: Just describe what you want conversationally
5. **Review Thoroughly**: Check the proposal before applying

## Technical Details

### Backend
- **Endpoint**: `/api/ai/chat` with `action: 'compose_note'`
- **AI Model**: Google Gemini (configured in system settings)
- **Context**: Entry details, relationships, available note types

### Frontend
- **Location**: `app/templates/sections/_ai_assistant_section.html`
- **Mode**: `noteComposerMode` (similar to planning mode)
- **Preview**: Dedicated note preview card with apply/refine options

### Note Creation
- **API**: `/api/entries/{id}/notes` (POST)
- **Format**: `multipart/form-data` for file uploads
- **Fields**: All standard note fields supported

## Troubleshooting

### AI Not Responding
- Check that Gemini API key is configured in system settings
- Verify the entry has the necessary context

### Attachment Upload Fails
- Check file size limits (configured in system settings)
- Verify allowed file types
- Ensure sufficient disk space

### Wrong Note Type Selected
- Explicitly specify the type in your request
- Check available note types for the entry type
- Use the refine option to change it

### Associations Not Working
- Ensure relationships exist between entries
- Verify entry IDs in the proposal
- Check relationship permissions

## Future Enhancements

Potential improvements for this feature:
- Image analysis for visual files
- Voice-to-text for audio notes
- Calendar integration for scheduling
- Template-based note generation
- Bulk note creation
- Note version history

---

**Need Help?** Ask the AI directly in the chat! It can guide you through the process.
