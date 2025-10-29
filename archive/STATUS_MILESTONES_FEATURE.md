# Status Milestones Feature

## Overview

The Status Milestones feature extends the time-based progress bar to show **intended status changes** during the active period of an entry. This allows you to plan and visualize when you expect status transitions to occur between entry creation and the intended end date.

## Implementation Date
October 28, 2025

## Visual Concept

The feature adds milestone markers to the time progress bar (the second bar that shows time-based progress):

```
┌──────────────────────────────────────────────────────────────┐
│ Status History (Actual Changes - Bar 1)                       │
│ [████Active████][██In Progress██][█Current█]                 │
├──────────────────────────────────────────────────────────────┤
│                                                                │
│ Time Progress with Milestones (Bar 2)                        │
│ Created: Oct 1              75% Complete    Target: Nov 1     │
│ ████████████████████◆░░░░░◆░░░░░░░░▼                         │
│ │              │     │    │     │    │                        │
│ Start          │  Primary  │ Bottling  Today                 │
│             Ferment  Complete                                 │
│                                                                │
│ Legend:                                                        │
│ ◆ = Milestone marker (intended status change)                │
│ ▼ = "Today" marker                                           │
│ ░ = Remaining time                                            │
└──────────────────────────────────────────────────────────────┘
```

## How It Works

### 1. Database Structure

**New Table: `EntryStateMilestone`**
```sql
CREATE TABLE EntryStateMilestone (
    id INTEGER PRIMARY KEY,
    entry_id INTEGER NOT NULL,
    target_state_id INTEGER NOT NULL,
    target_date TEXT NOT NULL,
    notes TEXT,
    is_completed INTEGER DEFAULT 0,
    completed_at TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (entry_id) REFERENCES Entry(id) ON DELETE CASCADE,
    FOREIGN KEY (target_state_id) REFERENCES EntryState(id) ON DELETE CASCADE
)
```

**Fields:**
- `entry_id`: Which entry this milestone belongs to
- `target_state_id`: The intended status at this milestone
- `target_date`: When you expect to reach this status
- `notes`: Optional notes about the milestone
- `is_completed`: Whether the milestone has been reached
- `completed_at`: When it was actually completed

### 2. API Endpoints

#### Get Milestones
```http
GET /api/entries/{entry_id}/milestones
```

**Response:**
```json
[
  {
    "id": 1,
    "entry_id": 5,
    "target_state_id": 3,
    "target_state_name": "Secondary Ferment",
    "target_state_color": "#0d6efd",
    "target_date": "2025-11-15",
    "notes": "Transfer to secondary fermenter",
    "is_completed": false,
    "completed_at": null
  }
]
```

#### Create Milestone
```http
POST /api/entries/{entry_id}/milestones
Content-Type: application/json

{
  "target_state_id": 3,
  "target_date": "2025-11-15",
  "notes": "Transfer to secondary fermenter"
}
```

#### Update Milestone
```http
PUT /api/entries/{entry_id}/milestones/{milestone_id}
Content-Type: application/json

{
  "target_date": "2025-11-20",
  "notes": "Updated timeline"
}
```

#### Delete Milestone
```http
DELETE /api/entries/{entry_id}/milestones/{milestone_id}
```

### 3. Visual Markers

Each milestone appears on the time progress bar as:

**Appearance:**
- **Symbol**: Diamond (◆) above the bar
- **Color**: Matches the target state color
- **Position**: Calculated based on the target date within the timeline
- **Tooltip**: Shows state name, date, and notes on hover

**States:**
- **Active milestone**: Bright colored diamond
- **Reached milestone**: Checkmark (✓), semi-transparent
- **Completed milestone**: Green checkmark

### 4. User Interface

**Managing Milestones:**

1. Click **"Manage Milestones"** button below the time progress bar
2. Modal opens showing:
   - List of existing milestones
   - Form to add new milestones
3. To add a milestone:
   - Select target status from dropdown
   - Choose target date (between created and intended end)
   - Optionally add notes
   - Click "Add Milestone"

**Viewing Milestones:**
- Milestones appear automatically on the time progress bar
- Hover over any diamond marker to see details
- Click a marker to see full information

## Use Cases

### Homebrewing Example

For a beer entry with timeline Oct 1 - Nov 1:

1. **Primary Ferment Complete** - Oct 15
   - Milestone: When primary fermentation should finish
   - Action: Transfer to secondary

2. **Secondary Ferment Complete** - Oct 25
   - Milestone: When secondary fermentation should finish
   - Action: Begin bottling

3. **Bottling Complete** - Oct 28
   - Milestone: When all bottles should be filled
   - Action: Begin carbonation

4. **Ready to Drink** - Nov 1 (intended end)
   - Automatically marked by intended_end_date

### Project Management Example

For a project with timeline Jan 1 - Mar 31:

1. **Planning Complete** - Jan 15
2. **Development Start** - Jan 20
3. **Alpha Release** - Feb 15
4. **Beta Release** - Mar 1
5. **Final Release** - Mar 31

## Features

### ✅ Implemented

- [x] Database table for storing milestones
- [x] Full CRUD API endpoints
- [x] Visual markers on time progress bar
- [x] Color-coded markers matching target states
- [x] Hover tooltips with details
- [x] Management modal for adding/editing/deleting
- [x] Automatic positioning based on dates
- [x] Integration with EntryState configuration

### 🔄 Planned Enhancements

- [ ] Bulk milestone creation from templates
- [ ] Automatic milestone completion detection
- [ ] Milestone notifications (ntfy integration)
- [ ] Historical milestone tracking (actual vs planned)
- [ ] Drag-and-drop milestone repositioning
- [ ] Milestone dependencies/ordering
- [ ] Export milestones to calendar

## Technical Details

### CSS Classes

```css
.time-progress-milestone {
    /* Vertical marker line */
    position: absolute;
    width: 2px;
    background: var(--milestone-color);
    z-index: 2;
}

.time-progress-milestone::before {
    /* Diamond symbol ◆ */
    content: '◆';
    font-size: 12px;
    color: var(--milestone-color);
}

.time-progress-milestone::after {
    /* Hover tooltip */
    content: attr(data-label);
    opacity: 0;
    /* Shows on hover */
}

.time-progress-milestone.milestone-reached {
    /* Styling for passed milestones */
    opacity: 0.5;
}
```

### JavaScript Functions

| Function | Purpose |
|----------|---------|
| `loadAndRenderMilestones()` | Fetch milestones from API |
| `renderMilestones(milestones)` | Create visual markers on progress bar |
| `showMilestoneDetails(milestone)` | Display milestone information |
| `openMilestoneModal()` | Show milestone management UI |
| `addMilestone()` | Create new milestone via API |
| `deleteMilestone(id)` | Remove milestone via API |

### Position Calculation

Milestones are positioned on the time progress bar using:

```javascript
const startDate = new Date(entry.created_at);
const endDate = new Date(entry.intended_end_date);
const milestoneDate = new Date(milestone.target_date);

const totalDuration = endDate - startDate;
const milestoneTime = milestoneDate - startDate;
const position = (milestoneTime / totalDuration) * 100;

marker.style.left = `${position}%`;
```

## Integration

### Requirements

- Entry must have `show_end_dates = true`
- Entry must have valid `intended_end_date`
- EntryState table must exist (for target states)

### Conditional Display

```html
{% if entry.show_end_dates and entry.intended_end_date %}
    <!-- Milestone features only shown when timeline exists -->
{% endif %}
```

## Migration

To add this feature to an existing installation:

```bash
docker exec -it template python migrations/add_entry_state_milestones.py
```

This creates the `EntryStateMilestone` table and indexes.

## Files Modified

1. **Database Migration**
   - `/migrations/add_entry_state_milestones.py` - Creates table

2. **API**
   - `/app/api/milestone_api.py` - CRUD endpoints
   - `/app/__init__.py` - Register blueprint

3. **UI**
   - `/app/templates/sections/_timeline_section.html`
     - CSS for milestone markers
     - JavaScript for fetching/rendering
     - Modal for milestone management
     - "Manage Milestones" button

## Benefits

### Planning
- Visualize expected workflow progression
- Set clear expectations for status changes
- Track whether you're ahead or behind schedule

### Communication
- Share timeline with stakeholders
- Show planned transition points
- Make progress transparent

### Analysis
- Compare actual vs planned transitions
- Identify process bottlenecks
- Improve future planning accuracy

## Example Usage

### Creating Entry with Milestones

1. Create entry with intended end date
2. Click "Manage Milestones" button
3. Add milestones for each expected status change:
   - Select status
   - Set target date
   - Add notes
4. Milestones appear on time progress bar
5. As entry progresses, milestones show if you're on track

### Monitoring Progress

- **Green markers ahead**: Future milestones
- **Semi-transparent markers**: Passed milestones
- **Checkmarks**: Completed milestones
- **Diamond position vs "Today" marker**: Shows if on schedule

## Conclusion

Status Milestones transform the time progress bar from a simple duration indicator into a comprehensive project planning tool. By visualizing intended status changes alongside actual progress, users can better plan, communicate, and track their workflow over time.

---

**Status:** ✅ **Ready for Testing!**  
**Complexity:** Medium-High  
**Maintainability:** High  
**User Value:** ⭐⭐⭐⭐⭐

---

**End of Status Milestones Feature Documentation**
