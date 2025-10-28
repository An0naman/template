# Time-Based Progress Bar Feature

## Overview
Added a secondary progress bar below the status progression bar that visualizes the intended timeline, making it easy to see time-based progress and overdue status at a glance.

## Implementation Date
October 28, 2025

## Visual Design

### Two-Bar Layout
```
┌──────────────────────────────────────────────┐
│ STATUS PROGRESSION BAR (40px height)         │
│ [Status A][Status B][Status C][Current]      │
├──────────────────────────────────────────────┤
│ TIME PROGRESS BAR (20px height)              │
│ ████████████████████▼░░░░░░░░                │
│                     ↑                         │
│                   Today                       │
└──────────────────────────────────────────────┘
```

### Time Progress Bar Components

1. **Track (Background)**
   - Light gray background
   - Full width (100%)
   - Height: 20px (half of status bar)
   - Rounded corners
   - Inset shadow for depth

2. **Progress Fill**
   - Gradient color from green → cyan → yellow → red
   - Width: 0-100% based on time elapsed
   - **Normal**: Multi-color gradient showing progress
   - **Overdue**: Solid red (#dc3545)

3. **"Today" Marker**
   - White vertical line (3px wide)
   - Black border for visibility
   - Position: Percentage of elapsed time
   - Can exceed 100% (shows at 100% mark)
   - Hover tooltip shows status

## Color Gradient Logic

### Normal Progress (0-100%)
```css
linear-gradient(90deg, 
    #28a745 0%,    /* Green - Early (0-50%) */
    #20c997 50%,   /* Teal - Mid (50-75%) */
    #0dcaf0 75%,   /* Cyan - Approaching (75-90%) */
    #ffc107 90%,   /* Yellow - Warning (90-100%) */
    #dc3545 100%   /* Red - At deadline */
)
```

### Overdue (>100%)
- Fill becomes **solid red**
- Marker moves to 100% position (right edge)
- Tooltip shows "X days overdue"

## States & Behaviors

### State 1: Early Progress (0-50%)
```
Created: 2025-10-01  25% Complete  Target: 2025-10-30
┌──────────────────────────────────────────────┐
│ [Status Segments]                            │
├──────────────────────────────────────────────┤
│ █████▼░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │
│      ↑ Today (21 days remaining)             │
└──────────────────────────────────────────────┘
```
- Fill: Green color
- Marker: Early position
- Tooltip: "Today (X days remaining)"

### State 2: Mid Progress (50-75%)
```
Created: 2025-10-01  60% Complete  Target: 2025-10-30
┌──────────────────────────────────────────────┐
│ [Status Segments]                            │
├──────────────────────────────────────────────┤
│ ████████████████████▼░░░░░░░░░░░░░░░░░░░░░░ │
│                     ↑ Today (12 days remaining)
└──────────────────────────────────────────────┘
```
- Fill: Teal/cyan gradient
- Marker: Mid position
- Tooltip: "Today (X days remaining)"

### State 3: Approaching Deadline (90-99%)
```
Created: 2025-10-01  95% Complete  Target: 2025-10-30
┌──────────────────────────────────────────────┐
│ [Status Segments]                            │
├──────────────────────────────────────────────┤
│ ███████████████████████████████████████▼░░░░ │
│                                        ↑ Today (2 days remaining)
└──────────────────────────────────────────────┘
```
- Fill: Yellow color (warning)
- Marker: Near end
- Tooltip: "Today (X days remaining)"

### State 4: Target Reached (100%)
```
Created: 2025-10-01  ✓ Target reached!  Target: 2025-10-30
┌──────────────────────────────────────────────┐
│ [Status Segments]                            │
├──────────────────────────────────────────────┤
│ ████████████████████████████████████████████▼│
│                                             ↑ Today (target reached!)
└──────────────────────────────────────────────┘
```
- Fill: 100% width, ends in red
- Marker: At right edge
- Tooltip: "Today (target reached!)"

### State 5: Overdue (>100%)
```
Created: 2025-10-01  ⚠️ 104% - OVERDUE  Target: 2025-10-26
┌══════════════════════════════════════════════┐ ← RED BORDER
│ [Status Segments with stripes]              │
├──────────────────────────────────────────────┤
│ ████████████████████████████████████████████▼│ ← SOLID RED
│                                             ↑ Today (2 days overdue)
└──────────────────────────────────────────────┘
```
- Fill: **Solid red** (100% width)
- Marker: At right edge, red border
- Tooltip: "Today (X days overdue)"
- Status bar above also shows red border + stripes

## Technical Implementation

### HTML Structure
```html
<div id="timeProgressBar" class="time-progress-bar mt-2">
    <div class="time-progress-track">
        <div id="timeProgressFill" class="time-progress-fill"></div>
        <div id="timeProgressMarker" class="time-progress-marker" title="Today"></div>
    </div>
</div>
```

### CSS Styles
```css
.time-progress-track {
    height: 20px;  /* Half the status bar height */
    background: rgba(0, 0, 0, 0.1);
    border-radius: 0.25rem;
    position: relative;
}

.time-progress-fill {
    height: 100%;
    background: linear-gradient(...); /* Color gradient */
    transition: width 0.5s ease;
}

.time-progress-fill.overdue {
    background: #dc3545; /* Solid red when overdue */
}

.time-progress-marker {
    position: absolute;
    width: 3px;
    background: #fff;
    border: 2px solid #000;
    /* Positioned via JavaScript */
}
```

### JavaScript Logic
```javascript
function calculateProgress() {
    const percentage = (daysElapsed / totalDays) * 100;
    const fillPercentage = Math.min(100, percentage);
    const markerPosition = Math.min(100, percentage);
    
    // Update fill bar (capped at 100%)
    timeProgressFill.style.width = fillPercentage + '%';
    
    // Update marker (capped at 100%)
    timeProgressMarker.style.left = markerPosition + '%';
    
    // Overdue styling
    if (daysRemaining < 0) {
        timeProgressFill.classList.add('overdue');
        timeProgressMarker.style.borderColor = '#dc3545';
        timeProgressMarker.title = `Today (${Math.abs(daysRemaining)} days overdue)`;
    }
}
```

## Conditional Display

Only shown when:
1. Entry has `show_end_dates = true`
2. Entry has valid `intended_end_date`

If no end date, only status progression bar is shown.

## Interaction Features

### Hover Tooltip
- Marker shows tooltip on hover
- Content changes based on state:
  - "Today (X days remaining)" - Normal
  - "Today (target reached!)" - Exactly on time
  - "Today (X days overdue)" - Past deadline

### Visual Feedback
- Smooth transitions (0.5s) when updating
- Gradient changes color as deadline approaches
- Marker border color changes when overdue

## Comparison: Status Bar vs Time Bar

| Feature | Status Progression Bar | Time Progress Bar |
|---------|----------------------|-------------------|
| **Height** | 40px | 20px (half) |
| **Purpose** | Show status changes over time | Show time-based progress |
| **Segments** | Multiple colored status segments | Single gradient fill |
| **Colors** | Dynamic from EntryState config | Fixed gradient (green→red) |
| **Marker** | None | "Today" marker |
| **Overdue** | Red border + stripes | Solid red fill |

## Benefits

### Visual Clarity
- ✅ Two distinct but complementary views
- ✅ Easy to see status vs time progress
- ✅ "Today" marker shows exact current position
- ✅ Overdue status unmistakable

### User Understanding
- ✅ Status bar: "What statuses has this been in?"
- ✅ Time bar: "How much time has elapsed?"
- ✅ Both together: Complete picture of progress

### Information Density
- ✅ Compact design (only 20px tall)
- ✅ Doesn't clutter interface
- ✅ Rich information at a glance

## Files Modified
- `/app/templates/sections/_timeline_section.html`
  - Added time progress bar HTML
  - Added CSS for track, fill, and marker
  - Updated `calculateProgress()` to render time bar
  - Added gradient color logic
  - Added overdue detection

## Related Features
- Unified Status Progress Bar
- Overdue Indicator Feature
- Dynamic Status Colors
- Time-based Progress Tracking

## Future Enhancements
- [ ] Milestone markers on timeline (e.g., 25%, 50%, 75%)
- [ ] Click on marker to see exact date/time
- [ ] Draggable marker for "what if" scenarios
- [ ] Multiple targets (min/max dates)
- [ ] Predicted completion date based on status velocity
- [ ] Historical comparison (compare multiple entries)
- [ ] Export timeline as image

## Accessibility
- Marker has visible border (black/red) for contrast
- Tooltip provides textual information
- Color gradient supplemented by position
- Works without relying on color alone

## Performance
- CSS gradients (no images)
- Smooth transitions (GPU-accelerated)
- Minimal DOM updates
- No extra API calls

## Conclusion
The time-based progress bar provides a complementary view to the status progression bar, making it immediately clear how much time has elapsed relative to the intended timeline. The "Today" marker and color gradient provide intuitive visual feedback, while the overdue state (solid red) makes deadline issues unmistakable.
