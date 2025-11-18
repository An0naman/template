# Status Trigger Enhancement - Automatic Date Setting

## Overview
Enhanced the entry status system to automatically set important date fields (`commenced_at` and `actual_end_date`) when specific statuses are applied to entries. This eliminates manual date entry and ensures consistent date tracking across the application.

## Features

### Status-Based Date Triggers
Each status/state can now be configured with two trigger flags:

1. **Sets Commenced Date** (`sets_commenced`)
   - When enabled, automatically populates `commenced_at` when this status is applied
   - Only sets the date if `commenced_at` is not already set
   - Useful for "In Progress", "Started", "Active" type statuses

2. **Sets Ended Date** (`sets_ended`)
   - When enabled, automatically populates `actual_end_date` when this status is applied
   - Only sets the date if `actual_end_date` is not already set
   - Useful for "Completed", "Finished", "Consumed" type statuses

## Changes Made

### 1. Database Schema (`migrations/add_status_triggers_to_entry_state.py`)
- **Added:** New migration file to add trigger columns to EntryState table
- **Columns Added:**
  - `sets_commenced` - INTEGER (0/1) boolean flag
  - `sets_ended` - INTEGER (0/1) boolean flag
- **Indexes:** Created partial indexes on both columns for performance
- **Default Values:** Both default to 0 (disabled)

### 2. Backend API Updates

#### `app/api/entry_api.py`
- **Function:** `update_entry()`
  - Modified to check status trigger flags when status changes
  - Queries EntryState table to check if new status has triggers enabled
  - Auto-sets `commenced_at` if trigger is enabled and field is null
  - Auto-sets `actual_end_date` if trigger is enabled and field is null
  - Logs automatic date setting for audit trail

#### `app/api/entry_state_api.py`
- **GET `/api/entry_types/<entry_type_id>/states`**
  - Added `sets_commenced` and `sets_ended` to response
  
- **POST `/api/entry_types/<entry_type_id>/states`**
  - Added support for `sets_commenced` and `sets_ended` parameters
  - Creates states with trigger configuration
  
- **PUT `/api/entry_types/<entry_type_id>/states/<state_id>`**
  - Added support for updating trigger flags
  - Allows enabling/disabling triggers on existing states

- **GET `/api/entries/<entry_id>/available_states`**
  - Includes trigger fields in available states response

### 3. Frontend Updates

#### `app/templates/manage_entry_types.html`
- **State Form:**
  - Added "Automatic Date Triggers" section with two checkboxes
  - "Sets Commenced Date" checkbox with descriptive icon and help text
  - "Sets Ended Date" checkbox with descriptive icon and help text
  
- **State List Display:**
  - Shows badges for states with triggers enabled
  - Blue "Commenced" badge with play icon for `sets_commenced`
  - Yellow "Ended" badge with flag icon for `sets_ended`
  
- **JavaScript:**
  - Updated `renderStates()` to display trigger badges
  - Updated `editState()` to load trigger values
  - Updated `saveState()` to include trigger flags in API calls

## Usage

### Configuring Status Triggers

1. Navigate to **Maintenance > Manage Entry Types**
2. Select an entry type
3. Click **"Manage States"**
4. Edit an existing state or create a new one
5. In the "Automatic Date Triggers" section:
   - Check **"Sets Commenced Date"** for statuses that indicate work has started
   - Check **"Sets Ended Date"** for statuses that indicate completion
6. Click **"Save State"**

### Example Configurations

#### Recipe/Brewing Entry Type
- **"Primary Fermentation"** → Sets Commenced ✓
- **"Secondary Fermentation"** → (no triggers)
- **"Bottled"** → (no triggers)
- **"Consumed"** → Sets Ended ✓

#### Project Entry Type
- **"Planning"** → (no triggers)
- **"In Progress"** → Sets Commenced ✓
- **"Testing"** → (no triggers)
- **"Completed"** → Sets Ended ✓

#### Task Entry Type
- **"To Do"** → (no triggers)
- **"Started"** → Sets Commenced ✓
- **"Done"** → Sets Ended ✓

### Behavior

When you change an entry's status to one with triggers:

1. **Commenced Trigger:**
   ```
   Entry status changes to "In Progress" (has sets_commenced = 1)
   → If commenced_at is NULL, sets it to current timestamp
   → If commenced_at already has a value, leaves it unchanged
   ```

2. **Ended Trigger:**
   ```
   Entry status changes to "Completed" (has sets_ended = 1)
   → If actual_end_date is NULL, sets it to current timestamp
   → If actual_end_date already has a value, leaves it unchanged
   ```

## Benefits

1. **Automatic Tracking:** Dates are set automatically, no manual entry needed
2. **Consistent Data:** All entries have proper start/end dates when appropriate
3. **Flexible Configuration:** Each entry type can have different trigger configurations
4. **Non-Intrusive:** Only sets dates if they're not already set
5. **Audit Trail:** Logged when automatic date setting occurs
6. **Better Analytics:** More complete date data enables better reporting and dashboards

## API Examples

### Create State with Triggers
```bash
curl -X POST /api/entry_types/1/states \
  -H "Content-Type: application/json" \
  -d '{
    "name": "In Progress",
    "category": "active",
    "color": "#007bff",
    "display_order": 1,
    "sets_commenced": true
  }'
```

### Update State to Add Trigger
```bash
curl -X PUT /api/entry_types/1/states/5 \
  -H "Content-Type: application/json" \
  -d '{
    "sets_ended": true
  }'
```

### Get States with Trigger Info
```bash
curl /api/entry_types/1/states
```

Response:
```json
[
  {
    "id": 1,
    "name": "Planning",
    "category": "active",
    "sets_commenced": false,
    "sets_ended": false
  },
  {
    "id": 2,
    "name": "In Progress",
    "category": "active",
    "sets_commenced": true,
    "sets_ended": false
  },
  {
    "id": 3,
    "name": "Completed",
    "category": "inactive",
    "sets_commenced": false,
    "sets_ended": true
  }
]
```

## Migration

The migration is **non-destructive** and **automatically applied** on container startup:

```bash
# Manual migration (if needed)
docker exec template python3 /app/migrations/add_status_triggers_to_entry_state.py

# Rollback (removes only the indexes, keeps the columns)
docker exec template python3 /app/migrations/add_status_triggers_to_entry_state.py --down
```

## Integration with Milestone System

The status triggers work seamlessly with the milestone system:

1. When a status with `sets_commenced = true` is applied:
   - Sets `commenced_at` automatically
   - Milestone calculations immediately use this as the start date
   - `intended_end_date` is recalculated based on milestone durations

2. When a status with `sets_ended = true` is applied:
   - Sets `actual_end_date` automatically
   - Entry is marked as completed
   - Progress tracking shows 100% completion

## Testing Checklist

- [x] Migration runs successfully
- [x] New columns exist in EntryState table
- [x] States can be created with trigger flags
- [x] States can be updated to enable/disable triggers
- [x] UI displays trigger checkboxes in state form
- [x] UI displays trigger badges in state list
- [x] API includes trigger fields in responses
- [ ] Commenced date is set when status changes to triggered state
- [ ] Ended date is set when status changes to triggered state
- [ ] Dates are NOT overwritten if already set
- [ ] Status change logging includes automatic date setting

## Future Enhancements

1. **Trigger Validation:** Warn if multiple states have `sets_commenced` enabled
2. **Undo Support:** Allow reverting automatic date changes
3. **Custom Triggers:** Support for custom date field triggers
4. **Notification Integration:** Send notifications when dates are auto-set
5. **Audit Log:** Detailed tracking of all automatic date changes
6. **Conditional Triggers:** Only set dates under certain conditions
