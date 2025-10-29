# 🎯 Configurable Entry States Feature

## Overview

The Configurable Entry States feature allows users to define custom states for entries on a per-entry-type basis. This replaces the previous hardcoded "Active" and "Inactive" status options with a flexible state management system.

## Use Cases

### Homebrewing Example
For a homebrewing application, you might define:
- **Active States**: "Primary Ferment", "Secondary Ferment", "Conditioning"
- **Inactive States**: "Racked", "Bottled", "Consumed", "Discarded"

### Project Management Example
- **Active States**: "Planning", "In Progress", "Review"
- **Inactive States**: "Completed", "Archived", "Cancelled"

### Inventory Example
- **Active States**: "In Stock", "Low Stock", "On Order"
- **Inactive States**: "Out of Stock", "Discontinued", "Returned"

## Features

### ✨ Key Capabilities

1. **Per-Entry-Type Configuration**: Each entry type can have its own set of states
2. **Category System**: States are categorized as either "Active" or "Inactive"
3. **Color Coding**: Each state can have a custom display color
4. **Default State**: Mark one state as default for new entries
5. **Display Order**: Control the order states appear in dropdowns
6. **Dynamic Filtering**: Filter entries by state category (active/inactive)
7. **Visual Management**: Easy-to-use UI for managing states

## Database Schema

### EntryState Table

```sql
CREATE TABLE EntryState (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_type_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    category TEXT NOT NULL CHECK(category IN ('active', 'inactive')),
    color TEXT DEFAULT '#6c757d',
    display_order INTEGER DEFAULT 0,
    is_default INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(entry_type_id, name),
    FOREIGN KEY (entry_type_id) REFERENCES EntryType(id) ON DELETE CASCADE
);
```

### Fields

- **entry_type_id**: Links the state to a specific entry type
- **name**: The display name of the state (e.g., "Primary Ferment")
- **category**: Either "active" or "inactive" - used for filtering
- **color**: Hex color code for visual display (e.g., "#28a745")
- **display_order**: Controls the order in dropdowns (lower = first)
- **is_default**: Boolean flag - only one state per entry type should be default
- **created_at**: Timestamp of state creation

## API Endpoints

### Get States for Entry Type
```http
GET /api/entry_types/{entry_type_id}/states
```

**Response:**
```json
[
  {
    "id": 1,
    "entry_type_id": 1,
    "name": "Primary Ferment",
    "category": "active",
    "color": "#28a745",
    "display_order": 0,
    "is_default": true,
    "created_at": "2025-10-12T00:00:00"
  },
  {
    "id": 2,
    "entry_type_id": 1,
    "name": "Consumed",
    "category": "inactive",
    "color": "#6c757d",
    "display_order": 1,
    "is_default": false,
    "created_at": "2025-10-12T00:00:00"
  }
]
```

### Create New State
```http
POST /api/entry_types/{entry_type_id}/states
Content-Type: application/json

{
  "name": "Secondary Ferment",
  "category": "active",
  "color": "#0d6efd",
  "display_order": 1,
  "is_default": false
}
```

### Update State
```http
PUT /api/entry_types/{entry_type_id}/states/{state_id}
Content-Type: application/json

{
  "name": "Secondary Fermentation",
  "color": "#0066cc",
  "display_order": 2
}
```

### Delete State
```http
DELETE /api/entry_types/{entry_type_id}/states/{state_id}
```

**Note:** Cannot delete a state if:
- It's currently in use by entries
- It's the last remaining state for the entry type

### Get Available States for Entry
```http
GET /api/entries/{entry_id}/available_states
```

Returns all available states for the entry's type.

## User Interface

### Managing States

1. **Navigate to Entry Types Management**
   - Go to Settings → Data Structure → Entry Types
   - Or navigate to `/manage_entry_types`

2. **Open State Manager**
   - Click the **Manage States** button (<i class="fas fa-list-check"></i>) for any entry type

3. **Add New State**
   - Click "Add New State" button
   - Fill in the form:
     - **State Name**: The display name (e.g., "Primary Ferment")
     - **Category**: Choose Active or Inactive
     - **Display Color**: Pick a color for the badge
     - **Display Order**: Set the sort order (0 = first)
     - **Set as Default**: Check to make this the default for new entries

4. **Edit Existing State**
   - Click the edit button (<i class="fas fa-edit"></i>) next to any state
   - Update the fields and save

5. **Delete State**
   - Click the delete button (<i class="fas fa-trash-alt"></i>) next to any state
   - Confirm deletion
   - **Note:** Cannot delete if state is in use

### Using States in Entries

#### Creating New Entries
When creating a new entry, it will automatically use the default state for that entry type.

#### Editing Entry Status
1. Open any entry detail page
2. Click "Edit" in the Details section
3. Select the desired state from the Status dropdown
4. Available states are filtered to those configured for the entry's type

#### Filtering by State Category
On the main index page, use the Status filter dropdown:
- **All Status**: Show all entries
- **Active**: Show only entries with active states
- **Inactive**: Show only entries with inactive states

## Migration & Backwards Compatibility

### Automatic Migration

When the system initializes:
1. The EntryState table is created if it doesn't exist
2. For each existing entry type without states, default "Active" and "Inactive" states are created
3. "Active" is set as the default state
4. Existing entries keep their current status values

### Default States Created

For each entry type:
```python
{
  "name": "Active",
  "category": "active",
  "color": "#28a745",  # Green
  "display_order": 0,
  "is_default": True
}

{
  "name": "Inactive",
  "category": "inactive",
  "color": "#6c757d",  # Gray
  "display_order": 1,
  "is_default": False
}
```

## Best Practices

### Naming Conventions
- Use clear, descriptive names (e.g., "Primary Fermentation" not "PF")
- Be consistent with terminology across similar entry types
- Use action-oriented names where appropriate

### Color Selection
- Use green shades for positive active states
- Use blue for neutral active states
- Use yellow/orange for warning states
- Use gray for inactive/archived states
- Ensure sufficient contrast for readability

### Organization
- Set display_order logically (workflow progression)
- Group similar states with similar colors
- Keep the number of states manageable (5-7 per type)
- Mark the most common initial state as default

### State Categories
- **Active**: Ongoing, in-progress, requires attention
- **Inactive**: Completed, archived, no action needed

Use categories consistently to ensure filtering works as expected.

## Implementation Details

### Files Modified

#### Database
- `app/db.py`: Added EntryState table and migration logic

#### API
- `app/api/entry_state_api.py`: New API endpoints for state management
- `app/api/entry_api.py`: Updated to use default states
- `app/__init__.py`: Registered new blueprint

#### Routes
- `app/routes/main_routes.py`: Updated queries to include state info

#### Templates
- `app/templates/manage_entry_types.html`: Added state management UI
- `app/templates/entry_detail.html`: Dynamic state loading
- `app/templates/index.html`: Color-coded state badges and category filtering

### JavaScript Functions

#### entry_detail.html
```javascript
// Load available states for the current entry
async function loadStatesForEntry()

// Listen for entry type changes
entryTypeSelect.addEventListener('change', loadStatesForEntry)
```

#### manage_entry_types.html
```javascript
// Open states modal
function openStatesModal(entryTypeId, entryTypeName)

// Load states for entry type
function loadStates(entryTypeId)

// Render states list
function renderStates(states)

// Add/Edit state form
function openAddStateForm()
function editState(stateId)
function saveState()

// Delete state
function deleteState(stateId)
```

## Troubleshooting

### States Not Appearing
1. Check that states are defined for the entry type
2. Verify the entry type ID matches
3. Check browser console for JavaScript errors

### Cannot Delete State
- Ensure no entries are using the state
- Check that it's not the last state for the entry type

### Default State Not Working
- Verify only one state per entry type has `is_default = 1`
- Check database integrity

### Colors Not Displaying
- Ensure hex color codes are properly formatted (#RRGGBB)
- Check for CSS conflicts

## Future Enhancements

### Potential Features
- State transitions and workflow rules
- State-based automation triggers
- State history tracking
- Bulk state updates
- State templates for quick setup
- State-based notifications
- Custom state icons
- State permissions

## Support

For issues or questions:
1. Check the logs: `docker logs template`
2. Verify database schema: Check EntryState table
3. Review API responses in browser DevTools
4. Consult this documentation

## Examples

### Complete Homebrewing States Setup

```javascript
// Primary Ferment - Active
{
  "name": "Primary Ferment",
  "category": "active",
  "color": "#28a745",
  "display_order": 0,
  "is_default": true
}

// Secondary Ferment - Active
{
  "name": "Secondary Ferment",
  "category": "active",
  "color": "#17a2b8",
  "display_order": 1,
  "is_default": false
}

// Conditioning - Active
{
  "name": "Conditioning",
  "category": "active",
  "color": "#0d6efd",
  "display_order": 2,
  "is_default": false
}

// Racked - Inactive
{
  "name": "Racked",
  "category": "inactive",
  "color": "#ffc107",
  "display_order": 3,
  "is_default": false
}

// Bottled - Inactive
{
  "name": "Bottled",
  "category": "inactive",
  "color": "#fd7e14",
  "display_order": 4,
  "is_default": false
}

// Consumed - Inactive
{
  "name": "Consumed",
  "category": "inactive",
  "color": "#6c757d",
  "display_order": 5,
  "is_default": false
}

// Discarded - Inactive
{
  "name": "Discarded",
  "category": "inactive",
  "color": "#dc3545",
  "display_order": 6,
  "is_default": false
}
```
