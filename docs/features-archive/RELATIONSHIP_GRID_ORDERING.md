# Relationship Grid Ordering Feature

## Overview

Added the ability to customize the display order of relationship type cards (grids) within the relationships section of Entry Detail V2. The ordering is configured **per entry type**, meaning when you reorder the grids for one entry, all entries of that type will display the grids in the same order.

## Features

✅ **Drag-and-Drop Reordering** - Intuitive drag handles to rearrange relationship type cards
✅ **Entry Type Level** - Order applies to all entries of the same type
✅ **Persistent Storage** - Order is saved to database and persists across sessions
✅ **Visual Feedback** - Clear drag handles and visual indicators during reordering
✅ **Auto-Save** - Changes are automatically saved when you finish dragging
✅ **Notification System** - Success/error messages when saving order

## How to Use

### 1. Navigate to an Entry
- Open any entry in the V2 detail view
- Scroll to the "Related Records" (Relationships) section

### 2. Enable Reorder Mode
- Click the **"Reorder"** button in the section header (appears when there are 2+ relationship types)
- Drag handles (⋮⋮) will appear on the left side of each relationship type card
- The button will turn blue and say "Done"

### 3. Reorder the Cards
- Click and hold on any drag handle (⋮⋮)
- Drag the card up or down to your desired position
- Release to drop the card in place
- The order is automatically saved

### 4. Exit Reorder Mode
- Click the **"Done"** button to exit reorder mode
- Drag handles will disappear
- Your custom order is now applied to all entries of this type

## Technical Implementation

### Database Schema

**Table: `RelationshipGridOrder`**
```sql
CREATE TABLE RelationshipGridOrder (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_type_id INTEGER NOT NULL,
    relationship_definition_id INTEGER NOT NULL,
    display_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (entry_type_id) REFERENCES EntryType(id) ON DELETE CASCADE,
    FOREIGN KEY (relationship_definition_id) REFERENCES RelationshipDefinition(id) ON DELETE CASCADE,
    UNIQUE(entry_type_id, relationship_definition_id)
);
```

### API Endpoints

#### Get Grid Order
```http
GET /api/entry_types/{entry_type_id}/relationship_grid_order
```
**Response:**
```json
{
  "1": 0,
  "2": 1,
  "3": 2
}
```
Maps relationship definition IDs to display order positions.

#### Save Grid Order
```http
POST /api/entry_types/{entry_type_id}/relationship_grid_order
Content-Type: application/json

{
  "order": [
    {"definition_id": 1, "order": 0},
    {"definition_id": 2, "order": 1},
    {"definition_id": 3, "order": 2}
  ]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Grid order saved successfully"
}
```

### Frontend Components

#### JavaScript Functions
- `initializeDragAndDrop()` - Sets up drag-and-drop event listeners
- `saveGridOrder()` - Persists order to database via API
- `toggleReorderMode()` - Toggles between normal and reorder mode
- `getDragAfterElement()` - Calculates drop position during drag

#### CSS Classes
- `.card-drag-handle` - Styling for drag handle icons
- `.reorder-mode-active` - Applied to container during reorder mode
- `.dragging` - Applied to card being dragged
- `.drag-over` - Applied to drop target during drag

## Files Modified

### Backend
1. **`app/db.py`** - Added RelationshipGridOrder table creation
2. **`app/api/relationships_api.py`** - Added GET/POST endpoints for grid order
3. **`migrations/add_relationship_grid_ordering.py`** - Migration script

### Frontend
4. **`app/templates/sections/_relationships_section_v2.html`**
   - Added reorder button in section header
   - Added drag handles to cards
   - Added drag-and-drop JavaScript functionality
   - Added CSS for drag-and-drop styling

## Migration

To add this feature to an existing database:

```bash
# Run migration
docker exec template python /app/migrations/add_relationship_grid_ordering.py /app/data/template.db
```

Or rebuild the container (table is created automatically on init):
```bash
docker compose down
docker compose up --build -d
```

## Default Behavior

- **No custom order**: Relationship types display in the order they were fetched from the database (typically by name)
- **Custom order exists**: Relationship types display in the saved order
- **New relationship type added**: Appears at the end until manually reordered

## Notes

- Only visible relationship types with relationships are shown (empty types can be toggled with "Show Empty" button)
- The reorder button only appears when there are 2 or more relationship type cards
- Order changes apply immediately to all entries of the same type
- The feature uses HTML5 Drag and Drop API for maximum compatibility

## Future Enhancements

Potential improvements:
- [ ] Bulk reorder across multiple entry types
- [ ] Export/import order configurations
- [ ] Reset to default order button
- [ ] Keyboard shortcuts for reordering
- [ ] Touch device support improvements

---

**Implementation Date**: November 6, 2025  
**Version**: 1.0  
**Status**: ✅ Complete and Production Ready
