# Automatic Intended End Date from Milestones

## Overview
The entry's `intended_end_date` is now automatically calculated based on the total duration of all milestones.

## How It Works

### Calculation Formula
```
intended_end_date = entry.created_at + SUM(all milestone durations)
```

### Example
**Entry created:** January 1, 2025

**Milestones:**
1. Brewing - 2 days
2. Fermenting - 14 days  
3. Conditioning - 7 days

**Total:** 23 days

**Auto-calculated end date:** January 24, 2025

## When End Date Updates

The `intended_end_date` is automatically recalculated whenever:

1. ✅ **A milestone is added** (POST `/api/entries/{id}/milestones`)
   - New duration added to total
   - End date extends accordingly

2. ✅ **A milestone duration is edited** (PUT `/api/entries/{id}/milestones/{milestone_id}`)
   - Total recalculated with new duration
   - End date adjusted

3. ✅ **A milestone is reordered** (PUT with `order_position`)
   - Order doesn't affect total duration
   - End date stays the same (unless duration also changed)

4. ✅ **A milestone is deleted** (DELETE `/api/entries/{id}/milestones/{milestone_id}`)
   - Duration removed from total
   - End date moves earlier

## Technical Implementation

### Backend Function
```python
def update_entry_intended_end_date(entry_id, cursor):
    """
    Update the entry's intended_end_date based on total milestone duration.
    """
    # Get entry created_at
    cursor.execute("SELECT created_at FROM Entry WHERE id = ?", (entry_id,))
    entry = cursor.fetchone()
    
    # Calculate total duration from all milestones
    cursor.execute("""
        SELECT COALESCE(SUM(duration_days), 0) as total_days
        FROM EntryStateMilestone
        WHERE entry_id = ?
    """, (entry_id,))
    total_days = cursor.fetchone()['total_days']
    
    if total_days > 0:
        created_at = datetime.fromisoformat(entry['created_at'])
        new_end_date = created_at + timedelta(days=total_days)
        
        cursor.execute("""
            UPDATE Entry
            SET intended_end_date = ?
            WHERE id = ?
        """, (new_end_date.isoformat(), entry_id))
```

### API Integration
The function is called in:
- `create_milestone()` - after inserting new milestone
- `update_milestone()` - after updating duration or order
- `delete_milestone()` - after deleting milestone

All within the same transaction (before `conn.commit()`).

## User Experience

### Before
- User manually sets intended_end_date
- Milestones are visual only
- No automatic synchronization

### After
- User adds milestones with durations
- System automatically calculates end date
- Timeline always reflects milestone plan
- Editing milestones updates end date in real-time

## Edge Cases

### No Milestones
- If entry has no milestones, `intended_end_date` remains unchanged
- User can still manually set end date

### Manual Override
- Currently, the system always overwrites `intended_end_date` when milestones exist
- Future enhancement: Add a flag to allow manual end date override

### Timeline Display
- The timeline progress bar uses `intended_end_date` for total duration
- Milestone segments are positioned within this timeline
- Everything stays synchronized automatically

## Benefits

1. **Consistency** - End date always matches milestone plan
2. **No manual calculation** - System does the math
3. **Real-time updates** - Changes reflect immediately
4. **Prevents drift** - Timeline and milestones stay aligned
5. **Better planning** - Visual feedback matches actual plan

## Future Enhancements

Potential additions:
- [ ] Flag to disable auto-calculation (manual mode)
- [ ] Warning if manual end date conflicts with milestone total
- [ ] Recalculate on entry `created_at` change
- [ ] Support for pause/buffer days between milestones
- [ ] Business days vs calendar days option

---

**Implemented:** October 29, 2025  
**Feature:** Automatic intended_end_date from milestone durations
