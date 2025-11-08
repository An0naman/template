# Show/Hide Functionality Fix - November 8, 2025

## Overview
Fixed the show/hide toggle functionality to work correctly with multiple section instances. Previously, the toggle buttons used the old section ID format and only worked with a single instance of each section type.

## Problem
1. **Old ID format**: Toggle buttons looked for `sectionType + 'SectionWrapper'` (e.g., `relationshipsSectionWrapper`)
2. **New ID format**: Sections now use `section-{id}-{tab_id}` (e.g., `section-42-main`)
3. **Shared config iteration**: Toggle buttons were created by iterating over `section_config` which didn't support multiple instances
4. **Missing instance information**: Each section instance needs its own toggle button

## Solution

### 1. Collect All Collapsible Sections (`entry_detail_v2.html`)

Added logic before rendering tabs to collect all visible, collapsible sections:

```jinja2
{# Collect all collapsible sections for toggle buttons #}
{% set all_collapsible_sections = [] %}
{% if tabs and tabs|length > 0 %}
    {% for tab in tabs %}
        {% if tab.is_visible %}
            {% set tab_sections = sections_by_tab.get(tab.tab_id, []) %}
            {% for section in tab_sections %}
                {% if section.is_visible and section.is_collapsible and section.section_type != 'header' %}
                    {% set _ = all_collapsible_sections.append({
                        'id': section.id,
                        'type': section.section_type,
                        'title': section.title,
                        'tab_id': tab.tab_id
                    }) %}
                {% endif %}
            {% endfor %}
        {% endif %}
    {% endfor %}
{% endif %}
```

This creates a list of all collapsible sections with their IDs, types, titles, and tab IDs.

### 2. Pass Collapsible Sections to Header

Updated the header include to pass the collected sections:

```jinja2
{% with section_id=section.id, collapsible_sections=all_collapsible_sections %}
    {% include 'sections/_header_section.html' %}
{% endwith %}
```

### 3. Update Toggle Buttons (`_header_section.html`)

**Before:**
```html
{% for section_type, config in section_config.items() %}
    {% if config.get('visible') and config.get('collapsible') and section_type != 'header' %}
        <button onclick="toggleSection('{{ section_type }}')"
                data-section="{{ section_type }}">
            {{ config.get('title', section_type.replace('_', ' ').title()) }}
        </button>
    {% endif %}
{% endfor %}
```

**After:**
```html
{% if collapsible_sections is defined %}
    {% for sect in collapsible_sections %}
        <button onclick="toggleSection({{ sect.id }}, '{{ sect.tab_id }}')"
                data-section-id="{{ sect.id }}"
                data-section-type="{{ sect.type }}"
                data-tab-id="{{ sect.tab_id }}">
            <i class="fas fa-eye me-1"></i>
            {{ sect.title or sect.type.replace('_', ' ').title() }}
        </button>
    {% endfor %}
{% endif %}
```

### 4. Update JavaScript Function

**Before:**
```javascript
function toggleSection(sectionType) {
    const sectionElement = document.getElementById(sectionType + 'SectionWrapper');
    const button = document.querySelector(`[data-section="${sectionType}"]`);
    // ...
}
```

**After:**
```javascript
function toggleSection(sectionId, tabId) {
    const sectionElement = document.getElementById(`section-${sectionId}-${tabId}`);
    const button = document.querySelector(`[data-section-id="${sectionId}"]`);
    // ...
}
```

## Benefits

### ✅ Now Working:
1. **Multiple toggle buttons** - One button per section instance (e.g., "Relationships #1", "Relationships #2")
2. **Unique targeting** - Each button targets its specific section instance
3. **Independent control** - Show/hide one instance without affecting others
4. **Custom titles** - Each button shows the section's custom title
5. **Tab-aware** - Correctly targets sections in their assigned tabs

### Example Usage:

If you have:
- 2 Relationship sections (one titled "Parents", one titled "Children")
- 2 Notes sections (one titled "Meeting Notes", one titled "Technical Details")

You'll now see 4 toggle buttons in the header:
- 👁️ Parents
- 👁️ Children
- 👁️ Meeting Notes
- 👁️ Technical Details

Each button independently shows/hides only its corresponding section.

## How It Works

1. **On Page Load:**
   - Template collects all visible, collapsible sections across all tabs
   - Stores their ID, type, title, and tab_id
   - Passes this list to the header section

2. **Button Rendering:**
   - Header creates one button per section instance
   - Each button gets unique data attributes
   - onclick calls `toggleSection(id, tab_id)`

3. **On Button Click:**
   - JavaScript receives section ID and tab ID
   - Constructs the correct selector: `section-{id}-{tab_id}`
   - Toggles visibility with animation
   - Updates button icon (eye/eye-slash)

## Files Modified

1. `app/templates/entry_detail_v2.html`
   - Added `all_collapsible_sections` collection logic
   - Updated header include to pass collapsible sections

2. `app/templates/sections/_header_section.html`
   - Changed toggle button loop from `section_config` to `collapsible_sections`
   - Updated button attributes to use section IDs
   - Modified `toggleSection()` function signature and implementation

## Testing

### Test Cases:

1. **Single Section Instances:**
   - ✅ Toggle button appears for collapsible sections
   - ✅ Click hides section with animation
   - ✅ Click again shows section
   - ✅ Button icon changes (eye/eye-slash)

2. **Multiple Section Instances:**
   - ✅ One button appears per instance
   - ✅ Each button shows correct title
   - ✅ Toggling one doesn't affect others
   - ✅ Works across different tabs

3. **Edge Cases:**
   - ✅ Sections marked non-collapsible don't get buttons
   - ✅ Hidden sections don't get buttons
   - ✅ Header section doesn't get a button
   - ✅ Works with single-tab layouts
   - ✅ Works with multi-tab layouts

## Known Limitations

1. **Button Order:** Buttons appear in the order sections are defined in tabs (might not match visual order)
2. **Button Group Size:** Many sections could make the button group very wide
3. **Mobile View:** Many toggle buttons might overflow on small screens

## Future Enhancements

1. **Dropdown Menu:** For >5 toggle buttons, use a dropdown instead of button group
2. **Keyboard Shortcuts:** Add hotkeys for common section toggles
3. **Remember State:** Store show/hide preferences in localStorage
4. **Collapsible Button Group:** Make the toggle buttons themselves collapsible on mobile

## Migration Notes

**No database changes required!** This is purely a frontend fix.

Existing users will immediately see:
- Toggle buttons for all collapsible section instances
- Each instance can be independently shown/hidden
- Smooth animations when toggling visibility

## Deployment

Container rebuilt and deployed. Changes are live.

To manually deploy:
```bash
docker compose down
docker compose up --build -d
```

---

## Example Scenarios

### Scenario 1: Project Management Entry
**Sections:**
- Header
- Relationships (title: "Stakeholders") - collapsible
- Relationships (title: "Dependencies") - collapsible  
- Notes (title: "Meeting Notes") - collapsible
- Sensors - not collapsible

**Toggle Buttons Shown:**
- 👁️ Stakeholders
- 👁️ Dependencies
- 👁️ Meeting Notes

### Scenario 2: Manufacturing Part Entry
**Sections:**
- Header
- Sensors (title: "Temperature Monitoring") - collapsible
- Sensors (title: "Pressure Monitoring") - collapsible
- Relationships (title: "Assembly Components") - collapsible
- Label Printing - collapsible

**Toggle Buttons Shown:**
- 👁️ Temperature Monitoring
- 👁️ Pressure Monitoring
- 👁️ Assembly Components
- 👁️ Label Printing

---

## Summary

The show/hide functionality now correctly:
✅ Creates individual toggle buttons for each section instance
✅ Uses the new `section-{id}-{tab_id}` ID format
✅ Targets specific section instances
✅ Shows custom section titles
✅ Works independently per instance
✅ Maintains smooth animations
✅ Updates button icons appropriately

Users can now effectively manage visibility of multiple section instances!
