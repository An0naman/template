# Overdue Indicator Feature

## Overview
Added visual indicators to highlight when an entry has exceeded its intended end date, making it immediately obvious when tasks or entries are overdue.

## Implementation Date
October 28, 2025

## Visual Indicators

### 1. **Progress Bar Red Border**
- **When**: Entry is past its `intended_end_date`
- **Style**: 2px red border around the unified progress bar
- **Color**: `#dc3545` (Bootstrap danger color)

### 2. **Diagonal Stripe Pattern**
- **When**: Entry is overdue
- **Style**: Subtle diagonal stripes overlay on the progress bar
- **Pattern**: 45° angle, 10px spacing, red tint with low opacity
- **Purpose**: Makes overdue status visible even at a glance

### 3. **"OVERDUE" Text Badge**
- **Location**: Top center, next to percentage
- **Format**: `[percentage]% - OVERDUE`
- **Icon**: Warning triangle (⚠️)
- **Color**: Red text (`text-danger`)

### 4. **Days Overdue Counter**
- **Location**: Bottom right corner
- **Format**: `X days overdue`
- **Icon**: Warning triangle
- **Color**: Red, bold
- **Calculation**: Absolute value of negative days remaining

## CSS Implementation

```css
.unified-progress-container.overdue {
    box-shadow: 0 0 0 2px #dc3545, 0 2px 4px rgba(0, 0, 0, 0.1);
}

.unified-progress-container.overdue::after {
    content: '';
    position: absolute;
    top: 0;
    right: 0;
    bottom: 0;
    left: 0;
    background: repeating-linear-gradient(
        45deg,
        transparent,
        transparent 10px,
        rgba(220, 53, 69, 0.1) 10px,
        rgba(220, 53, 69, 0.1) 20px
    );
    pointer-events: none;
}
```

## JavaScript Logic

### Overdue Detection
```javascript
{% if entry.show_end_dates and entry.intended_end_date %}
const intendedEndDate = new Date('{{ entry.intended_end_date }}');
const now = new Date();
const isOverdue = now > intendedEndDate;

if (isOverdue) {
    container.classList.add('overdue');
}
{% endif %}
```

### Progress Text Update
```javascript
const daysRemaining = totalDays - daysElapsed; // Can be negative

if (daysRemaining < 0) {
    progressText.innerHTML = '<i class="fas fa-exclamation-triangle me-1"></i>' +
        '<span>' + Math.round(percentage) + '</span>% - OVERDUE';
    progressText.classList.add('text-danger');
}
```

### Days Counter Update
```javascript
if (daysRemaining < 0) {
    remainingText.innerHTML = 
        `<i class="fas fa-exclamation-triangle me-1"></i>${Math.abs(daysRemaining)} days overdue`;
    remainingText.className = 'text-danger fw-bold';
}
```

## User Experience

### Normal Entry
```
┌─────────────────────────────────────────┐
│ Created: 2025-10-01  92% Complete  Target: 2025-10-30 │
├─────────────────────────────────────────┤
│ ████████████████████████████░░░░░░░░    │ ← Normal blue/green segments
├─────────────────────────────────────────┤
│ 24 days elapsed  [●●●●] Legend  2 days remaining │
└─────────────────────────────────────────┘
```

### Overdue Entry
```
┌─────────────────────────────────────────┐
│ Created: 2025-10-01  ⚠️ 104% - OVERDUE  Target: 2025-10-26 │
├═════════════════════════════════════════┤ ← RED BORDER
│ ████████████████████████████████████▓▓▓▓│ ← Diagonal stripes
├─────────────────────────────────────────┤
│ 28 days elapsed  [●●●●] Legend  ⚠️ 2 days overdue │
└─────────────────────────────────────────┘
```

## States

### On Time
- **Condition**: `now <= intended_end_date`
- **Progress**: 0-100%
- **Color**: Normal (no red)
- **Message**: "X days remaining"

### Target Reached (On Time)
- **Condition**: `daysRemaining === 0`
- **Progress**: 100%
- **Color**: Green success
- **Message**: "✓ Target reached!"

### Overdue
- **Condition**: `now > intended_end_date`
- **Progress**: 100%+
- **Color**: Red danger
- **Border**: Red outline
- **Pattern**: Diagonal stripes
- **Message**: "⚠️ X days overdue"

## Conditional Display

Only shows overdue indicators when:
1. Entry has `show_end_dates = true`
2. Entry has valid `intended_end_date`
3. Current date > intended end date

Entries without end dates show normal timeline without overdue status.

## Accessibility

- **Color Not Only Indicator**: Uses icons (⚠️) in addition to red color
- **Pattern Overlay**: Provides visual texture for colorblind users
- **Bold Text**: "OVERDUE" text is prominent
- **Multiple Signals**: Border, pattern, text, icon all indicate overdue status

## Performance

- **Calculation**: Done once on load and when progress updates
- **CSS**: Uses pseudo-elements (::after) for pattern overlay
- **No Extra DOM**: Stripe pattern uses CSS gradients, not extra elements

## Integration Points

- Works with unified progress bar
- Respects `entry.show_end_dates` setting
- Uses `entry.intended_end_date` for calculation
- Updates dynamically if progress recalculated

## Testing Scenarios

1. **Entry with future end date** → Normal display
2. **Entry with end date today** → "Target reached!"
3. **Entry with end date yesterday** → "1 day overdue" + red styling
4. **Entry with end date 1 week ago** → "7 days overdue" + red styling
5. **Entry without end date** → No overdue indicator shown

## Files Modified
- `/app/templates/sections/_timeline_section.html`
  - Added `.overdue` CSS class with red border and stripe pattern
  - Added overdue detection in `renderStatusProgression()`
  - Updated `calculateProgress()` to show overdue status
  - Added "OVERDUE" badge to progress text
  - Updated days counter to show "days overdue"

## Related Features
- Unified Progress Bar
- Dynamic Status Colors
- Time-based Progress Tracking
- Status History Timeline

## Future Enhancements
- [ ] Configurable overdue warning threshold (e.g., 3 days before)
- [ ] Different severity levels (warning at 90%, critical when overdue)
- [ ] Notifications when entry becomes overdue
- [ ] Overdue filter in entry list
- [ ] Overdue dashboard widget
- [ ] Custom overdue messages per entry type
- [ ] Grace period configuration

## Conclusion
The overdue indicator feature provides immediate visual feedback when entries exceed their intended completion dates, using multiple visual cues (color, border, pattern, text, icons) to ensure the status is unmistakable and accessible to all users.
