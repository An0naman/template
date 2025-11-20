# 🌲 Hierarchy Tab Feature for Relationships Section V2

## Overview

Added a new **Hierarchy View** tab to the Relationships Section V2 that displays all related records in a directory-tree structure, showing parent-child relationships visually.

## 🎯 Features

### Two-Tab Interface
1. **Grouped View** (default) - Original card-based view with relationships grouped by type
2. **Hierarchy View** (new) - Tree structure showing parent-child relationships

### Hierarchy Tree Display
- **Visual directory-tree structure** - Shows relationships as expandable/collapsible nodes
- **Parent-child indicators** - Clear visual distinction between parents and children
- **Current entry highlighting** - The current record is highlighted with a "Current" badge
- **Entry type icons** - Each node shows its entry type with colored icon
- **Status badges** - Display entry status in the tree
- **Relationship labels** - Shows the relationship type for each connection
- **Clickable links** - Each node links to its entry detail page (opens in new tab)
- **Expand/collapse controls** - Toggle button for nodes with children

### Design Elements
- **Indentation** - Visual hierarchy with 20px indent per level
- **Color coding**:
  - Current entry: Blue highlight with left border
  - Parent entries: Cyan highlight with left border
- **Icons**: 
  - Directory icon (fa-sitemap) for the tab
  - Chevron down/right for expand/collapse
- **Smooth animations** - Collapse/expand transitions
- **Dark mode support** - Fully themed for light/dark modes

## 📁 Files Modified

### Template File
**File**: `/app/templates/sections/_relationships_section_v2.html`

**Changes**:
1. Added tab navigation structure (Grouped View / Hierarchy View)
2. Moved grouped view content into first tab panel
3. Added hierarchy view tab panel with loading state
4. Added comprehensive CSS for tree structure styling
5. Added JavaScript functions for hierarchy loading and rendering

## 🔧 Implementation Details

### HTML Structure
```html
<!-- Tabs Navigation -->
<ul class="nav nav-tabs">
  <li><button>Grouped View</button></li>
  <li><button>Hierarchy View</button></li>
</ul>

<!-- Tab Content -->
<div class="tab-content">
  <!-- Grouped View Tab -->
  <div class="tab-pane active" id="groupedTab">
    <!-- Original card-based view -->
  </div>
  
  <!-- Hierarchy View Tab -->
  <div class="tab-pane" id="hierarchyTab">
    <div id="hierarchyLoading">Loading...</div>
    <div id="hierarchyContent">
      <!-- Tree populated via JavaScript -->
    </div>
  </div>
</div>
```

### JavaScript Functions

#### `loadHierarchy()`
- Fetches hierarchy data from `/api/entries/{id}/relationships/hierarchy`
- Only loads once (lazy loading when tab is activated)
- Handles errors with retry button
- Shows loading spinner during fetch

#### `renderHierarchyTree(hierarchy, container)`
- Takes hierarchy data and renders complete tree
- Handles empty state
- Initializes tree toggle functionality

#### `renderTreeNode(node, level)`
- Recursive function to render each tree node
- Handles:
  - Indentation based on level
  - Toggle button for nodes with children
  - Entry type icon and color
  - Entry title as link
  - Current/Parent badges
  - Status badge
  - Relationship type label
  - Child nodes (recursive call)

#### `initializeTreeToggles()`
- Attaches click handlers to expand/collapse buttons
- Animates chevron icon rotation
- Toggles `collapsed` class on children containers

#### `setupTabListeners()`
- Listens for hierarchy tab activation
- Triggers hierarchy loading on first view

### CSS Classes

#### Tree Structure
- `.relationship-tree` - Container for entire tree
- `.tree-node` - Individual node wrapper
- `.tree-node-content` - Node content with hover effects
- `.tree-children` - Container for child nodes (collapsible)
- `.tree-children.collapsed` - Hidden state with animations

#### Tree Elements
- `.tree-toggle-btn` - Expand/collapse button
- `.tree-spacer` - Empty space for nodes without children
- `.tree-entry-type` - Entry type icon
- `.tree-entry-link` - Entry title link
- `.status-badge` - Status indicator

#### Special States
- `.current-entry` - Highlights the current record (blue)
- `.parent-entry` - Highlights parent records (cyan)

#### Utilities
- `.hierarchy-empty-state` - Empty state message

### Tab Styling
- Custom tab design with bottom border indicator
- Active tab highlighted in primary color
- Hover effects for inactive tabs

## 🚀 Usage

### For Users
1. Navigate to any entry detail page (v2)
2. Scroll to "Related Records" section
3. Click the **"Hierarchy View"** tab
4. View parent-child relationships in tree structure
5. Click chevron buttons to expand/collapse nodes
6. Click entry names to navigate to those records

### Tree Structure Example
```
├─ 📊 Project Alpha [Parent]
│  ├─ 📋 Current Entry [Current]
│  │  ├─ ✅ Task 1
│  │  ├─ ✅ Task 2
│  │  └─ ✅ Task 3
│  └─ 📋 Feature B
│     ├─ ✅ Task 4
│     └─ ✅ Task 5
```

## 🔌 API Endpoint Used

**Endpoint**: `GET /api/entries/<entry_id>/relationships/hierarchy`

**Response Format**:
```json
{
  "hierarchy": [
    {
      "id": 123,
      "title": "Project Alpha",
      "status": "Active",
      "is_parent": true,
      "entry_type": {
        "label": "Project",
        "icon": "fas fa-project-diagram",
        "color": "#0d6efd"
      },
      "children": [
        {
          "id": 456,
          "title": "Current Entry",
          "relationship_type": "Child of",
          "children": [...]
        }
      ]
    }
  ]
}
```

## ⚙️ Configuration

### Max Depth
The hierarchy API supports a `max_depth` parameter (default: 3) to limit tree depth and prevent performance issues.

### Relationship Detection
The hierarchy automatically detects parent-child relationships by looking for relationships with labels containing:
- "Parent" or "parent"
- "Contains"
- "Has"

## 🎨 Visual Features

### Indentation
Each level is indented by 20px to create visual hierarchy

### Icons
- Entry type icons with custom colors
- Expand/collapse chevrons
- Status and badge indicators

### Colors
- **Current Entry**: Blue background (#0d6efd with opacity)
- **Parent Entry**: Cyan background (#0dcaf0 with opacity)
- **Hover**: Secondary background color

### Animations
- Smooth expand/collapse with max-height transition
- Opacity fade for children
- Chevron rotation on toggle
- Hover effects on nodes

## 🌙 Dark Mode

All styles include dark mode support:
- Adjusted background colors
- Proper contrast for borders
- Themed text colors
- Icon color adjustments

## 📊 Benefits

### For Users
1. **Visual Understanding** - See relationship structure at a glance
2. **Quick Navigation** - Jump to any related entry easily
3. **Hierarchy Context** - Understand where an entry fits in the structure
4. **Parent-Child Clarity** - Easily distinguish relationship directions

### For Development
1. **Reuses Existing API** - No new backend endpoints needed
2. **Lazy Loading** - Only loads when tab is activated
3. **Performance** - Tree limited to 3 levels by default
4. **Maintainable** - Clean separation of concerns
5. **Extensible** - Easy to add more features

## 🔄 Future Enhancements

Potential improvements:
1. **Search in tree** - Filter/highlight nodes
2. **Drag and drop** - Reorganize relationships
3. **Context menu** - Right-click actions on nodes
4. **Export** - Download tree as image or text
5. **Different layouts** - Horizontal tree, radial tree
6. **Relationship strength** - Visual indicators for quantity/importance
7. **Multi-level expand/collapse** - Expand all, collapse all buttons
8. **Minimap** - Overview for large trees

## ✅ Testing

### Test Cases
1. ✓ Hierarchy loads when tab is activated
2. ✓ Empty state displays when no hierarchical relationships exist
3. ✓ Tree nodes expand and collapse correctly
4. ✓ Current entry is highlighted
5. ✓ Parent entries are highlighted
6. ✓ Links navigate to correct entries
7. ✓ Status badges display correctly
8. ✓ Entry type icons show with correct colors
9. ✓ Error handling with retry button works
10. ✓ Dark mode styling is correct
11. ✓ Responsive on mobile devices

### Browser Compatibility
- Chrome/Edge ✓
- Firefox ✓
- Safari ✓
- Mobile browsers ✓

## 📝 Notes

- The hierarchy view is independent of the grouped view
- Both views use the same underlying relationship data
- Hierarchy tab uses lazy loading for better performance
- Tree is limited to 3 levels deep by default (API parameter)
- The grouped view remains the default tab

---

**Implementation Date**: 2025-11-02  
**Status**: ✅ Complete  
**Version**: 1.0
