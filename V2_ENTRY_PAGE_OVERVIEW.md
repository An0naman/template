# V2 Entry Page - End-to-End Overview

**Date:** October 28, 2025  
**Purpose:** Comprehensive documentation of the v2 entry detail page architecture

---

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Route Handler](#route-handler)
3. [Layout Service](#layout-service)
4. [Template Structure](#template-structure)
5. [Section Components](#section-components)
6. [API Endpoints](#api-endpoints)
7. [JavaScript Integration](#javascript-integration)
8. [Data Flow](#data-flow)
9. [Current Implementation Status](#current-implementation-status)

---

## Architecture Overview

The v2 entry page uses a **dynamic grid-based layout system** that allows customizable section positioning and visibility per entry type.

### Key Features
- **Grid-based layout** with 12-column Bootstrap grid
- **Dynamic section rendering** based on entry type configuration
- **Collapsible sections** with smooth animations
- **Responsive design** with mobile-first approach
- **Modular section components** for easy extension
- **Entry Layout Builder** for visual configuration

### Technology Stack
- **Backend:** Flask + SQLite
- **Frontend:** Bootstrap 5.3.3, Chart.js, Marked.js (Markdown)
- **Dynamic Rendering:** Jinja2 templates with include system
- **State Management:** Section visibility toggles via JavaScript

---

## Route Handler

**File:** `/app/routes/main_routes.py`

### Route: `/entry/<int:entry_id>/v2`

```python
@main_bp.route('/entry/<int:entry_id>/v2')
def entry_detail_v2(entry_id):
    """Alternative entry detail page using v2 template with dynamic layout"""
```

### Data Fetching Process

1. **Get Entry Data** (Lines 266-282)
   - Fetches entry details with JOIN to EntryType and EntryState
   - Includes: title, description, status, dates, entry type config
   - Returns 404 if entry not found

2. **Build Entry Dictionary** (Lines 284-303)
   - Normalizes entry data into standardized format
   - Handles boolean conversions and default values
   - Includes entry type configuration (sensors, labels, dates)

3. **Get Layout Configuration** (Lines 305-308)
   ```python
   layout_service = EntryLayoutService()
   layout = layout_service.get_layout_for_entry_type(entry_data.get('entry_type_id'))
   ```

4. **Build Section Configuration** (Lines 310-348)
   - Creates `section_config` dictionary with visibility and display settings
   - Generates `section_rows` array grouping sections by Y-coordinate (row)
   - Creates `section_order` array for sequential section ordering
   - Groups sections by Y position, sorts by X within each row

5. **Render Template** (Lines 353-358)
   ```python
   return render_template('entry_detail_v2.html',
                          project_name=params.get('project_name'),
                          entry=entry_data,
                          section_config=section_config,
                          section_order=section_order,
                          section_rows=section_rows)
   ```

### Context Variables Passed to Template

| Variable | Type | Purpose |
|----------|------|---------|
| `project_name` | String | System name for title/branding |
| `entry` | Dict | Complete entry data with all fields |
| `section_config` | Dict | Section settings keyed by section_type |
| `section_order` | List | Ordered list of visible section types |
| `section_rows` | List[List] | 2D array: rows containing section types |

---

## Layout Service

**File:** `/app/services/entry_layout_service.py`

### EntryLayoutService Class

Manages entry type layouts and section configurations.

### Default Sections Configuration

**Visible by Default:**
1. **header** - Row 0, Full width (12 cols), Height 3
2. **ai_assistant** - Row 1, Full width (12 cols), Height 4
3. **sensors** - Row 2, Left side (7 cols), Height 5
4. **notes** - Row 2, Right side (5 cols), Height 5

**Hidden by Default:**
- relationships
- labels
- reminders
- attachments
- form_fields
- qr_code
- relationship_opportunities
- timeline

### Section Configuration Schema

```python
{
    'section_type': {
        'title': 'Section Display Title',
        'section_type': 'unique_identifier',
        'position_x': 0-11,      # Grid column start (0-11)
        'position_y': 0-N,       # Grid row (Y coordinate)
        'width': 1-12,           # Column span (1-12)
        'height': 1-12,          # Relative height units
        'is_visible': 0/1,       # Show/hide section
        'is_collapsible': 0/1,   # Can user collapse it?
        'default_collapsed': 0/1, # Start collapsed?
        'display_order': int,    # Sequential ordering
        'config': {}             # Section-specific settings
    }
}
```

### Key Methods

1. `get_layout_for_entry_type(entry_type_id)` - Fetches or creates layout
2. `create_default_layout(entry_type_id)` - Initializes DEFAULT_SECTIONS
3. `get_sections_for_layout(layout_id)` - Returns all sections for a layout

---

## Template Structure

**File:** `/app/templates/entry_detail_v2.html`

### HTML Structure

```html
<!DOCTYPE html>
<html data-bs-theme="...">
<head>
    <!-- Bootstrap 5.3.3 -->
    <!-- Font Awesome -->
    <!-- Chart.js + date-fns adapter -->
    <!-- Marked.js for Markdown -->
    <!-- Dynamic theme CSS -->
    <!-- Markdown content styles -->
    <!-- Clean base styles with CSS variables -->
</head>
<body>
    <div class="container-fluid py-3">
        <!-- DEBUG comments showing section_rows and section_config -->
        
        <!-- Loop through rows -->
        {% for row in section_rows %}
            <div class="row g-4 mb-4">
                
                <!-- Loop through sections in row -->
                {% for section_type in row %}
                    <div class="col-12 col-lg-{{ width }} section-wrapper">
                        <div class="content-section theme-section">
                            <div class="section-content">
                                <!-- Section header -->
                                <!-- Section-specific include -->
                                {% if section_type == 'header' %}
                                    {% include 'sections/_header_section.html' %}
                                {% elif section_type == 'ai_assistant' %}
                                    {% include 'sections/_ai_assistant_section.html' %}
                                {% elif section_type == 'sensors' %}
                                    {% include 'sections/_sensors_section.html' %}
                                <!-- ... other sections ... -->
                                {% endif %}
                            </div>
                        </div>
                    </div>
                {% endfor %}
                
            </div>
        {% endfor %}
    </div>
    
    <!-- Modals -->
    {% include 'sections/_sensors_modals.html' %}
    
    <!-- Scripts -->
    <script>const entryId = {{ entry.id }};</script>
    <script src="...sensors.js"></script>
    <script>/* Markdown rendering */</script>
</body>
</html>
```

### CSS Architecture

#### CSS Custom Properties
```css
:root {
    --content-spacing: 1rem;
    --border-radius: 0.5rem;
    --shadow-sm, --shadow-md, --shadow-lg
    --transition-base: all 0.2s ease;
}
```

#### Key CSS Classes

**`.content-section`** - Main section container
- Background with theme variables
- Border with accent color on left
- Shadow and hover effects
- Smooth transitions

**`.section-wrapper`** - Section positioning wrapper
- Flexbox container for equal heights
- Animation support (slideIn/slideOut)
- Transform-origin: top

**`.info-card`** - Information display cards
- Used in header section for details/dates
- Themed background and borders

**Animations:**
```css
@keyframes slideOut { /* Collapse animation */ }
@keyframes slideIn { /* Expand animation */ }
```

#### Responsive Design
```css
@media (max-width: 991.98px) {
    /* Mobile: vertical stacking */
    /* Reduced padding/margins */
    /* Auto heights instead of fixed */
}
```

---

## Section Components

**Directory:** `/app/templates/sections/`

### 1. Header Section
**File:** `_header_section.html` (593 lines)

**Features:**
- Entry title (editable inline)
- Action buttons (Back, Edit, Delete)
- Section toggle buttons (for collapsible sections)
- Info cards: Details (Type, Status) and Dates (Created, End Dates)
- Edit/View mode switching
- Status badge with color coding

**Key Elements:**
```html
<h1 id="entryTitle">{{ entry.title }}</h1>
<div class="btn-group"><!-- Action buttons --></div>
<div class="btn-group"><!-- Section toggles --></div>
<div class="row">
    <div class="col-md-4"><!-- Details card --></div>
    <div class="col-md-8"><!-- Dates card --></div>
</div>
```

### 2. AI Assistant Section
**File:** `_ai_assistant_section.html` (353 lines)

**Features:**
- Chat interface with history
- Quick action prompts
- Description generation/refinement
- Conversation mode
- Draft preview capability

**JavaScript Functions:**
- `quickPrompt(prompt)` - Set and send prompt
- `selectAction(action, prompt, displayName, iconName)` - Choose AI action
- `sendChatMessage()` - Send message to API
- `updateDraft()` - Refine current draft

**API Integration:**
```javascript
fetch('/api/ai/chat', {
    method: 'POST',
    body: JSON.stringify({
        message: message,
        entry_id: {{ entry.id }},
        action: actionToSend,
        chat_history: chatHistory
    })
})
```

### 3. Sensors Section
**File:** `_sensors_section.html` (EMPTY)

**Note:** Currently empty, functionality likely in sensors.js

### 4. Sensors Modals
**File:** `_sensors_modals.html`

Contains modal dialogs for sensor data management.

### 5. Timeline Section
**File:** `_timeline_section.html`

Progress timeline visualization.

### Placeholder Sections (Not Yet Implemented)
- **notes** - Notes management
- **relationships** - Entry relationships
- **labels** - Label printing and QR codes
- **reminders** - Reminder management
- **attachments** - File attachments
- **form_fields** - Custom fields
- **qr_code** - QR code generation
- **label_printing** - Label printer integration
- **relationship_opportunities** - Shared relationships

---

## API Endpoints

**Directory:** `/app/api/`

### Entry API (`entry_api.py`)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/entries` | GET | Get all entries |
| `/api/entries/sensor-enabled` | GET | Get entries with sensors |
| `/api/entries` | POST | Create new entry |
| `/api/entries/<id>` | GET | Get single entry |
| `/api/entries/<id>` | PUT | Update entry |
| `/api/entries/<id>` | DELETE | Delete entry |

### Entry Layout API (`entry_layout_api.py`)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/entry-types/<id>/layout` | GET | Get layout config |
| `/api/entry-types/<id>/layout` | POST | Create layout |
| `/api/entry-types/<id>/layout` | PUT | Update layout |
| `/api/entry-types/<id>/layout/sections` | GET | Get all sections |
| `/api/entry-types/<id>/layout/sections` | POST | Add section |
| `/api/entry-layout/sections/<id>` | GET | Get section |
| `/api/entry-layout/sections/<id>` | PUT | Update section |
| `/api/entry-layout/sections/<id>` | DELETE | Delete section |
| `/api/entry-types/<id>/layout/sections/bulk-update` | PATCH | Bulk update positions |

### AI API (`ai_api.py`)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/ai/chat` | POST | AI assistant chat |
| `/api/ai/entry-chat` | POST | Entry-context conversation |

### Other Relevant APIs
- **Notes API** (`notes_api.py`) - Note management
- **Relationships API** (`relationships_api.py`) - Relationship management
- **Labels API** (`labels_api.py`) - Label management
- **Theme API** (`theme_api.py`) - Theme settings

---

## JavaScript Integration

### Global Variables
```javascript
const entryId = {{ entry.id }};  // Entry ID for API calls
```

### External Scripts
1. **Bootstrap 5.3.3** - UI components and modals
2. **Chart.js 4.4.0** - Sensor data visualization
3. **chartjs-adapter-date-fns 3.0.0** - Time-series charts
4. **sensors.js** - Sensor data management functions
5. **Marked.js** - Markdown rendering

### Inline Scripts

#### Markdown Rendering
```javascript
function renderMarkdown(element) {
    const markdownText = element.textContent.trim();
    element.innerHTML = marked.parse(markdownText);
}

document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.markdown-content').forEach(renderMarkdown);
});
```

### Section Toggle Functionality (Expected)
```javascript
function toggleSection(sectionType) {
    // Toggle section visibility with animation
    // Update button state
    // Save preference to localStorage/API
}
```

---

## Data Flow

### 1. Page Load Sequence

```
User Request: /entry/123/v2
    ↓
Route Handler: entry_detail_v2()
    ↓
Database Query: Entry + EntryType + EntryState
    ↓
Layout Service: get_layout_for_entry_type()
    ↓
Database Query: EntryLayout + EntryLayoutSection
    ↓
Build Context:
    - entry (dict)
    - section_config (dict)
    - section_rows (list of lists)
    - section_order (list)
    ↓
Render Template: entry_detail_v2.html
    ↓
Loop section_rows:
    For each row:
        For each section_type:
            Check section_config visibility
            Include section template
    ↓
Client-side JavaScript:
    - Initialize charts (sensors.js)
    - Render markdown
    - Attach event handlers
```

### 2. Section Rendering Logic

```python
# Template rendering loop
for row in section_rows:  # [[header], [ai_assistant], [sensors, notes]]
    for section_type in row:  # 'sensors', 'notes', etc.
        config = section_config[section_type]
        if config['visible']:
            # Render with proper Bootstrap columns
            # col-12 col-lg-{{ config.width }}
            # Include appropriate section template
```

### 3. Section Configuration Flow

```
EntryLayoutService.DEFAULT_SECTIONS (in code)
    ↓
create_default_layout() - On first access
    ↓
INSERT INTO EntryLayout
INSERT INTO EntryLayoutSection (for each section)
    ↓
get_layout_for_entry_type() - On subsequent access
    ↓
SELECT from database
    ↓
Return layout dict with sections array
    ↓
Route handler builds section_config, section_rows
```

---

## Current Implementation Status

### ✅ Fully Implemented

1. **Core Architecture**
   - Route handler with layout service integration
   - Dynamic section rendering system
   - Grid-based responsive layout
   - Section visibility configuration

2. **Header Section**
   - Entry title and metadata display
   - Action buttons (Edit, Delete, Back)
   - Section toggle buttons
   - Status badge with colors
   - Info cards for details and dates

3. **AI Assistant Section**
   - Chat interface
   - Quick action prompts
   - Description generation
   - Conversation mode
   - API integration

4. **Layout Builder**
   - Visual grid-based editor
   - Drag and drop section positioning
   - Visibility toggles
   - Section configuration
   - Entry Layout Builder page at `/entry-layout-builder/<entry_type_id>`

5. **Styling System**
   - Theme-aware CSS variables
   - Responsive design
   - Section animations
   - Mobile optimization

### ⚠️ Partially Implemented

1. **Sensors Section**
   - Template file exists but is empty
   - JavaScript file exists (`sensors.js`)
   - Modals file exists
   - Likely functional but needs verification

2. **Timeline Section**
   - Include statement exists
   - Implementation status unclear

### ❌ Not Yet Implemented (Placeholders Only)

1. **Notes Section** - Shows placeholder text
2. **Relationships Section** - Shows placeholder text
3. **Labels Section** - Shows placeholder text
4. **Reminders Section** - Shows placeholder text
5. **Attachments Section** - Shows placeholder text
6. **Form Fields Section** - Shows placeholder text
7. **QR Code Section** - Shows placeholder text
8. **Label Printing Section** - Shows placeholder text
9. **Relationship Opportunities Section** - Shows placeholder text

### 📋 Missing Features

1. **Section Toggle JavaScript**
   - Toggle button handlers not implemented
   - Animation state management needed
   - Preference persistence (localStorage or API)

2. **Edit Mode Functionality**
   - Entry title editing
   - Details/status editing
   - Save/cancel handlers
   - API calls for updates

3. **Delete Functionality**
   - Confirmation modal
   - API call to delete entry
   - Redirect after deletion

---

## Next Steps & Recommendations

### High Priority

1. **Implement Missing Section Components**
   - Create `_notes_section.html` with note management
   - Create `_relationships_section.html` with relationship CRUD
   - Create `_labels_section.html` with label/QR features
   - Populate `_sensors_section.html` (currently empty)

2. **Complete Header Section Functionality**
   - Implement edit mode JavaScript
   - Add save/cancel handlers
   - Connect to entry update API
   - Add delete confirmation modal

3. **Section Toggle System**
   - Implement `toggleSection(sectionType)` function
   - Add smooth show/hide animations
   - Persist user preferences
   - Update toggle button states

### Medium Priority

4. **Sensors Section**
   - Verify sensors.js integration
   - Add inline documentation
   - Test chart rendering
   - Ensure responsive behavior

5. **API Documentation**
   - Document request/response formats
   - Add error handling examples
   - Include authentication if needed

6. **Testing**
   - Test all section layouts
   - Verify mobile responsiveness
   - Test edit/delete workflows
   - Browser compatibility testing

### Low Priority

7. **Performance Optimization**
   - Lazy load section content
   - Debounce API calls
   - Optimize chart rendering
   - Cache layout configurations

8. **Accessibility**
   - Add ARIA labels
   - Keyboard navigation
   - Screen reader support
   - Focus management

9. **Documentation**
   - Developer guide for adding sections
   - User guide for layout builder
   - API reference documentation

---

## Configuration Files

### Database Schema Tables

**EntryLayout**
- `id` - Primary key
- `entry_type_id` - Foreign key to EntryType
- `name` - Layout name
- `created_at`, `updated_at` - Timestamps

**EntryLayoutSection**
- `id` - Primary key
- `layout_id` - Foreign key to EntryLayout
- `section_type` - Section identifier (header, notes, etc.)
- `title` - Display title
- `position_x`, `position_y` - Grid coordinates
- `width`, `height` - Size in grid units
- `is_visible`, `is_collapsible`, `default_collapsed` - Boolean flags
- `display_order` - Sequential ordering
- `config` - JSON configuration
- `created_at`, `updated_at` - Timestamps

---

## Summary

The v2 entry page represents a **modern, flexible architecture** for displaying entry details with:

✅ **Strengths:**
- Dynamic, configurable layouts per entry type
- Clean separation of concerns (routes, services, templates)
- Grid-based responsive design
- Modular section system for easy extension
- Theme-aware styling with CSS variables
- AI assistant integration
- Visual layout builder

⚠️ **Gaps:**
- Many sections not yet implemented (placeholders)
- Edit/delete functionality incomplete
- Section toggle JavaScript missing
- Sensors section template empty

🎯 **Architecture Grade:** A-
The foundation is excellent with proper MVC separation, service layer, and extensible design. Implementation completion is the main gap.

📊 **Completion Estimate:** ~40% implemented
- Core: 100%
- Header: 90% (missing JS handlers)
- AI Assistant: 95%
- Other sections: 5% (placeholders only)

---

**End of V2 Entry Page Overview**
