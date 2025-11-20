# Milestone Module Enhancement - Commenced Date Feature

## Overview
Enhanced the milestone module to use a separate `commenced_at` date field instead of `created_at` for milestone calculations. This allows entries to track when work actually started separately from when the entry was created in the system.

## Changes Made

### 1. Database Schema (`migrations/add_commenced_at_to_entry.py`)
- **Added:** New migration file to add `commenced_at` column to Entry table
- **Column Type:** TEXT (ISO datetime string)
- **Default Behavior:** For existing entries, automatically populated with `created_at` value
- **Index:** Created `idx_entry_commenced_at` for query performance

### 2. Backend API Updates

#### `app/api/milestone_api.py`
- **Function:** `update_entry_intended_end_date()`
  - Modified to use `commenced_at` if available, falling back to `created_at` if null
  - Updated query to fetch both `commenced_at` and `created_at`
  - Improved logging to show which date is being used for calculations

#### `app/api/entry_api.py`
- **POST `/api/entries`**
  - Added `commenced_at` parameter handling
  - Updated INSERT statement to include commenced_at field
  
- **PATCH `/api/entries/<entry_id>`**
  - Added support for updating `commenced_at` field
  - Field can be updated independently of other date fields

- **GET endpoints**
  - Updated all entry retrieval queries to include `commenced_at`
  - Added `commenced_at` to JSON responses:
    - `GET /api/entries`
    - `GET /api/entries/<entry_id>`
    - `GET /api/entries/sensor-enabled`

#### `app/routes/main_routes.py`
- **Function:** `entry_detail_v2()`
  - Updated entry query to include `commenced_at`
  - Added `commenced_at` to entry_data dictionary passed to template

### 3. Frontend Updates

#### `app/templates/sections/_header_section.html`
- **Display Mode:**
  - Added "Commenced:" field showing commenced_at date (if set)
  - Displays between "Created On" and "Intended End" dates
  
- **Edit Mode:**
  - Added "Commenced Date" input field with date picker
  - Includes helper text: "Start date for milestone calculations"
  - Positioned before Intended End Date field
  
- **JavaScript:**
  - Added `commencedAtInput` element reference
  - Added `commencedAt` to `originalValues` for cancel functionality
  - Updated save function to include `commenced_at` in PATCH request
  - Added reset functionality for cancelled edits

#### `app/templates/sections/_timeline_section.html`
- **Progress Display:**
  - Updated start date display to show "Started:" instead of "Created:" when commenced_at is set
  - Falls back to "Created:" when commenced_at is null
  
- **JavaScript:**
  - Added `commencedAt` to entryData object
  - Falls back to `created_at` if `commenced_at` is not set
  - Updated `renderMilestones()` function to use `entryData.commencedAt`
  - Updated `buildStatusProgression()` function to use `entryData.commencedAt`

## Benefits

1. **Accurate Milestone Tracking:** Milestones now calculate from when work actually started, not when the entry was created
2. **Backward Compatible:** Existing entries work correctly by falling back to created_at
3. **Flexible Date Management:** Users can set commenced date different from creation date
4. **Better Project Planning:** Separates system record creation from actual project commencement

## Usage

### Setting Commenced Date
1. Navigate to an entry detail page
2. Click "Edit" button
3. Scroll to the "Dates" section
4. Set the "Commenced Date" field
5. Click "Save"

### Milestone Calculations
- If `commenced_at` is set: `intended_end_date = commenced_at + sum(milestone_durations)`
- If `commenced_at` is null: `intended_end_date = created_at + sum(milestone_durations)`

## API Examples

### Create Entry with Commenced Date
```bash
curl -X POST /api/entries \
  -H "Content-Type: application/json" \
  -d '{
    "title": "New Project",
    "entry_type_id": 1,
    "commenced_at": "2025-01-15T00:00:00Z"
  }'
```

### Update Commenced Date
```bash
curl -X PATCH /api/entries/123 \
  -H "Content-Type: application/json" \
  -d '{
    "commenced_at": "2025-01-20T00:00:00Z"
  }'
```

### Get Entry with Commenced Date
```bash
curl /api/entries/123
```

Response:
```json
{
  "id": 123,
  "title": "Project",
  "created_at": "2025-01-10T12:00:00Z",
  "commenced_at": "2025-01-15T00:00:00Z",
  "intended_end_date": "2025-02-15T00:00:00Z",
  ...
}
```

## Migration

The migration is **non-destructive** and **automatically applied** on container startup:

```bash
# Manual migration (if needed)
docker exec template python3 /app/migrations/add_commenced_at_to_entry.py

# Rollback (removes only the index, keeps the column)
docker exec template python3 /app/migrations/add_commenced_at_to_entry.py --down
```

## Testing Checklist

- [x] Migration runs successfully
- [x] Existing entries have commenced_at populated with created_at
- [x] New entries can be created with commenced_at
- [x] Commenced date can be edited via UI
- [x] Milestone calculations use commenced_at when available
- [x] Timeline displays correct start date
- [x] API returns commenced_at in all entry endpoints
- [ ] Verify milestone end date calculations are accurate
- [ ] Test with entries that have no commenced_at (should fallback)

## Future Enhancements

1. **Bulk Update:** Add ability to bulk set commenced dates for multiple entries
2. **Validation:** Add validation to ensure commenced_at is not before created_at
3. **Reports:** Update reporting features to optionally use commenced_at
4. **Notifications:** Consider notifications when commenced_at is approaching but entry hasn't started
