# Dynamic Intended End Date Update Fix

## Problem Report (User Screenshot)

**Issue:** With 3 milestones each lasting 1 day:
- ✅ Milestone segments rendered correctly (3 colored bars)
- ❌ Target date marker at day 15 (old intended_end_date)
- ❌ Overdue section calculated from day 15 instead of day 3
- **Expected:** Target at day 3, overdue starting after day 3

## Root Cause

The timeline rendering had **two sources of truth**:

1. **Milestone segments** → Calculated from current milestone data (CORRECT)
2. **Progress/overdue bars** → Used stale Jinja template variable (WRONG)

```javascript
// Milestones: Used current data ✅
const totalDays = milestones.reduce((sum, m) => sum + m.duration_days, 0);

// Progress: Used stale template variable ❌
const endDate = new Date('{{ entry.intended_end_date }}'); // From page load!
```

**Timeline of events:**
1. Page loads with `intended_end_date = Oct 15`
2. User adds 3 milestones (1 day each)
3. Backend updates database: `intended_end_date = Oct 15` (Oct 12 + 3 days)
4. Milestones render using sum(durations) = 3 days ✅
5. Progress/overdue uses old Oct 15 from page load ❌

**Result:** Timeline shows 3 milestone segments ending at day 3, but target marker at day 15!

## Solution Implemented

### 1. Store Entry Data Dynamically

**Added global state object:**
```javascript
let entryData = {
    createdAt: '{{ entry.created_at }}',
    intendedEndDate: '{{ entry.intended_end_date }}',  // Will be updated
    showEndDates: {{ 'true' if entry.show_end_dates else 'false' }}
};
```

### 2. Refresh Entry Data Function

**Created API fetch to get updated data:**
```javascript
async function refreshEntryData() {
    const response = await fetch(`/api/entries/${entryId}`);
    if (response.ok) {
        const entry = await response.json();
        if (entry.intended_end_date) {
            entryData.intendedEndDate = entry.intended_end_date;
            console.log('Updated intended_end_date:', entryData.intendedEndDate);
        }
    }
}
```

### 3. Updated Progress Calculation

**Changed from static to dynamic:**
```javascript
// BEFORE (stale):
function calculateProgress() {
    const startDate = new Date('{{ entry.created_at }}');
    const endDate = new Date('{{ entry.intended_end_date }}');  // ❌ Never updates
    // ...
}

// AFTER (dynamic):
function calculateProgress() {
    const startDate = new Date(entryData.createdAt);
    const endDate = new Date(entryData.intendedEndDate);  // ✅ Updates from API
    // ...
}
```

### 4. Refresh on Milestone Changes

**Updated `loadAndRenderMilestones()`:**
```javascript
async function loadAndRenderMilestones() {
    // 1. Fetch milestones
    const milestones = await fetch(`/api/entries/${entryId}/milestones`).json();
    
    // 2. Refresh entry data (gets new intended_end_date)
    await refreshEntryData();
    
    // 3. Recalculate progress with updated end date
    calculateProgress();
    
    // 4. Render milestone segments
    renderMilestones(milestones);
}
```

## Fixed Flow

**User adds/edits milestone:**
1. API call updates milestone → backend recalculates `intended_end_date` ✅
2. `loadAndRenderMilestones()` called
3. Fetches updated milestones ✅
4. **NEW:** Fetches updated entry data (`refreshEntryData()`) ✅
5. **NEW:** Recalculates progress with new end date ✅
6. Renders milestone segments ✅
7. **Result:** Everything synchronized! ✅

## Example Scenario

**Entry created:** Oct 12, 2025  
**Milestones added:**
- #1: 1 day
- #2: 1 day  
- #3: 1 day

**Backend updates:**
```sql
UPDATE Entry
SET intended_end_date = '2025-10-15'  -- Oct 12 + 3 days
WHERE id = 91
```

**Frontend (OLD - BROKEN):**
- Milestone segments: Show days 0-1, 1-2, 2-3 ✅
- Target marker: At day 15 (stale from page load) ❌
- Overdue: Starts at day 15 ❌
- **Visual mismatch!**

**Frontend (NEW - FIXED):**
- Fetches updated entry: `intended_end_date = 2025-10-15` ✅
- Milestone segments: Show days 0-1, 1-2, 2-3 ✅
- Target marker: At day 3 (Oct 15) ✅
- Overdue: Starts at day 3 ✅
- **Everything aligned!**

## Additional Improvements

### Dynamic Target Tooltip
```javascript
// BEFORE: Hardcoded from template
timeProgressTarget.title = `Target: {{ entry.intended_end_date[:10] }}`;

// AFTER: Dynamic from current data
const endDateStr = endDate.toISOString().split('T')[0];
timeProgressTarget.title = `Target: ${endDateStr}`;
```

### Consistent Date Handling
All timeline calculations now use the same `entryData.intendedEndDate` variable, ensuring consistency across:
- Progress percentage
- Overdue calculation
- Target marker position
- Days remaining display

## Testing Verification

### Test Case 1: Add Milestones
1. Create entry (Oct 12)
2. Add milestone: 3 days
3. ✅ Backend: intended_end_date = Oct 15
4. ✅ Frontend: Refreshes and shows target at day 3
5. ✅ Today (Oct 29) shows overdue starting at day 3

### Test Case 2: Edit Duration
1. Change milestone from 3 to 7 days
2. ✅ Backend: intended_end_date = Oct 19
3. ✅ Frontend: Refreshes and shows target at day 7
4. ✅ Overdue section adjusts to start at day 7

### Test Case 3: Delete Milestone
1. Delete 3-day milestone
2. ✅ Backend: intended_end_date unchanged (no milestones)
3. ✅ Frontend: Shows original end date
4. ✅ Timeline returns to original state

## Performance Consideration

**Extra API Call:**
- One additional GET `/api/entries/{id}` per milestone operation
- Negligible impact (< 50ms typically)
- Alternative would be to include `intended_end_date` in milestone response

**Future Optimization:**
```python
# In milestone_api.py, include updated entry data in response
return jsonify({
    'message': 'Milestone created successfully',
    'milestone_id': milestone_id,
    'intended_end_date': entry.intended_end_date  # Include here
})
```

## Summary

**Problem:** Timeline components used different data sources (current vs stale)  
**Solution:** Fetch updated entry data after every milestone change  
**Result:** Progress bar, target marker, and overdue section now perfectly align with milestone plan

**User Experience:**
- Add milestones → Target moves to end of last milestone ✅
- Edit duration → Target adjusts immediately ✅
- Overdue section starts right after target ✅
- No page reload needed ✅

---

**Fixed:** October 29, 2025  
**Issue:** Progress bar using stale intended_end_date after milestone changes
