# Entry Layout Rendering - Implementation TODO

## Current Status ✅

### Completed
1. ✅ **Layout Builder UI** - Fully functional drag-and-drop interface
2. ✅ **Database Schema** - EntryTypeLayout and EntryLayoutSection tables
3. ✅ **API Layer** - All CRUD endpoints for managing layouts
4. ✅ **Service Layer** - Business logic for layout operations
5. ✅ **Layout Configuration** - Users can customize layouts per entry type
6. ✅ **Layout Data Loading** - entry_detail route now loads layout and passes to template

### What Users Can Do Now
- Navigate to "Manage Entry Types" 
- Click "Configure Layout" for any entry type
- See 13 available sections in the palette
- Drag sections onto the grid
- Resize sections by dragging corners
- Set exact sizes using width/height inputs in properties panel
- Configure section properties (title, visibility, collapsible, etc.)
- Save layouts

## What's Missing 🚧

### The Layout is Configured But Not Applied
The `entry_detail.html` template currently uses **hardcoded HTML structure** (9908 lines!). The layout configuration is now passed as `entry_layout` to the template, but the template doesn't use it yet.

### What Needs to Happen

#### Option 1: Modify Existing Template (Complex)
The current `entry_detail.html` would need to:
1. Check if `entry_layout` exists and has sections
2. Sort sections by `display_order` or grid position
3. Loop through `entry_layout.sections`
4. For each section, check `section_type` and render the appropriate content
5. Apply visibility, collapsible states, sizes from the layout config

**Challenges:**
- Template is 9908 lines - very complex
- Contains lots of hardcoded sections
- Would need extensive refactoring
- Risk of breaking existing functionality

#### Option 2: Create New Layout-Based Template (Recommended)
Create a new template that:
1. Uses GridStack or CSS Grid to render sections based on layout
2. Has modular section templates (one per section type)
3. Dynamically includes only visible sections
4. Applies configured sizes and properties

**Advantages:**
- Clean implementation
- Doesn't break existing template
- Can be tested separately
- Easier to maintain

## Implementation Plan (Option 2)

### Step 1: Create Section Templates
Create individual templates for each section type in `app/templates/sections/`:

```
app/templates/sections/
├── header.html          # Entry title, dates, status
├── notes.html           # Notes display
├── relationships.html   # Related entries
├── labels.html          # Category labels
├── sensors.html         # Sensor charts
├── reminders.html       # Scheduled reminders
├── ai_assistant.html    # AI chat interface
├── attachments.html     # File uploads
├── form_fields.html     # Custom entry type fields
├── qr_code.html         # QR code display
├── label_printing.html  # Label print interface
├── relationship_opportunities.html  # Suggested relationships
└── timeline.html        # Activity history
```

### Step 2: Create New Layout-Based Entry Detail Template
Create `app/templates/entry_detail_dynamic.html`:

```jinja2
{% extends "base.html" %}

{% block content %}
<div class="container-fluid">
    {% if entry_layout and entry_layout.sections %}
    
    {# Render using configured layout #}
    <div class="row g-3">
        {% for section in entry_layout.sections|sort(attribute='display_order') %}
            {% if section.is_visible %}
            <div class="col-12 col-md-{{ section.width }}">
                <div class="card {% if section.is_collapsible %}collapsible-section{% endif %}" 
                     style="min-height: {{ section.height * 80 }}px;">
                    
                    <div class="card-header">
                        <h5>{{ section.title }}</h5>
                        {% if section.is_collapsible %}
                        <button class="btn btn-sm btn-link" 
                                data-bs-toggle="collapse" 
                                data-bs-target="#section-{{ section.id }}">
                            <i class="fas fa-chevron-down"></i>
                        </button>
                        {% endif %}
                    </div>
                    
                    <div id="section-{{ section.id }}" 
                         class="card-body {% if section.default_collapsed %}collapse{% endif %}">
                        {% include 'sections/' + section.section_type + '.html' %}
                    </div>
                </div>
            </div>
            {% endif %}
        {% endfor %}
    </div>
    
    {% else %}
    {# Fallback to original template if no layout configured #}
    {% include 'entry_detail_original.html' %}
    {% endif %}
</div>
{% endblock %}
```

### Step 3: Update Route to Use New Template
Modify `app/routes/main_routes.py`:

```python
# Add parameter to toggle between layouts
use_dynamic_layout = params.get('use_dynamic_entry_layouts', False)

if use_dynamic_layout and layout:
    return render_template('entry_detail_dynamic.html', ...)
else:
    return render_template('entry_detail.html', ...)
```

### Step 4: Create Section Templates
Extract each section from the current `entry_detail.html` into modular templates.

For example, `sections/header.html`:
```jinja2
<div class="entry-header">
    <h1>{{ entry.title }}</h1>
    <p class="text-muted">{{ entry.description }}</p>
    <div class="entry-meta">
        <span class="badge" style="background-color: {{ entry.status_color }}">
            {{ entry.status }}
        </span>
        <span>Created: {{ entry.created_at }}</span>
    </div>
</div>
```

### Step 5: Add System Parameter
Add `use_dynamic_entry_layouts` to SystemParameters table:
```sql
INSERT INTO SystemParameters (key, value, description) 
VALUES ('use_dynamic_entry_layouts', 'false', 'Use configurable layouts for entry detail pages');
```

### Step 6: Testing
1. Set `use_dynamic_entry_layouts` to `true`
2. Visit an entry detail page
3. Verify sections render according to layout
4. Test collapsible sections
5. Test hiding/showing sections
6. Test different sizes

## Estimated Effort

- **Section Template Extraction**: 4-6 hours (13 sections × 20-30 min each)
- **Dynamic Template Creation**: 2-3 hours
- **Route Updates**: 30 minutes
- **Testing & Debugging**: 2-3 hours
- **Documentation**: 1 hour

**Total**: 10-14 hours of development work

## Quick Win Alternative

If you want to see layouts working immediately with minimal work:

### Quick Implementation (1-2 hours)
1. Create a simple version that only respects **visibility** and **order**
2. Don't worry about sizes/positioning yet
3. Just show/hide sections based on `is_visible`
4. Sort by `display_order`

This would let you:
- ✅ Hide unwanted sections
- ✅ Reorder sections
- ❌ Custom sizes (would use default responsive sizing)
- ❌ Grid positioning

Would you like me to implement the **Quick Win** version now, or would you prefer to plan for the full implementation?

## Current Workaround

For now, your layout configurations are **saved and working** in the layout builder, but they're not yet **applied** to the entry detail pages. The entry pages still show all sections in the original hardcoded order.

To see your layouts in action, we need to implement one of the approaches above.

