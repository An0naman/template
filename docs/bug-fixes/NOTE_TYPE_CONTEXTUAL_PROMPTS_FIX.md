# Note Type Contextual Prompts - Bug Fix

## Problem Description

The note types maintenance interface had sections for configuring AI contextual prompts for each default note type (General, Important, Warning, Success), but the functionality was broken. Users could not save or load note type-specific prompts.

## Root Cause

The frontend JavaScript was making requests to `/api/system_params/custom_note_types` to get and save note type prompts, but this API endpoint did not exist. The backend only had:
- `GET /api/system_params` - returns ALL system parameters
- `POST/PATCH /api/system_params` - updates system parameters

## Issues Identified

### Issue 1: Missing API Endpoint
**Problem**: Frontend calls `GET /api/system_params/custom_note_types` but endpoint doesn't exist
**Location**: `app/templates/manage_note_types.html` lines 412, 501, 602

### Issue 2: Response Format Mismatch
**Problem**: Frontend expects `{value: '...'}` format but API would return `{custom_note_types: '...'}`
**Location**: `app/templates/manage_note_types.html` line 605 checks for `data.value`

### Issue 3: Incorrect Default Structure
**Problem**: Database default for `custom_note_types` was `'[]'` instead of `'{"custom_types":[],"default_prompts":{}}'`
**Location**: `app/db.py` line 789

## Solution Implemented

### 1. Added Single Parameter Endpoint
**File**: `app/api/system_params_api.py`

Added new route after line 24:
```python
@system_params_api_bp.route('/system_params/<param_name>', methods=['GET'])
def api_get_single_param(param_name):
    """Get a single system parameter by name"""
    try:
        params = get_system_parameters()
        if param_name in params:
            return jsonify({'value': params[param_name]}), 200
        else:
            # Return empty structure for custom_note_types if it doesn't exist yet
            if param_name == 'custom_note_types':
                return jsonify({'value': '{"custom_types":[],"default_prompts":{}}'}), 200
            return jsonify({'error': 'Parameter not found'}), 404
    except Exception as e:
        logger.error(f"Error fetching parameter {param_name}: {e}", exc_info=True)
        return jsonify({'error': 'An internal error occurred.'}), 500
```

**Benefits**:
- Supports GET requests to `/api/system_params/<param_name>`
- Returns proper `{value: '...'}` format expected by frontend
- Provides fallback structure for custom_note_types if not initialized

### 2. Fixed Default Value Structure
**File**: `app/db.py` line 789

Changed:
```python
'custom_note_types': '[]',  # OLD - incorrect structure
```

To:
```python
'custom_note_types': '{"custom_types":[],"default_prompts":{}}',  # NEW - correct structure
```

**Benefits**:
- Matches expected data structure: `{custom_types: [], default_prompts: {}}`
- Supports both custom note types and default note type prompts
- Prevents parsing errors on first load

## Data Flow (Fixed)

### Loading Note Type Prompts
1. Frontend calls `GET /api/system_params/custom_note_types`
2. New endpoint returns `{value: '{"custom_types":[],"default_prompts":{}}'}`
3. Frontend parses JSON and extracts `default_prompts` object
4. Populates textareas for General, Important, Warning, Success note types

### Saving Note Type Prompts
1. Frontend reads current config from `/api/system_params/custom_note_types`
2. Updates `default_prompts[noteTypeName]` with new prompt text
3. POSTs entire structure to `/api/system_params` with `custom_note_types` parameter
4. Existing POST endpoint handles the save (no changes needed)

### Using Note Type Prompts
1. AI service calls `_get_note_type_base_prompt(note_type)`
2. Function loads `custom_note_types` from database
3. Checks `default_prompts` dict for matching note type name
4. Falls back to custom types array if not found in defaults
5. Uses prompt to customize AI responses based on note type

## Testing Verification

After applying these fixes, verify functionality:

1. **Navigate** to Note Types maintenance page
2. **Expand** "AI Setup" section for any default note type (e.g., General)
3. **Enter** a custom prompt in the textarea
4. **Click** "Save Default Prompt" button
5. **Refresh** the page
6. **Verify** the prompt persisted and displays correctly
7. **Create** a new note of that type
8. **Verify** AI responses use the custom contextual prompt

## Files Modified

1. `app/api/system_params_api.py` - Added GET `/system_params/<param_name>` endpoint
2. `app/db.py` - Fixed default structure for `custom_note_types` parameter

## Related Features

This fix complements the recently completed AI Settings reorganization:
- ✅ AI service selector (Gemini/Groq)
- ✅ Model selection (Gemini: 2 models, Groq: 5 models)
- ✅ System-wide prompts configuration (7 prompt types)
- ✅ **Note type-specific contextual prompts (THIS FIX)**

## Version

Fixed in version 1.0.18+ (after AI settings reorganization)
