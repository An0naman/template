# Macro-Based Entry Layout Implementation Guide

## ✅ Completed So Far

1. **Created Macro System** (`app/templates/macros/entry_sections.html`)
   - Main `render_section()` macro that routes to specific section renderers
   - `section_wrapper()` macro for consistent responsive layout
   - Individual section macros for each type (13 total)

2. **Created Partial Template** (`app/templates/partials/_entry_header_content.html`)
   - Extracted header section content as proof of concept
   
3. **Imported Macros** in `entry_detail.html` (line ~2067)
   ```jinja2
   {% from 'macros/entry_sections.html' import render_section %}
   ```

## 🔧 Next Steps

### Option A: Quick Implementation (Recommended)

Replace the hardcoded sections in `entry_detail.html` with a simple loop.

**Current structure** (lines ~2072-3000):
```jinja2
<div class="container-fluid">
    <!-- Header Section (lines 2074-2362) -->
    {% if section_visible.get('header', {}).get('visible', True) %}
    <div class="row">
        ...header content...
    </div>
    {% endif %}
    
    <!-- Label Printing Section (lines 2364-2434) -->
    {% set label_printing_visible = ... %}
    ...
    
    <!-- Sensors Section (lines 2442-2623) -->
    ...
    
    <!-- AI Assistant Section (lines 2625-2730) -->
    ...
    
    <!-- Notes Section (lines 2732-3000) -->
    ...
</div>
```

**New structure**:
```jinja2
<div class="container-fluid">
    {% for section_type in section_order %}
        {{ render_section(section_type, entry) }}
    {% endfor %}
</div>
```

### How to Implement

#### Step 1: Find the Main Content Container

In `entry_detail.html`, locate line ~2072 where it says:
```jinja2
<div class="container-fluid">
```

#### Step 2: Add the Dynamic Section Loop

Replace everything from line ~2074 to line ~3002 (where sections end and modals begin) with:

```jinja2
<div class="container-fluid">
    {# Render all sections dynamically based on layout configuration #}
    {% for section_type in section_order %}
        {{ render_section(section_type, entry, {
            'allowed_file_types': allowed_file_types,
            'max_file_size': max_file_size
        }) }}
    {% endfor %}
</div>

<!-- Everything below this point stays the same: modals, scripts, etc. -->
```

#### Step 3: Update the Macro to Include Inline Content

Since creating 13 separate partial files is tedious, modify `entry_sections.html` to include content inline using blocks. For example:

```jinja2
{% macro header_section(config, entry, context_data) %}
    {% call section_wrapper('header', config) %}
        {% if config.get('collapsible', False) %}
        <div class="section-header d-flex justify-content-between align-items-center mb-3 px-3 pt-3">
            <h4 class="section-title mb-0">
                <i class="fas fa-info-circle me-2"></i>{{ config.get('title', 'Entry Details') }}
            </h4>
            <button class="btn btn-sm btn-outline-secondary" type="button" 
                    data-bs-toggle="collapse" data-bs-target="#headerSectionContent">
                <i class="fas fa-chevron-{{ 'down' if config.get('collapsed', False) else 'up' }}"></i>
            </button>
        </div>
        {% endif %}
        
        <div class="section-content {{ 'px-3 pb-3' if config.get('collapsible', False) else '' }}">
            {# Copy the actual header HTML content here from lines 2100-2360 of entry_detail.html #}
            <div class="d-flex flex-column flex-md-row...
            ...all the header content...
        </div>
    {% endcall %}
{% endmacro %}
```

##  Alternative: Hybrid Approach (Easier)

Instead of refactoring everything at once, keep the existing code but add a check at the beginning of each section:

### Before (current):
```jinja2
<!-- Header Section -->
{% if section_visible.get('header', {}).get('visible', True) %}
<div class="row">
    <div class="col-12 col-md-{{ header_width }}">
        ... content ...
    </div>
</div>
{% endif %}
```

### After (hybrid):
```jinja2
<!-- Header Section -->
{% if 'header' in section_order and section_visible.get('header', {}).get('visible', True) %}
<div class="row">
    <div class="col-12 col-md-{{ header_width }}">
        ... content ...
    </div>
</div>
{% endif %}
```

Then wrap all sections in a block that respects order:

```jinja2
<div class="container-fluid">
    {% for section_type in section_order %}
        {% if section_type == 'header' and section_visible.get('header', {}).get('visible', True) %}
            <!-- Include header section HTML here -->
        {% elif section_type == 'notes' and section_visible.get('notes', {}).get('visible', True) %}
            <!-- Include notes section HTML here -->
        {% elif section_type == 'ai_assistant' ... %}
            <!-- Include AI assistant section HTML here -->
        {# ... etc for all sections ... #}
        {% endif %}
    {% endfor %}
</div>
```

## 🧪 Testing Plan

1. **Visual Test**: Open an entry page and verify sections appear in the order configured in layout builder
2. **Drag Test**: Change section order in layout builder → refresh entry page → verify new order
3. **Visibility Test**: Hide a section in layout builder → refresh entry page → verify section is hidden
4. **Width Test**: Change section width → refresh → verify responsive grid columns update
5. **Functionality Test**: Ensure all buttons, forms, and JavaScript still work

## 📊 Progress Summary

| Task | Status | File | Lines |
|------|--------|------|-------|
| Create macro system | ✅ Done | `macros/entry_sections.html` | 1-290 |
| Import macros | ✅ Done | `entry_detail.html` | ~2067 |
| Create header partial | ✅ Done | `partials/_entry_header_content.html` | 1-250 |
| Replace hardcoded sections | ⏳ Pending | `entry_detail.html` | ~2074-3002 |
| Test integration | ⏳ Pending | - | - |

## 📝 Recommended Next Action

**Use the Hybrid Approach** - it's the fastest and lowest risk:

1. Find line ~2072 in `entry_detail.html`
2. Wrap all existing section code in a `{% for section_type in section_order %}` loop
3. Add `{% if section_type == 'header' %}` before each section
4. Keep all existing HTML content as-is
5. Test that sections render in configured order

This gives you the layout order feature immediately without refactoring 10,000 lines of template code.

## 🎯 End Goal

When complete:
- Entry page respects layout configuration from builder
- Sections appear in `display_order` sequence
- Width, height, collapsible state all controlled by database
- Easy to add new sections (just add to macro file)
- Maintainable, clean separation of layout logic and content

## ⚠️ Important Notes

- Lint errors in Jinja2 templates are normal (CSS parser sees `{{ }}` syntax)
- The macro system uses `caller()` pattern for wrapper functionality
- section_order is a list like `['header', 'notes', 'sensors', ...]`
- section_config is a dict like `{'header': {'visible': True, 'width': 12, ...}}`
- All JavaScript IDs and functionality must stay the same for compatibility
