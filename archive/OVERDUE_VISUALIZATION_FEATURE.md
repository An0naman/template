# Overdue Days Visualization Feature

## Overview
Enhanced the time progress bar to visually display overdue days as an extension beyond the 100% mark, making it immediately clear how far past the deadline an entry is.

## Implementation Date
October 28, 2025

## Visual Design

### Normal State (On Track)
```
Target: 2025-10-30
┌────────────────────────────────────────┐
│ ████████████████▼░░░░░░░░░░░░░░░░░░░░▼│
│                 ↑ Today              ↑ Target
│                 60%                 100%
└────────────────────────────────────────┘
```
- Green → Yellow gradient fill
- "Today" marker at current position
- Target marker at 100%

### Overdue State (Past Deadline)
```
Target: 2025-10-26 (2 days ago)
┌────────────────────────────────────────┬──────┐
│ ████████████████████████████████████████▼▓▓▓▓▓▼│
│                                       ↑     ↑
│                                    Target Today
│                                     100%  108%
└────────────────────────────────────────┴──────┘
         Intended Timeline              Overdue
         (Green→Red Gradient)       (Red Stripes)
```
- Fill bar: 100% (full intended timeline with gradient)
- **Overdue extension**: Red diagonal stripes beyond 100%
- Target marker: Black line at 100%
- "Today" marker: Extends into overdue section with red border

## Three-Section Layout

### 1. Progress Fill (0-100%)
- **Purpose**: Shows intended timeline
- **Width**: Always 100% of track when overdue
- **Color**: Green → Yellow → Red gradient
- **Style**: Rounded left corners

### 2. Overdue Extension (100%+)
- **Purpose**: Shows days beyond deadline
- **Width**: Percentage of overdue days relative to total timeline
- **Color**: Red diagonal stripes (#dc3545)
- **Style**: Rounded right corners, shadow on left edge
- **Pattern**: 45° diagonal stripes for visibility

### 3. Target Marker (100%)
- **Purpose**: Shows exact intended end date
- **Position**: Always at 100% mark
- **Style**: Black vertical line (2px)
- **Icon**: ▼ above the line
- **Tooltip**: "Target: [date]"

## Calculation Logic

### Timeline Scaling
The key is that the track width represents different timespans depending on state:

**On Track: Track = Created to Intended End**
```javascript
const totalDays = 26; // Created to intended end
const fillPercentage = (daysElapsed / totalDays) * 100;
// Track width = 100% of intended timeline
```

**Overdue: Track = Created to Today**
```javascript
const overdueDays = 2; // Days past deadline
const totalDisplayDays = totalDays + overdueDays; // 28 days (created to today)
const intendedPercentage = (26 / 28) * 100; // 92.9% of track
const overduePercentage = (2 / 28) * 100;   // 7.1% of track
// Track width = 100% but represents created to today
```

### Visual Layout When Overdue
```
Track (100% width) = Created (Day 0) to Today (Day 28)
|←──────── 92.9% (Intended) ──────→|←─ 7.1% (Overdue) ─→|
|██████████████████████████████████|▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓|
 Day 0                            Day 26              Day 28
                                    ▲                   ▲
                                 Target               Today
```

## Progression Examples

### Day 1: Just Started (4% complete)
```
Track = 26 days (created to target)
┌────────────────────────────────────────┐
│ █▼░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░▼│
│  ↑                                    ↑
│ Today (25 days remaining)         Target
└────────────────────────────────────────┘
```

### Day 13: Halfway (50% complete)
```
Track = 26 days (created to target)
┌────────────────────────────────────────┐
│ ████████████████████▼░░░░░░░░░░░░░░░░▼│
│                     ↑                 ↑
│ Today (13 days remaining)         Target
└────────────────────────────────────────┘
```

### Day 24: Warning (92% complete)
```
Track = 26 days (created to target)
┌────────────────────────────────────────┐
│ ████████████████████████████████████▼░▼│
│                                     ↑ ↑
│ Today (2 days remaining)        Target
└────────────────────────────────────────┘
```

### Day 26: Target Reached (100%)
```
Track = 26 days (created to target)
┌────────────────────────────────────────┐
│ ████████████████████████████████████████▼
│                                         ↑
│                            Today = Target!
└────────────────────────────────────────┘
```

### Day 28: 2 Days Overdue
```
Track = 28 days (created to TODAY)
Intended = 26/28 = 92.9% | Overdue = 2/28 = 7.1%
┌────────────────────────────────────────┐
│ █████████████████████████████████████▼▓▓▼
│                                      ↑ ↑
│                                  Target Today
│                              (2 days overdue)
└────────────────────────────────────────┘
```

### Day 35: 9 Days Overdue
```
Track = 35 days (created to TODAY)
Intended = 26/35 = 74.3% | Overdue = 9/35 = 25.7%
┌────────────────────────────────────────┐
│ ██████████████████████████████▼▓▓▓▓▓▓▓▓▓▓▼
│                               ↑          ↑
│                           Target      Today
│                              (9 days overdue)
└────────────────────────────────────────┘
```

## Visual Elements

### Diagonal Stripe Pattern
```css
.time-progress-overdue {
    background: repeating-linear-gradient(
        45deg,
        #dc3545,      /* Red */
        #dc3545 10px,
        #a02a3a 10px, /* Darker red */
        #a02a3a 20px
    );
}
```
- **Purpose**: Makes overdue section distinct from progress fill
- **Angle**: 45° for classic "warning" appearance
- **Colors**: Alternating red shades for texture
- **Spacing**: 10px bands for visibility

### Target Date Marker
```
    ▼  ← Triangle indicator
    │  ← Black vertical line
    │
```
- Shows exact position of intended end date
- Stays fixed at 100% even when overdue
- Tooltip shows actual target date
- Provides clear reference point

### "Today" Marker Changes
- **Normal**: Black border, neutral color
- **Overdue**: Red border (#dc3545), danger color
- **Position**: Moves beyond 100% into overdue section
- **Tooltip**: Updates to show "X days overdue"

## Scale & Proportions

### Dynamic Track Scaling
The track width (100%) represents different time periods based on state:

**Normal State:**
- Track represents: Created → Intended End
- Fill percentage: Days elapsed / Total intended days
- Example: 13 of 26 days = 50% fill

**Overdue State:**
- Track represents: Created → **Today** (not intended end!)
- Fill percentage: Intended days / Total days to today
- Overdue percentage: Overdue days / Total days to today
- Example: 26 intended + 2 overdue = 28 total
  - Fill: 26/28 = 92.9%
  - Overdue: 2/28 = 7.1%

### Why This Approach?

**Problem with Fixed Width:**
If we kept the track as "created to intended end" and extended beyond 100%, very overdue entries would break the layout:
```
BAD: Entry 10 days overdue on 26-day timeline
┌──────────────────────────────────────────┬─────────────────┐
│ (138% total width - breaks container!)   │
└──────────────────────────────────────────┴─────────────────┘
```

**Solution with Dynamic Scaling:**
Track always = 100% width, but meaning changes:
```
GOOD: Same entry with dynamic scaling
┌────────────────────────────────────────┐
│ ███████████████████████████▼▓▓▓▓▓▓▓▓▓▓▓▼│
│ 72% fill           28% overdue         │
└────────────────────────────────────────┘
26/(26+10) = 72%    10/(26+10) = 28%
```

### Overdue Proportion Examples

**2 days overdue on 26-day timeline:**
- Total display: 28 days
- Intended: 92.9% of bar
- Overdue: 7.1% of bar
- **Visual**: Small red section

**13 days overdue on 26-day timeline:**
- Total display: 39 days  
- Intended: 66.7% of bar
- Overdue: 33.3% of bar
- **Visual**: Significant red section (1/3 of bar)

**26 days overdue on 26-day timeline:**
- Total display: 52 days
- Intended: 50% of bar
- Overdue: 50% of bar
- **Visual**: Red section as large as intended timeline!

## Maximum Display

To prevent extreme overdue from breaking layout:
```javascript
const markerPosition = 100 + overduePercentage;
timeProgressMarker.style.left = Math.min(markerPosition, 200) + '%';
```
- Caps "Today" marker at 200% (double the intended timeline)
- Overdue section can still grow beyond this
- Prevents marker from going off-screen

## Accessibility

### Multiple Visual Cues
1. **Color**: Red for overdue
2. **Pattern**: Diagonal stripes
3. **Position**: Extension beyond intended timeline
4. **Marker**: Visual indicator at current position
5. **Tooltip**: Text description with exact days

### Hover States
- **Target Marker**: Shows "Target: [date]" on hover
- **Today Marker**: Shows "Today (X days overdue)" on hover
- **Tooltips**: Provide textual information for screen readers

## Integration with Status Bar

### Combined View
```
┌─────────────────────────────────────────────┐
│ STATUS BAR (with red border + diagonal)     │
│ [Active][In Progress][Current]   ←Overdue   │
├─────────────────────────────────────────────┤
│ TIME BAR                                    │
│ ████████████████████████████████████▼▓▓▓▓▓▓▼│
│                                    ↑       ↑ │
└────────────────────────────────────┴───────┘
```

Both bars show overdue status:
- **Status Bar**: Red border, diagonal overlay on segments
- **Time Bar**: Red striped extension, target + today markers

## Files Modified
- `/app/templates/sections/_timeline_section.html`
  - Added `timeProgressOverdue` div for overdue extension
  - Added `timeProgressTarget` marker at 100%
  - Updated CSS with stripe pattern and positioning
  - Modified `calculateProgress()` to calculate overdue percentage
  - Updated marker positioning logic
  - Added conditional rendering for overdue vs normal states

## Technical Details

### HTML Structure
```html
<div class="time-progress-track">
    <div id="timeProgressFill"></div>     <!-- 0-100% -->
    <div id="timeProgressOverdue"></div>   <!-- 100%+ -->
    <div id="timeProgressTarget"></div>    <!-- At 100% -->
    <div id="timeProgressMarker"></div>    <!-- Today -->
</div>
```

### CSS Positioning
```css
.time-progress-fill {
    left: 0;
    max-width: 100%;
}

.time-progress-overdue {
    left: 100%;  /* Starts where fill ends */
    width: 0%;   /* Grows when overdue */
}

.time-progress-target {
    left: 100%;  /* Fixed at deadline */
}

.time-progress-marker {
    left: X%;    /* Moves from 0% to 200%+ */
}
```

## Benefits

### User Understanding
- ✅ **Immediate Recognition**: Overdue status is unmistakable
- ✅ **Proportional Awareness**: See how overdue relative to total timeline
- ✅ **Clear Reference**: Target marker shows intended deadline
- ✅ **Exact Information**: Tooltips provide precise day counts

### Visual Impact
- ✅ **Extends Track**: Shows problem is ongoing
- ✅ **Pattern Differentiation**: Stripes vs solid gradient
- ✅ **Color Coding**: Red indicates urgency
- ✅ **Dual Markers**: Today vs Target positions clear

## Future Enhancements
- [ ] Animate overdue section growth
- [ ] Add milestone markers (25%, 50%, 75%)
- [ ] Show grace period before "hard" overdue
- [ ] Different stripe patterns for severity levels
- [ ] Export timeline visualization as image
- [ ] Comparison view for multiple entries
- [ ] Predictive "at risk" indicator before overdue

## Conclusion
The overdue extension transforms the time progress bar from a simple completion indicator into a comprehensive deadline tracking tool. By visually extending the bar beyond 100%, users can immediately understand not just that an entry is overdue, but how much overdue time has accumulated relative to the original timeline.
