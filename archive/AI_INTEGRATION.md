# AI Integration Documentation

## Overview

This document describes the Google Gemini AI integration that provides writing assistance throughout the Template App for descriptions, notes, and SQL queries.

## Features

### 1. Entry Description Assistance
- **Generate**: Create new descriptions based on entry type and context
- **Improve**: Enhance existing descriptions for clarity and completeness
- **Location**: Entry detail pages (edit mode)

### 2. SQL IDE Assistance  
- **Generate**: Create SQL queries based on natural language descriptions
- **Explain**: Break down complex SQL queries with plain English explanations
- **Location**: SQL IDE interface

### 3. Note Improvement
- **Enhance**: Improve existing notes for clarity and structure
- **Location**: Available through API for future integration

## Setup Instructions

### 1. Install Dependencies

The AI integration requires the Google Generative AI package:

```bash
pip install google-generativeai>=0.3.0
```

Or run the setup script:

```bash
python setup_ai.py
```

### 2. Get Google Gemini API Key

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the generated API key

### 3. Configure Environment

Add your API key to the environment:

**Option A: Environment Variable**
```bash
export GEMINI_API_KEY='your-api-key-here'
```

**Option B: .env File**
```bash
echo 'GEMINI_API_KEY=your-api-key-here' >> .env
```

**Option C: Docker Compose**
```yaml
environment:
  - GEMINI_API_KEY=your-api-key-here
```

### 4. Restart Application

After setting the API key, restart your application to enable AI features.

## Technical Architecture

### Backend Components

#### AIService (`app/services/ai_service.py`)
Core service class that handles:
- Google Gemini API integration
- Text generation and improvement
- Error handling and fallbacks
- Configuration validation

#### AI API (`app/api/ai_api.py`)
REST endpoints for AI functionality:
- `POST /api/ai/generate_description` - Generate entry descriptions
- `POST /api/ai/improve_note` - Improve existing text
- `POST /api/ai/generate_sql` - Generate SQL queries
- `POST /api/ai/explain_sql` - Explain SQL queries
- `GET /api/ai/status` - Check service availability

### Frontend Integration

#### SQL IDE (`app/templates/sql_ide.html`)
- AI Generate button for query creation
- AI Explain button for query analysis
- Modal dialogs for AI interactions
- Integration with CodeMirror editor

#### Entry Detail (`app/templates/entry_detail.html`)
- AI Generate button for new descriptions
- AI Improve button for existing descriptions
- Responsive button design (text on desktop, icons on mobile)
- Integration with description editing workflow

## API Reference

### Generate Description

**Endpoint**: `POST /api/ai/generate_description`

**Request**:
```json
{
  "entry_type": "maintenance_task",
  "context": "Oil change for vehicle",
  "additional_info": "2019 Honda Civic, 45000 miles"
}
```

**Response**:
```json
{
  "success": true,
  "description": "Regular oil change maintenance for 2019 Honda Civic..."
}
```

### Improve Note

**Endpoint**: `POST /api/ai/improve_note`

**Request**:
```json
{
  "text": "changed oil today",
  "context": "maintenance_task"
}
```

**Response**:
```json
{
  "success": true,
  "improved_text": "Completed oil change maintenance today..."
}
```

### Generate SQL

**Endpoint**: `POST /api/ai/generate_sql`

**Request**:
```json
{
  "description": "Find all overdue maintenance tasks",
  "schema_info": "entries table with due_date column"
}
```

**Response**:
```json
{
  "success": true,
  "sql_query": "SELECT * FROM entries WHERE due_date < DATE('now') AND entry_type = 'maintenance_task'"
}
```

### Explain SQL

**Endpoint**: `POST /api/ai/explain_sql`

**Request**:
```json
{
  "sql_query": "SELECT COUNT(*) FROM entries WHERE due_date < DATE('now')"
}
```

**Response**:
```json
{
  "success": true,
  "explanation": "This query counts all entries that are overdue..."
}
```

## Error Handling

### Service Not Configured
When the API key is missing:
```json
{
  "success": false,
  "error": "AI service not configured"
}
```

### API Errors
When Google's API returns an error:
```json
{
  "success": false,
  "error": "AI service temporarily unavailable"
}
```

### Invalid Requests
When request data is missing or malformed:
```json
{
  "success": false,
  "error": "Missing required field: entry_type"
}
```

## Security Considerations

### API Key Protection
- Store API keys in environment variables, never in code
- Use `.env` files for local development
- Configure secrets management for production

### Content Filtering
- The Gemini API includes built-in safety filters
- Content is processed according to Google's usage policies
- No sensitive data should be sent to the API

### Rate Limiting
- Google Gemini has usage quotas and rate limits
- Implement client-side rate limiting for heavy usage
- Consider caching responses for repeated queries

## Troubleshooting

### AI Features Not Working

1. **Check API Key**:
   ```bash
   echo $GEMINI_API_KEY
   ```

2. **Verify Package Installation**:
   ```bash
   pip list | grep google-generativeai
   ```

3. **Test Service Status**:
   ```bash
   curl http://localhost:5000/api/ai/status
   ```

### Common Issues

**"AI service not configured"**
- API key is missing or incorrect
- Environment variable not set properly
- Application needs restart after setting key

**"AI service temporarily unavailable"**
- Google API is down or rate limited
- Network connectivity issues
- Invalid API key

**Buttons not appearing**
- JavaScript errors in browser console
- Template caching issues
- Blueprint not registered properly

## Development Notes

### Adding New AI Features

1. Add method to `AIService` class
2. Create corresponding API endpoint
3. Add UI components and JavaScript
4. Update documentation and tests

### Customizing Prompts

Edit the prompt templates in `app/services/ai_service.py`:
- Modify `generate_description()` for different description styles
- Update `improve_note()` for specific improvement criteria
- Adjust SQL prompts for your database schema

### Testing

Use the provided test scripts:
```bash
python setup_ai.py  # Test configuration
curl -X POST http://localhost:5000/api/ai/status  # Test API
```

## Future Enhancements

Potential improvements:
- Note editing AI assistance throughout the app
- Smart entry categorization
- Automated reminder text generation
- SQL query optimization suggestions
- Custom prompt templates per user
- Offline AI capability with local models

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review application logs
3. Verify Google AI Studio API status
4. Test with minimal examples

The AI integration is designed to enhance user productivity while maintaining privacy and security best practices.
