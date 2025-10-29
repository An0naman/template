# Timeline Rendering Fix

## Problem Identified

The planned milestone timeline was showing incorrect positions after editing milestone durations because:

1. **Backend** correctly updated `intended_end_date` in the database
2. **Frontend** was using the **stale** `intended_end_date` from page load (Jinja template variable)
3. When milestones changed, the JavaScript never got the updated end date

## The Bug

### Before (Incorrect):
```javascript
// Used static Jinja variable from page load
const endDate = new Date('{{ entry.intended_end_date }}'); // STALE!
const totalDuration = endDate - startDate;
const totalDays = Math.ceil(totalDuration / (1000 * 60 * 60 * 24));
```

**Problem:** After editing a milestone duration:
- Database: `intended_end_date` updated ✅
- JavaScript: Still using old `intended_end_date` from template ❌
- Result: Milestone positions calculated incorrectly

### After (Fixed):
```javascript
// Calculate from milestones themselves (source of truth)
const totalDays = milestones.reduce((sum, m) => sum + m.duration_days, 0);
```

**Benefits:**
- Always uses **current** milestone data
- No dependency on stale template variables
- Timeline updates immediately when milestones change
- Single source of truth: the milestone durations

## What Changed

### renderMilestones() Function

**Old Logic:**
1. Get `endDate` from Jinja template (set on page load)
2. Calculate `totalDays = (endDate - startDate) / ms_per_day`
3. Position milestones as percentage of this total

**New Logic:**
1. ✅ Calculate `totalDays = sum(all milestone.duration_days)`
2. ✅ Position milestones as percentage of this total
3. ✅ Each segment starts where previous ended (cumulative)

### Position Calculation

**Before:**
```javascript
cumulativeDays += milestone.duration_days;
const position = (cumulativeDays / totalDays) * 100;
const width = (milestone.duration_days / totalDays) * 100;
marker.style.left = `${Math.max(0, position - width)}%`; // WRONG!
```

**After:**
```javascript
const startPosition = (cumulativeDays / totalDays) * 100;
cumulativeDays += milestone.duration_days;
const width = (milestone.duration_days / totalDays) * 100;
marker.style.left = `${startPosition}%`; // CORRECT!
```

## Example Scenario

**Milestones:**
- #1 Brewing: 2 days
- #2 Fermenting: 14 days
- #3 Conditioning: 7 days

**Total:** 23 days

### User edits Fermenting to 10 days:

**Backend:**
1. Updates milestone duration_days = 10 ✅
2. Recalculates intended_end_date = created_at + 19 days ✅
3. Saves to database ✅

**Frontend (OLD - BROKEN):**
1. Still thinks total is 23 days (from page load)
2. Positions milestones incorrectly
3. Timeline doesn't match reality ❌

**Frontend (NEW - FIXED):**
1. Refetches milestones via API ✅
2. Calculates total = 2 + 10 + 7 = 19 days ✅
3. Positions: 0-2 (Brewing), 2-12 (Fermenting), 12-19 (Conditioning) ✅
4. Timeline perfectly matches milestone plan ✅

## Additional Improvements

### Removed "Skip if beyond end date" logic
**Before:**
```javascript
if (milestoneDate > endDate) {
    return; // Skip milestones beyond intended end
}
```
**Why removed:** With the new logic, milestones **define** the timeline, so they can't be "beyond" it.

### Better empty state handling
```javascript
if (!timeProgressBar || milestones.length === 0) {
    if (timeProgressBar) {
        timeProgressBar.querySelectorAll('.time-progress-milestone').forEach(el => el.remove());
    }
    return;
}
```

### Zero-duration safety
```javascript
const totalDays = milestones.reduce((sum, m) => sum + m.duration_days, 0);
if (totalDays === 0) return; // Prevent divide-by-zero
```

## Testing

### Test Case 1: Add Milestone
1. Add milestone (5 days)
2. ✅ Backend sets intended_end_date = created_at + 5
3. ✅ Frontend calculates totalDays = 5
4. ✅ Timeline shows segment from 0% to 100%

### Test Case 2: Edit Duration
1. Edit milestone from 5 to 10 days
2. ✅ Backend sets intended_end_date = created_at + 10
3. ✅ Frontend recalculates totalDays = 10
4. ✅ Timeline updates immediately

### Test Case 3: Multiple Milestones
1. Add M1 (2d), M2 (7d), M3 (5d)
2. ✅ Backend sets intended_end_date = created_at + 14
3. ✅ Frontend totalDays = 14
4. ✅ Segments: 0-14% (M1), 14-64% (M2), 64-100% (M3)

### Test Case 4: Reorder
1. Move M3 before M2
2. ✅ Backend intended_end_date unchanged (same total)
3. ✅ Frontend totalDays unchanged
4. ✅ Segments reorder visually but timeline length stays same

## Summary

**Root Cause:** Using stale template variable for timeline calculation  
**Solution:** Calculate from current milestone data (source of truth)  
**Result:** Timeline always accurate, updates in real-time

---

**Fixed:** October 29, 2025  
**Bug:** Planned timeline rendering with stale intended_end_date
