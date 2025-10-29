# User Preferences Migration to SQL

## Summary

Successfully migrated locally saved parameters from browser localStorage to SQL database storage. The main focus was on chart preferences that were previously stored in the browser's localStorage.

## Changes Made

### 1. Database Schema
- **Added UserPreferences table** to `app/db.py`:
  ```sql
  CREATE TABLE IF NOT EXISTS UserPreferences (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      preference_name TEXT NOT NULL,
      preference_value TEXT,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      UNIQUE(preference_name)
  );
  ```

### 2. Database Functions
- **Already existed** in `app/db.py`:
  - `get_user_preference(preference_name, default_value=None)`
  - `set_user_preference(preference_name, preference_value)`
  - `get_all_user_preferences()`

### 3. API Layer
- **Created new API** `app/api/user_preferences_api.py`:
  - `GET /api/user_preferences` - Get all preferences
  - `GET /api/user_preferences/<preference_name>` - Get specific preference
  - `POST /api/user_preferences/<preference_name>` - Set specific preference
  - `GET /api/user_preferences/chart/<entry_id>` - Get chart preferences for entry
  - `POST /api/user_preferences/chart/<entry_id>` - Set chart preferences for entry
  - `DELETE /api/user_preferences/chart/<entry_id>` - Delete chart preferences for entry

### 4. Frontend JavaScript Updates
- **Modified chart preference functions** in `entry_detail.html`:
  - `loadChartPreferences()` - Now async, loads from API with localStorage fallback
  - `autoSaveChartPreferences()` - Now async, saves to API with localStorage fallback
  - `saveChartPreferences()` - Now async, saves to API
  - `resetChartPreferences()` - Now async, deletes from API and localStorage

### 5. Application Registration
- **Registered new API blueprint** in `app/__init__.py`:
  ```python
  from .api.user_preferences_api import user_preferences_api_bp
  app.register_blueprint(user_preferences_api_bp, url_prefix='/api')
  ```

## Features

### Chart Preferences Stored:
- **Chart Type**: line, bar, scatter, etc.
- **Sensor Type Filter**: all, temperature, humidity, etc.
- **Time Range Filter**: all, 24h, 7d, 30d, etc.
- **Data Limit**: all, or specific number of records

### Fallback Mechanism:
- **Primary Storage**: SQL database via API
- **Fallback Storage**: localStorage (if API fails)
- **Migration**: Automatically attempts to load from localStorage if database is empty

### Error Handling:
- **API Failures**: Falls back to localStorage
- **Database Errors**: Logged and handled gracefully
- **Network Issues**: Continues to function with localStorage

## API Endpoints

### General User Preferences:
```
GET    /api/user_preferences                    # Get all preferences
GET    /api/user_preferences/{name}             # Get specific preference
POST   /api/user_preferences/{name}             # Set specific preference
```

### Chart-Specific Preferences:
```
GET    /api/user_preferences/chart/{entry_id}   # Get chart preferences
POST   /api/user_preferences/chart/{entry_id}   # Set chart preferences  
DELETE /api/user_preferences/chart/{entry_id}   # Delete chart preferences
```

## Request/Response Format

### Set Preference:
```json
POST /api/user_preferences/test_setting
{
  "value": "some_value"
}
```

### Set Chart Preferences:
```json
POST /api/user_preferences/chart/22
{
  "chartType": "bar",
  "sensorType": "temperature", 
  "timeRange": "24h",
  "dataLimit": "100"
}
```

### Response Format:
```json
{
  "success": true,
  "message": "Preference saved successfully",
  "preference_name": "test_setting",
  "preference_value": "some_value"
}
```

## Testing

### API Testing:
- Created `test_user_preferences_api.py` 
- Tests all CRUD operations
- Verifies data persistence
- Tests error handling

### Test Results:
```
✅ Get initial preferences (defaults)
✅ Set chart preferences 
✅ Get saved preferences (persisted)
✅ Set general preference
✅ Get general preference
✅ Delete chart preferences
✅ Get preferences after deletion (defaults)
```

## Benefits

1. **Data Persistence**: Preferences survive browser cache clears
2. **Cross-Device Sync**: Same preferences across different browsers/devices
3. **Centralized Storage**: All user preferences in one database table
4. **Backup/Recovery**: Preferences included in database backups
5. **Admin Visibility**: Admins can view/modify user preferences if needed
6. **Graceful Degradation**: Falls back to localStorage if database unavailable

## Future Enhancements

1. **User-Specific Preferences**: Add user authentication and user-specific preferences
2. **Preference Categories**: Organize preferences by category/module
3. **Default Preference Templates**: Admin-defined default preference sets
4. **Preference Import/Export**: Allow users to backup/restore their preferences
5. **Preference Validation**: Add validation rules for preference values
6. **Preference History**: Track changes to preferences over time

## Migration Notes

- **Backward Compatible**: Existing localStorage preferences still work as fallback
- **Automatic Migration**: Old localStorage preferences automatically saved to database on first use
- **No User Impact**: Migration is transparent to end users
- **Performance**: Database queries are fast and cached where appropriate
