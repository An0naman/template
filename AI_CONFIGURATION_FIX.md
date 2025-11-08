# AI Configuration Fix - Google Gemini API Integration

## Problem Summary

The Google Gemini AI integration was not working properly in deployed app instances (like garden management) even when the API key and model selection were configured via the system parameters UI.

### Root Cause

The `AIService` was implemented as a singleton that initialized **once** when the Flask application started:

1. Service created on module load: `ai_service = AIService()`
2. Configuration checked only during `__init__()`
3. Even though `is_available()` tried to reconfigure if not configured, it didn't detect when system parameters **changed after initialization**
4. Users had to **restart the entire Docker container** for changes to take effect

This was particularly problematic because:
- The framework documentation emphasized that settings could be changed via the UI
- No indication was given that a restart was required
- Multi-app deployments made restarts disruptive

## Solution Implemented

### 1. Enhanced AI Service Reconfiguration (`app/services/ai_service.py`)

**Changes Made:**
- Added configuration tracking: `_last_api_key` and `_last_model_name`
- Modified `_configure()` to detect when settings have changed
- Added `reconfigure()` method to force re-initialization
- Updated `is_available()` to **always** check for configuration changes (lightweight operation)

**Key Improvements:**
```python
def _configure(self):
    """Configure the Gemini AI model"""
    # ... load API key and model from env or system params ...
    
    # Check if configuration has changed
    config_changed = (api_key != self._last_api_key or model_name != self._last_model_name)
    
    if config_changed or not self.is_configured:
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        self.is_configured = True
        self._last_api_key = api_key
        self._last_model_name = model_name
        logger.info(f"Gemini AI successfully configured with model: {model_name}")

def is_available(self) -> bool:
    """Check if AI service is available and configured"""
    # Always try to reconfigure to pick up any system parameter changes
    # This is lightweight if nothing changed
    self._configure()
    return self.is_configured and self.model is not None
```

### 2. New API Endpoint for Manual Reconfiguration (`app/api/ai_api.py`)

Added `/api/ai/reconfigure` endpoint:
```python
@ai_api_bp.route('/ai/reconfigure', methods=['POST'])
def reconfigure_ai():
    """Force reconfiguration of AI service (useful after settings change)"""
    ai_service = get_ai_service()
    success = ai_service.reconfigure()
    
    return jsonify({
        'success': success,
        'message': 'AI service successfully reconfigured' if success else 'Check API key',
        'available': success
    })
```

### 3. Automatic Reconfiguration on Settings Update (`app/api/system_params_api.py`)

Modified `/api/system_params` to automatically reconfigure AI when relevant parameters change:
```python
@system_params_api_bp.route('/system_params', methods=['POST', 'PATCH'])
def api_update_system_params():
    # ... parameter update logic ...
    ai_params_updated = False
    
    for param_name, param_value in data.items():
        # Track if AI-related parameters are being updated
        if param_name in ['gemini_api_key', 'gemini_model_name', 'gemini_base_prompt']:
            ai_params_updated = True
        # ... update parameter ...
    
    # If AI parameters were updated, reconfigure the AI service
    if ai_params_updated:
        from app.services.ai_service import get_ai_service
        ai_service = get_ai_service()
        ai_service.reconfigure()
        logger.info("AI service reconfigured after parameter update")
```

### 4. Improved UI Feedback (`app/templates/settings.html`)

Updated the AI settings form to provide clear feedback:
```javascript
displayStatus('aiStatusMessage', 
    '✅ AI settings saved and applied successfully! No restart required.', 
    'alert-success');
```

## Benefits

### For Users
✅ **No container restart required** - Changes apply immediately  
✅ **Clear feedback** - UI confirms settings are applied  
✅ **Better UX** - Configure AI directly in the settings page  
✅ **Multi-app friendly** - Each app can have its own API key  

### For Framework
✅ **Consistent behavior** - Matches documentation promises  
✅ **Automatic migration** - Existing databases get gemini parameters  
✅ **Backward compatible** - Still supports environment variables  
✅ **Lightweight** - Configuration check is fast if nothing changed  

## Configuration Priority

The AI service checks for configuration in this order:

1. **Environment Variable** `GEMINI_API_KEY` (highest priority)
2. **System Parameter** `gemini_api_key` (via database)
3. **Model name** from system parameters (even if key is from environment)

This allows:
- Docker-level API key configuration (via `docker-compose.yml`)
- Per-app configuration (via system parameters UI)
- Flexibility for different deployment scenarios

## Testing Instructions

### For Existing Apps (like garden management)

1. **Without restarting the container:**
   ```bash
   # Access your app
   open http://your-server:5001
   ```

2. **Configure AI settings:**
   - Go to Settings → AI Integration Settings
   - Enter your Google Gemini API Key
   - Select a model (e.g., gemini-2.5-flash)
   - Click "Save AI Settings"
   - You should see: "✅ AI settings saved and applied successfully! No restart required."

3. **Verify it works:**
   - Click "Test AI Service" button
   - Should show: "✅ AI service is working correctly!"
   - Status badge should change from "Not Configured" to "Available"

4. **Try AI features:**
   - Create or edit an entry
   - Try the "Generate with AI" button for descriptions
   - Open AI chat on an entry detail page
   - All AI features should now work

### For New Apps

New apps deployed from the updated framework image will have:
- Gemini parameters in database by default (via migration)
- Immediate configuration pickup when API key is set
- No special setup required

## Files Modified

1. **`app/services/ai_service.py`** - Enhanced reconfiguration logic
2. **`app/api/ai_api.py`** - Added `/api/ai/reconfigure` endpoint
3. **`app/api/system_params_api.py`** - Auto-reconfigure on AI param updates
4. **`app/templates/settings.html`** - Improved user feedback

## Migration

The existing migration `migrations/migrate_gemini_api_key.py` ensures all databases have the required parameters:
- `gemini_api_key` (default: empty)
- `gemini_model_name` (default: `gemini-1.5-flash`)
- `gemini_base_prompt` (default: helpful assistant prompt)

This migration runs automatically on container startup via `docker-entrypoint.sh`.

## API Documentation

### Check AI Status
```bash
GET /api/ai/status
```
Response:
```json
{
  "available": true,
  "service": "Google Gemini"
}
```

### Force Reconfiguration
```bash
POST /api/ai/reconfigure
```
Response:
```json
{
  "success": true,
  "message": "AI service successfully reconfigured",
  "available": true
}
```

### Update System Parameters (Auto-reconfigures AI)
```bash
PATCH /api/system_params
Content-Type: application/json

{
  "gemini_api_key": "your-api-key-here",
  "gemini_model_name": "gemini-2.5-flash"
}
```

## Rollout Plan

1. ✅ **Code Changes** - Completed
2. ✅ **Testing** - Verified locally
3. 🔄 **Commit & Push** - Ready to commit
4. 🔄 **Framework Build** - GitHub Actions will build new image
5. 🔄 **App Updates** - Existing apps can pull latest image and restart

## Backward Compatibility

All changes are **fully backward compatible**:
- Existing environment variable configuration still works
- Apps without API keys configured continue to work (AI features disabled)
- No breaking changes to API contracts
- No database schema changes (migration adds parameters if missing)

## Future Enhancements (Optional)

Potential improvements for future iterations:
- Add UI indication of where API key is configured (env vs database)
- Add API usage/quota monitoring
- Support for multiple AI providers (OpenAI, Anthropic, etc.)
- Per-entry-type custom prompts configuration

---

**Status:** ✅ Complete and Ready for Deployment  
**Impact:** 🟢 Low Risk - Backward Compatible Enhancement  
**User Benefit:** 🚀 High - Immediate AI configuration without restarts
