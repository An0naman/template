# Entry Layout Builder - Design Document

## Overview

The Entry Layout Builder feature introduces a configurable layout system for entry detail pages, similar to the Dashboard Builder. This allows administrators to customize the placement, size, and visibility of different sections within entry detail pages at the **entry type level** - meaning all entries of the same type will share the same layout configuration.

## Core Concept

Just as the Dashboard Builder allows users to:
- Create multiple dashboards
- Add/remove widgets
- Drag & drop widgets to rearrange
- Resize widgets
- Configure widget properties

The Entry Layout Builder will allow administrators to:
- Define custom layouts for each entry type
- Show/hide different sections (Notes, Relationships, Labels, etc.)
- Rearrange section placement via drag & drop
- Control section size and visibility
- Set default collapsed/expanded states

## Key Differences from Dashboard Builder

| Aspect | Dashboard Builder | Entry Layout Builder |
|--------|------------------|---------------------|
| **Scope** | User creates multiple dashboards | Admin configures per entry type |
| **Application** | Selected by user when viewing | Automatic based on entry type |
| **Persistence** | Per dashboard instance | Per entry type (affects all entries of that type) |
| **Components** | Widgets (dynamic data) | Sections (entry components) |
| **Users** | End users create/manage | Admin/config users only |

## Architecture

### Database Schema

#### EntryTypeLayout Table
Stores the overall layout configuration for each entry type.

```sql
CREATE TABLE EntryTypeLayout (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_type_id INTEGER NOT NULL UNIQUE,
    layout_config TEXT DEFAULT '{"cols": 12, "rowHeight": 80}', -- JSON grid configuration
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (entry_type_id) REFERENCES EntryType(id) ON DELETE CASCADE
);
```

#### EntryLayoutSection Table
Stores individual section configurations within an entry type layout.

```sql
CREATE TABLE EntryLayoutSection (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    layout_id INTEGER NOT NULL,
    section_type TEXT NOT NULL, -- 'header', 'notes', 'relationships', 'labels', 'sensors', 'reminders', 'ai_assistant', 'attachments', 'form_fields', 'qr_code', 'label_printing'
    title TEXT, -- Custom title (optional, defaults to section type's default)
    position_x INTEGER DEFAULT 0, -- Grid column position
    position_y INTEGER DEFAULT 0, -- Grid row position
    width INTEGER DEFAULT 12, -- Grid columns (1-12)
    height INTEGER DEFAULT 2, -- Grid rows
    is_visible INTEGER DEFAULT 1, -- 0 = hidden, 1 = visible
    is_collapsible INTEGER DEFAULT 1, -- Can the section be collapsed?
    default_collapsed INTEGER DEFAULT 0, -- Should it start collapsed?
    config TEXT DEFAULT '{}', -- JSON for section-specific settings
    display_order INTEGER DEFAULT 0, -- Fallback ordering when not using grid
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (layout_id) REFERENCES EntryTypeLayout(id) ON DELETE CASCADE
);
```

### Available Section Types

Based on the current `entry_detail.html` structure:

1. **header** - Entry title, description, status, dates
2. **notes** - Notes section with add/edit capabilities
3. **relationships** - Entry relationships display
4. **labels** - Labels/tags section (if enabled for entry type)
5. **sensors** - Sensor data and charts (if enabled for entry type)
6. **reminders** - Reminder management section
7. **ai_assistant** - AI assistant chat interface
8. **attachments** - File attachments section
9. **form_fields** - Custom form fields (if configured)
10. **qr_code** - QR code generation section
11. **label_printing** - Label printer integration
12. **relationship_opportunities** - Shared relationship suggestions
13. **note_relationships** - Note-to-note relationships
14. **timeline** - Progress timeline (if applicable)

### Default Section Configurations

Each section type has default settings:

```json
{
    "header": {
        "title": "Entry Details",
        "width": 12,
        "height": 3,
        "position_x": 0,
        "position_y": 0,
        "is_visible": 1,
        "is_collapsible": 0,
        "default_collapsed": 0,
        "config": {
            "show_dates": true,
            "show_status": true,
            "show_description": true
        }
    },
    "notes": {
        "title": "Notes",
        "width": 6,
        "height": 4,
        "position_x": 0,
        "position_y": 3,
        "is_visible": 1,
        "is_collapsible": 1,
        "default_collapsed": 0,
        "config": {
            "default_note_type": "General",
            "show_note_relationships": true
        }
    },
    "relationships": {
        "title": "Relationships",
        "width": 6,
        "height": 4,
        "position_x": 6,
        "position_y": 3,
        "is_visible": 1,
        "is_collapsible": 1,
        "default_collapsed": 0,
        "config": {
            "show_add_button": true
        }
    },
    "sensors": {
        "title": "Sensor Data",
        "width": 12,
        "height": 5,
        "position_x": 0,
        "position_y": 7,
        "is_visible": 1,
        "is_collapsible": 1,
        "default_collapsed": 0,
        "config": {
            "default_chart_type": "line",
            "default_time_range": "7d"
        }
    },
    "ai_assistant": {
        "title": "AI Assistant",
        "width": 12,
        "height": 4,
        "position_x": 0,
        "position_y": 12,
        "is_visible": 1,
        "is_collapsible": 1,
        "default_collapsed": 1,
        "config": {
            "auto_open": false
        }
    }
}
```

## Backend Components

### 1. Service Layer: `app/services/entry_layout_service.py`

Handles business logic for entry layouts:

```python
class EntryLayoutService:
    
    @staticmethod
    def get_layout_for_entry_type(entry_type_id):
        """Get the layout configuration for an entry type"""
        # Returns layout with all sections
        
    @staticmethod
    def create_default_layout(entry_type_id):
        """Create default layout when entry type is created"""
        # Creates standard layout based on entry type capabilities
        
    @staticmethod
    def update_section_positions(layout_id, sections_data):
        """Update positions of multiple sections at once"""
        
    @staticmethod
    def toggle_section_visibility(section_id, is_visible):
        """Show/hide a section"""
        
    @staticmethod
    def reset_to_default_layout(entry_type_id):
        """Reset layout to default configuration"""
```

### 2. API Layer: `app/api/entry_layout_api.py`

RESTful API endpoints:

```python
# Layout Management
GET    /api/entry-types/<int:entry_type_id>/layout
POST   /api/entry-types/<int:entry_type_id>/layout
PUT    /api/entry-types/<int:entry_type_id>/layout
DELETE /api/entry-types/<int:entry_type_id>/layout/reset

# Section Management
GET    /api/entry-layouts/<int:layout_id>/sections
POST   /api/entry-layouts/<int:layout_id>/sections
PUT    /api/entry-layouts/<int:layout_id>/sections/<int:section_id>
DELETE /api/entry-layouts/<int:layout_id>/sections/<int:section_id>
PATCH  /api/entry-layouts/<int:layout_id>/sections/positions  # Bulk update

# Section Types (for UI builder)
GET    /api/entry-layouts/available-sections
```

### 3. Routes: `app/routes/entry_layout_routes.py`

```python
@entry_layout_bp.route('/admin/entry-layout-builder/<int:entry_type_id>')
def entry_layout_builder(entry_type_id):
    """Layout builder interface for administrators"""
```

## Frontend Components

### 1. Layout Builder Interface
**Template:** `app/templates/entry_layout_builder.html`

Similar to dashboard.html, provides:
- Drag-and-drop grid interface (using GridStack.js)
- Section library/palette
- Configuration panels for each section
- Preview mode
- Save/Reset functionality

**Features:**
- Visual grid editor
- Section properties panel
- Real-time preview
- Section visibility toggles
- Collapse state controls

### 2. Entry Detail Renderer
**Template:** `app/templates/entry_detail.html` (modified)

Changes needed:
- Load layout configuration from database
- Dynamically render sections based on layout
- Apply position, size, and visibility settings
- Respect collapse states
- Maintain existing functionality

**JavaScript:** `app/static/js/entry_layout_renderer.js`

```javascript
class EntryLayoutRenderer {
    constructor(entryTypeId, entryId) {
        this.entryTypeId = entryTypeId;
        this.entryId = entryId;
        this.layout = null;
        this.sections = [];
    }
    
    async loadLayout() {
        // Fetch layout configuration
    }
    
    async renderSections() {
        // Render sections in grid
    }
    
    initializeGridStack() {
        // Setup GridStack (read-only for end users)
    }
}
```

## User Experience Flow

### For Administrators (Layout Configuration)

1. Navigate to "Manage Entry Types"
2. Click "Configure Layout" button for an entry type
3. Opens Layout Builder interface with:
   - Current layout displayed in grid
   - Section palette on the side
   - Properties panel
4. Admin can:
   - Drag sections to rearrange
   - Resize sections
   - Hide/show sections
   - Configure section properties
   - Add/remove optional sections
5. Click "Save Layout" to persist
6. Option to "Reset to Default" if needed

### For End Users (Viewing Entries)

1. Navigate to entry detail page
2. Entry renders with configured layout
3. Layout is automatic based on entry type
4. Sections appear in configured positions/sizes
5. Hidden sections don't appear
6. Collapsible sections respect default states
7. All existing functionality remains intact

## Migration Strategy

### Phase 1: Database Schema
1. Create migration script `migrations/add_entry_layout_tables.py`
2. Add new tables: `EntryTypeLayout` and `EntryLayoutSection`
3. Create default layouts for existing entry types

### Phase 2: Backend Implementation
1. Create `EntryLayoutService`
2. Create `entry_layout_api.py` with all endpoints
3. Add routes for layout builder interface

### Phase 3: Frontend - Layout Builder
1. Create `entry_layout_builder.html`
2. Create `entry_layout_builder.js`
3. Integrate with "Manage Entry Types" page

### Phase 4: Frontend - Entry Renderer
1. Modify `entry_detail.html` to support dynamic layouts
2. Create `entry_layout_renderer.js`
3. Test with various layout configurations

### Phase 5: Testing & Documentation
1. Test all section types
2. Test various layout configurations
3. Create user documentation
4. Create admin guide

## Configuration Options

### Global Settings
Accessed via system parameters or dedicated settings:

- **Enable Layout Builder**: Toggle feature on/off
- **Allow Per-Entry Overrides**: Future enhancement
- **Default Grid Columns**: 12 (standard)
- **Default Row Height**: 80px
- **Minimum Section Width**: 3 columns
- **Minimum Section Height**: 1 row

### Per-Section Settings

Each section type can have specific configuration:

**Notes Section:**
- Default note type
- Show note relationships toggle
- Allow inline editing
- Display mode (list/card)

**Sensors Section:**
- Default chart type
- Default time range
- Visible sensor types
- Chart height

**Relationships Section:**
- Group by relationship type
- Show counts
- Allow quick add

**AI Assistant Section:**
- Auto-open on page load
- Default prompt
- Context depth

## API Examples

### Get Layout for Entry Type

```http
GET /api/entry-types/1/layout

Response:
{
    "id": 1,
    "entry_type_id": 1,
    "layout_config": {"cols": 12, "rowHeight": 80},
    "sections": [
        {
            "id": 1,
            "section_type": "header",
            "title": "Entry Details",
            "position_x": 0,
            "position_y": 0,
            "width": 12,
            "height": 2,
            "is_visible": 1,
            "is_collapsible": 0,
            "default_collapsed": 0,
            "config": {}
        },
        {
            "id": 2,
            "section_type": "notes",
            "title": "Notes",
            "position_x": 0,
            "position_y": 2,
            "width": 6,
            "height": 4,
            "is_visible": 1,
            "is_collapsible": 1,
            "default_collapsed": 0,
            "config": {"default_note_type": "General"}
        }
    ]
}
```

### Update Section Positions (Bulk)

```http
PATCH /api/entry-layouts/1/sections/positions
Content-Type: application/json

{
    "sections": [
        {"id": 1, "position_x": 0, "position_y": 0, "width": 12, "height": 2},
        {"id": 2, "position_x": 0, "position_y": 2, "width": 8, "height": 4},
        {"id": 3, "position_x": 8, "position_y": 2, "width": 4, "height": 4}
    ]
}

Response:
{
    "message": "Section positions updated successfully",
    "updated_count": 3
}
```

### Toggle Section Visibility

```http
PUT /api/entry-layouts/1/sections/5
Content-Type: application/json

{
    "is_visible": 0
}

Response:
{
    "message": "Section visibility updated",
    "section": {
        "id": 5,
        "section_type": "ai_assistant",
        "is_visible": 0
    }
}
```

## Benefits

### 1. Flexibility
- Customize entry layouts per type
- Show only relevant sections
- Optimize space usage

### 2. User Experience
- Cleaner, more focused interfaces
- Reduced clutter
- Better mobile responsiveness

### 3. Scalability
- Easy to add new section types
- Supports future enhancements
- Backward compatible

### 4. Consistency
- All entries of same type look the same
- Predictable user experience
- Easier training

## Future Enhancements

1. **Per-Entry Overrides**: Allow individual entries to override type layout
2. **Layout Templates**: Pre-defined layout templates (compact, detailed, mobile, etc.)
3. **Section Variants**: Different rendering styles for same section
4. **Conditional Sections**: Show sections based on entry state or data
5. **Layout Versioning**: Track layout changes over time
6. **Import/Export Layouts**: Share layouts between systems
7. **Layout Analytics**: Track which sections users interact with most
8. **Responsive Breakpoints**: Different layouts for mobile/tablet/desktop

## Implementation Checklist

### Database
- [ ] Create `EntryTypeLayout` table
- [ ] Create `EntryLayoutSection` table
- [ ] Add indexes for performance
- [ ] Create migration script
- [ ] Generate default layouts for existing entry types

### Backend
- [ ] Create `EntryLayoutService` class
- [ ] Implement all service methods
- [ ] Create `entry_layout_api.py` blueprint
- [ ] Implement all API endpoints
- [ ] Add routes for layout builder
- [ ] Add authorization checks (admin only)

### Frontend - Layout Builder
- [ ] Create `entry_layout_builder.html`
- [ ] Create `entry_layout_builder.js`
- [ ] Integrate GridStack.js
- [ ] Build section palette UI
- [ ] Build properties panel
- [ ] Add save/reset functionality
- [ ] Add to "Manage Entry Types" page

### Frontend - Entry Renderer
- [ ] Modify `entry_detail.html` for dynamic rendering
- [ ] Create `entry_layout_renderer.js`
- [ ] Implement section factory pattern
- [ ] Handle collapsible sections
- [ ] Handle visibility states
- [ ] Test all section types

### Testing
- [ ] Unit tests for service layer
- [ ] API endpoint tests
- [ ] Layout rendering tests
- [ ] Cross-browser testing
- [ ] Mobile responsiveness testing
- [ ] Performance testing with complex layouts

### Documentation
- [ ] Admin user guide
- [ ] End user documentation
- [ ] API documentation
- [ ] Migration guide
- [ ] Troubleshooting guide

## Technical Considerations

### Performance
- Cache layout configurations
- Lazy load section content
- Minimize API calls
- Optimize grid rendering

### Security
- Restrict layout editing to admins
- Validate section configurations
- Sanitize user inputs
- Prevent XSS in custom titles

### Compatibility
- Maintain backward compatibility
- Graceful fallback for missing layouts
- Support existing entry detail functionality
- Progressive enhancement approach

### Accessibility
- Maintain keyboard navigation
- Preserve screen reader compatibility
- Ensure proper heading hierarchy
- Maintain ARIA labels

## Comparison with Dashboard Builder

### Similarities
- Grid-based layout system (GridStack.js)
- Drag-and-drop interface
- Position and size configuration
- JSON-based config storage
- RESTful API architecture
- Similar UI patterns

### Differences
- **Scope**: Entry type vs. user preference
- **Audience**: Admins vs. end users
- **Content**: Static sections vs. dynamic widgets
- **Data**: Entry components vs. aggregated data
- **Persistence**: Entry type-level vs. dashboard-level
- **Flexibility**: Predefined sections vs. custom widgets

## Conclusion

The Entry Layout Builder brings the power and flexibility of the Dashboard Builder to entry detail pages, allowing administrators to create optimized, type-specific layouts that enhance user experience and reduce clutter. By leveraging the same grid-based architecture and drag-and-drop interface, it provides a consistent configuration experience while serving a distinct use case in the application.
