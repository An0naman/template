# Enabled Types Tab Implementation

## Overview
Implemented functionality for the "Enabled Types" tab in the Sensor Configuration modal to behave like the manage_sensors page for that entry type.

## Changes Made

### 1. Backend API Enhancement
**File**: `app/api/entry_api.py`

- Added new GET endpoint `/api/entries/<int:entry_id>` to retrieve single entry data including:
  - Entry details (id, title, description, dates, status)
  - Entry type information (entry_type_id, entry_type_label, entry_type_name)
  - Sensor configuration (has_sensors, enabled_sensor_types)

### 2. Frontend JavaScript Functions
**File**: `app/static/js/sections/_sensors_functions.js`

Added two new functions:

#### `populateEnabledSensorTypes()`
- Fetches all available sensor types from system parameters
- Loads current entry's entry type and enabled sensor types
- Builds a checkbox list of all sensor types with current selections
- Displays loading states and error handling
- Includes a "Save" button to persist changes

#### `saveEnabledSensorTypes()`
- Collects selected sensor types from checkboxes
- Retrieves entry's entry_type_id
- Updates the entry type's enabled_sensor_types via PATCH API
- Reloads sensor types and sensor data to reflect changes
- Shows success/error notifications

Both functions are exposed globally for template access.

### 3. Modal Template Enhancement
**File**: `app/templates/sections/_sensors_modals.html`

#### Updated "Enabled Types" Tab Content:
- Added informative alert explaining the feature
- Created scrollable container for sensor type checkboxes
- Added loading state indicator
- Removed placeholder "Add Custom Type" button

#### Added Modal Event Listener:
- Wired up Bootstrap modal `show.bs.modal` event
- Automatically calls `populateEnabledSensorTypes()` when modal opens
- Ensures fresh data is loaded each time the configuration modal is accessed

## Features

### User Experience
1. **Easy Access**: Click the gear icon in the sensor section header to open configuration
2. **Visual Feedback**: See which sensor types are currently enabled with checkboxes
3. **Instant Updates**: Changes apply immediately and reload relevant data
4. **Error Handling**: Clear error messages if something goes wrong
5. **Loading States**: Visual indicators during data fetching

### Functionality Parity with manage_sensors.html
- ✅ Displays all available sensor types from system
- ✅ Shows current enabled status with checkboxes
- ✅ Allows toggling sensor types on/off
- ✅ Saves changes to entry type configuration
- ✅ Updates affect all entries of that type
- ✅ Handles empty states (no sensor types discovered yet)
- ✅ Provides informative messages and feedback

## Technical Details

### API Flow
```
1. User opens configuration modal
2. Modal triggers populateEnabledSensorTypes()
3. Fetch system sensor types: GET /api/system_params
4. Fetch entry data: GET /api/entries/{entry_id}
5. Display checkboxes with current selections
6. User modifies selections and clicks Save
7. Execute saveEnabledSensorTypes()
8. Update entry type: PATCH /api/entry_types/{entry_type_id}
9. Reload sensor types and data
10. Show success notification
```

### Data Structure
- System sensor types stored as comma-separated string in SystemParameters
- Entry type enabled_sensor_types stored as comma-separated string in EntryType table
- JavaScript parses strings into arrays for checkbox manipulation
- Saves arrays back as comma-separated strings

## Benefits

1. **Centralized Control**: Configure sensor types without leaving the entry page
2. **Context Aware**: Changes apply to the entry type, affecting all related entries
3. **User Friendly**: No need to navigate to separate settings page
4. **Consistent UX**: Matches behavior of manage_sensors page
5. **Real-time Updates**: Immediate reflection of changes in UI

## Testing Checklist

- [ ] Open an entry with sensor data enabled
- [ ] Click the gear icon to open sensor configuration
- [ ] Verify "Enabled Types" tab loads with checkboxes
- [ ] Verify current enabled types are checked
- [ ] Toggle some sensor types on/off
- [ ] Click "Save Enabled Types"
- [ ] Verify success notification appears
- [ ] Verify sensor type selector updates
- [ ] Create new entry of same type, verify same sensor types available
- [ ] Test with entry type that has no sensor types enabled
- [ ] Test error handling (disconnect network, etc.)

## Future Enhancements

1. Add inline sensor type creation (currently requires manage_sensor_types page)
2. Show count of existing data for each sensor type
3. Warn if disabling a sensor type that has existing data
4. Bulk enable/disable all sensor types
5. Export/import sensor type configurations between entry types
