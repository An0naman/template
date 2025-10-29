# Milestone Reordering - User Guide

## Overview
You can now manage the order of your status milestones directly in the modal interface.

## How to Reorder Milestones

### Using the Modal Interface
1. Click **"Manage Milestones"** button on the timeline section
2. In the modal, you'll see all existing milestones listed in order (#1, #2, #3, etc.)
3. Each milestone has four buttons on the right:
   - **✏️ Edit** - Click to edit the duration (days) inline
   - **⬆️ Up Arrow** - Move this milestone one position earlier
   - **⬇️ Down Arrow** - Move this milestone one position later  
   - **🗑️ Delete** - Remove this milestone

### Editing Duration
1. Click the **✏️ Edit** button next to a milestone
2. The duration changes to an input field
3. Enter the new number of days (must be ≥ 1)
4. Click **✓** to save or **✗** to cancel
5. Timeline and cumulative days update automatically

### How Ordering Works
- Milestones are displayed in sequential order (#1, #2, #3...)
- Each milestone has a **duration** (e.g., 7 days)
- The timeline position is **cumulative**:
  - Milestone #1 (5 days) → ends at day 5
  - Milestone #2 (7 days) → ends at day 12 (5+7)
  - Milestone #3 (3 days) → ends at day 15 (5+7+3)

### What Happens When You Reorder
- ✅ **Smooth update** - No page reload, the modal stays open
- ✅ **Timeline updates** - The planned status timeline re-renders immediately
- ✅ **Order badges update** - Numbers (#1, #2, #3) adjust automatically
- ✅ **Cumulative days recalculate** - "ends day X" labels update

### What Happens When You Edit Duration
- ✅ **Instant feedback** - Click edit → change value → save
- ✅ **Timeline redraws** - Width of milestone segments adjust to new duration
- ✅ **Cumulative recalculation** - All "ends day X" labels for subsequent milestones update
- ✅ **Validation** - Duration must be at least 1 day

## Example Workflow

**Scenario:** You have milestones for Brewing → Fermenting → Conditioning

1. Initially ordered:
   - #1 Brewing (2 days, ends day 2)
   - #2 Fermenting (14 days, ends day 16)
   - #3 Conditioning (7 days, ends day 23)

2. You realize Conditioning should come before Fermenting
   - Click ⬆️ on **Conditioning** milestone
   - New order instantly updates:
     - #1 Brewing (2 days, ends day 2)
     - #2 Conditioning (7 days, ends day 9)  
     - #3 Fermenting (14 days, ends day 23)

3. You realize Fermenting should actually be 21 days instead of 14
   - Click ✏️ **Edit** on Fermenting
   - Change duration from 14 to 21
   - Click ✓ to save
   - Timeline updates:
     - #1 Brewing (2 days, ends day 2)
     - #2 Conditioning (7 days, ends day 9)  
     - #3 Fermenting (21 days, ends day 30) ← updated!

4. Timeline bars re-render with the new order, colors, and durations

## Technical Details

### Database Schema
```sql
CREATE TABLE EntryStateMilestone (
    id INTEGER PRIMARY KEY,
    entry_id INTEGER NOT NULL,
    target_state_id INTEGER NOT NULL,
    target_state_name TEXT,
    target_state_color TEXT,
    order_position INTEGER NOT NULL,  -- Sequential: 1, 2, 3...
    duration_days INTEGER NOT NULL,   -- How long this status lasts
    notes TEXT,
    is_completed BOOLEAN DEFAULT 0,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)
```

### API Endpoints
- **GET** `/api/entries/{id}/milestones` - Fetch all milestones (sorted by order_position)
- **POST** `/api/entries/{id}/milestones` - Create new milestone
- **PUT** `/api/entries/{id}/milestones/{milestone_id}` - Update order_position or duration_days
- **DELETE** `/api/entries/{id}/milestones/{milestone_id}` - Remove milestone

### Frontend Functions
- `moveMilestone(id, currentOrder, direction)` - Moves milestone up/down
- `editDuration(id)` - Shows inline duration editor
- `saveDuration(id)` - Saves new duration via API
- `cancelEditDuration(id, originalValue)` - Cancels edit and restores original
- `refreshModalMilestonesList()` - Updates modal list without reload
- `loadAndRenderMilestones()` - Re-renders timeline progress bars
- `renderMilestones(milestones)` - Draws milestone segments on timeline

## Improvements Made

### Issue #1: Modal Reload Flash
**Before:** Entire modal closed and reopened when reordering  
**After:** Only the milestone list updates in-place (smooth, no flash)

### Issue #2: Timeline Not Updating
**Before:** Timeline didn't show new order after reordering  
**After:** `loadAndRenderMilestones()` is called after every change to re-render the timeline

## Tips
- Use **duration** instead of absolute dates - milestones calculate cumulative positions
- Keep milestones in the order you expect the entry to progress
- You can delete and re-add if you make a mistake
- The "ends day X" label helps you visualize the cumulative timeline

---

**Last Updated:** October 29, 2025  
**Feature:** Status Milestone Ordering & Management
