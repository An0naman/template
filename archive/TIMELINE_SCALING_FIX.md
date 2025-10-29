# Timeline Scaling Fix - Summary

## Problem Identified
The time progress bar was extending beyond the container bounds when entries were overdue, breaking the page layout.

## Root Cause
The original implementation kept the track as a fixed width representing "created to intended end" and tried to extend the overdue section beyond 100%, causing overflow:

```javascript
// BEFORE (Broken):
timeProgressFill.style.width = '100%';           // Fill = intended timeline
timeProgressOverdue.style.width = overduePercentage + '%'; // Extends BEYOND 100%
// Result: Total width could be 150%, 200%, etc. - breaks layout!
```

## Solution: Dynamic Track Scaling
Changed the track to represent different timespans based on entry state:

### Normal State (On Track)
- **Track represents**: Created → Intended End Date
- **Fill calculation**: `(daysElapsed / totalDays) * 100%`
- **Track width**: Always 100% of container

### Overdue State
- **Track represents**: Created → **Today** (current date)
- **Fill calculation**: `(intendedDays / totalDisplayDays) * 100%`
- **Overdue calculation**: `(overdueDays / totalDisplayDays) * 100%`
- **Track width**: Always 100% of container
- **Key**: `totalDisplayDays = intendedDays + overdueDays`

## Implementation

### JavaScript Changes
```javascript
// AFTER (Fixed):
if (daysRemaining < 0) {
    const overdueDays = Math.abs(daysRemaining);
    const totalDisplayDays = totalDays + overdueDays; // Created to Today
    
    // Both sections sized as percentage of total display
    const intendedPercentage = (totalDays / totalDisplayDays) * 100;
    const overduePercentage = (overdueDays / totalDisplayDays) * 100;
    
    timeProgressFill.style.width = intendedPercentage + '%';    // e.g., 92.9%
    timeProgressOverdue.style.width = overduePercentage + '%';  // e.g., 7.1%
    // Total: 92.9% + 7.1% = 100% - stays within bounds!
}
```

### Marker Positioning
```javascript
// Target marker shows where deadline was
timeProgressTarget.style.left = intendedPercentage + '%';

// "Today" marker always at 100% (right edge when overdue)
timeProgressMarker.style.left = '100%';
```

## Visual Examples

### Example 1: 2 Days Overdue on 26-Day Timeline
```
Total display = 26 + 2 = 28 days
Intended: 26/28 = 92.9%
Overdue: 2/28 = 7.1%

┌────────────────────────────────────────┐ ← 100% container
│ █████████████████████████████████████▼▓▼│
│ ←──────── 92.9% ────────→ ←── 7.1% ──→│
│                          ↑             ↑
│                       Target        Today
└────────────────────────────────────────┘
```

### Example 2: 9 Days Overdue on 26-Day Timeline
```
Total display = 26 + 9 = 35 days
Intended: 26/35 = 74.3%
Overdue: 9/35 = 25.7%

┌────────────────────────────────────────┐ ← 100% container
│ ██████████████████████████████▼▓▓▓▓▓▓▓▓▓▼│
│ ←────── 74.3% ──────→ ←─── 25.7% ───→│
│                       ↑               ↑
│                    Target          Today
└────────────────────────────────────────┘
```

### Example 3: Heavily Overdue (26 days on 26-day timeline)
```
Total display = 26 + 26 = 52 days
Intended: 26/52 = 50%
Overdue: 26/52 = 50%

┌────────────────────────────────────────┐ ← 100% container
│ █████████████████████▼▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▼│
│ ←─────── 50% ───────→ ←──── 50% ─────→│
│                      ↑                 ↑
│                   Target            Today
└────────────────────────────────────────┘
```

## Benefits

### Layout Stability
✅ **Always 100% width** - Never breaks container  
✅ **Responsive** - Works at any screen size  
✅ **Scalable** - Handles extreme overdue gracefully

### Visual Communication
✅ **Proportional** - Overdue size relative to total time  
✅ **Contextual** - 2 days looks different on 7-day vs 90-day timeline  
✅ **Intuitive** - Larger red section = more overdue relative to timeline

### Mathematical Accuracy
✅ **Precise** - Exact day calculations  
✅ **Consistent** - Same logic for all states  
✅ **Verifiable** - percentages always sum to 100%

## Edge Cases Handled

### Just Overdue (1 day on 365-day timeline)
- Display: 366 days
- Intended: 99.7%
- Overdue: 0.3% (very thin red line)
- **Works**: Small visual indicator

### Heavily Overdue (100 days on 7-day timeline)
- Display: 107 days  
- Intended: 6.5%
- Overdue: 93.5% (dominates the bar)
- **Works**: Red section clearly dominates

### Exactly On Time
- Display: 26 days
- Intended: 100%
- Overdue: 0%
- **Works**: No red section, marker at target

## Code Location
`/app/templates/sections/_timeline_section.html`
- Lines: ~875-925 (calculateProgress function)
- Updated: October 28, 2025

## Related Documentation
- TIME_PROGRESS_BAR_FEATURE.md
- OVERDUE_VISUALIZATION_FEATURE.md
- OVERDUE_INDICATOR_FEATURE.md

## Testing Checklist
- [x] Normal progress (0-99%) stays within bounds
- [x] Exactly on time (100%) displays correctly
- [x] Slightly overdue (1-2 days) shows small red section
- [x] Moderately overdue (10-20% of timeline) shows visible red
- [x] Heavily overdue (50%+ of timeline) shows dominant red
- [x] Extreme overdue (100%+ of timeline) stays within container
- [x] Markers positioned correctly
- [x] Tooltips show accurate information
- [x] Responsive on different screen sizes

## Conclusion
By dynamically scaling what the track represents (intended timeline vs. total elapsed time), we maintain a consistent 100% container width while accurately visualizing both the intended timeline and overdue period. This ensures layout stability while providing clear, proportional visualization of overdue status.
