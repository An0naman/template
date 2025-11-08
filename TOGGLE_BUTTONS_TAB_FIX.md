# Toggle Buttons Tab-Aware Fix - November 8, 2025

## Problem Identified

The show/hide toggle buttons were completely unresponsive because:

1. **Wrong scope**: Toggle buttons in each tab were receiving ALL collapsible sections from ALL tabs
2. **Header duplication**: The header section appears in each tab, so multiple headers were created
3. **Global collection**: `all_collapsible_sections` collected sections from all tabs globally
4. **Mismatch**: Buttons in Tab A tried to toggle sections in Tab B (wrong tab_id in the element ID)

### Example of the Issue:
- **Tab A (Overview)**: Header with buttons for sections from Tab B
- **Tab B (Details)**: Header with buttons for sections from Tab A
- **Result**: Clicking buttons did nothing because `section-{id}-{wrong_tab_id}` didn't exist

## Solution

Changed from **global collection** to **per-tab collection** of collapsible sections.

### Key Changes:

**Before (Broken):**
```jinja2
{# Collected once, globally, before tabs #}
{% set all_collapsible_sections = [] %}
{% for tab in tabs %}
    {% for section in sections_by_tab.get(tab.tab_id, []) %}
        {# All sections from all tabs added to one list #}
    {% endfor %}
{% endfor %}

{# Each header in each tab got the same global list #}
{% with collapsible_sections=all_collapsible_sections %}
    {% include 'sections/_header_section.html' %}
{% endwith %}
```

**After (Fixed):**
```jinja2
{% for tab in tabs %}
    <div class="tab-pane" id="tab-{{ tab.tab_id }}">
        
        {# Collect collapsible sections for THIS tab only #}
        {% set tab_collapsible_sections = [] %}
        {% for sect in tab_sections %}
            {% if sect.is_visible and sect.is_collapsible and sect.section_type != 'header' %}
                {% set _ = tab_collapsible_sections.append({
                    'id': sect.id,
                    'type': sect.section_type,
                    'title': sect.title,
                    'tab_id': tab.tab_id  {# Correct tab_id! #}
                }) %}
            {% endif %}
        {% endfor %}
        
        {# Header gets only sections from current tab #}
        {% with collapsible_sections=tab_collapsible_sections %}
            {% include 'sections/_header_section.html' %}
        {% endwith %}
    </div>
{% endfor %}
```

## How It Works Now

### 1. **Tab-Specific Collection**
Each tab collects its own collapsible sections:
- Tab A header sees only Tab A sections
- Tab B header sees only Tab B sections

### 2. **Correct Element Targeting**
Toggle buttons now correctly target:
- `section-{id}-{current_tab_id}` ✅
- Not `section-{id}-{wrong_tab_id}` ❌

### 3. **Independent Operation**
Each tab's header operates independently:
- Buttons in Tab A toggle Tab A sections only
- Buttons in Tab B toggle Tab B sections only

### 4. **Fallback Still Works**
Single-tab layouts still collect their sections correctly using the fallback logic.

## Files Modified

1. **`app/templates/entry_detail_v2.html`**
   - Moved collapsible section collection inside tab loop
   - Created `tab_collapsible_sections` per tab
   - Updated header include to use `tab_collapsible_sections`
   - Maintained fallback for single-tab layouts

## Testing Checklist

### Multi-Tab Layouts:
- [x] Toggle buttons appear in each tab's header
- [x] Buttons only show sections from the current tab
- [x] Clicking button hides/shows correct section
- [x] Button icon changes (eye/eye-slash)
- [x] No cross-tab interference
- [x] Each tab operates independently

### Single-Tab Layouts:
- [x] Toggle buttons appear in header
- [x] Buttons show all collapsible sections
- [x] Clicking works correctly
- [x] Fallback logic still functional

### Multiple Section Instances:
- [x] Each instance gets its own button
- [x] Buttons show custom titles
- [x] Independent toggle per instance
- [x] Works across different tabs

## Example Scenario

### Setup:
**Tab A - "Overview":**
- Header section
- Relationships (title: "Parents") - collapsible
- Notes (title: "Summary") - collapsible

**Tab B - "Details":**
- Header section
- Relationships (title: "Children") - collapsible
- Sensors (title: "Temperature") - collapsible

### Result:

**In Tab A, header shows buttons:**
- 👁️ Parents (toggles relationships in Tab A)
- 👁️ Summary (toggles notes in Tab A)

**In Tab B, header shows buttons:**
- 👁️ Children (toggles relationships in Tab B)
- 👁️ Temperature (toggles sensors in Tab B)

**Key Point:** Tab A buttons don't try to toggle Tab B sections!

## Why This Fix Was Necessary

### Element ID Structure:
Sections in tabs have IDs like: `section-{section_id}-{tab_id}`

Example:
- `section-42-overview` (section 42 in overview tab)
- `section-43-details` (section 43 in details tab)

### The Problem:
If header in "overview" tab had buttons for "details" tab sections:
```javascript
toggleSection(43, 'details')  // Tries to find section-43-details
// But we're in overview tab!
// section-43-details doesn't exist in this tab's DOM
// Button does nothing ❌
```

### The Solution:
Header in "overview" tab only has buttons for "overview" sections:
```javascript
toggleSection(42, 'overview')  // Finds section-42-overview
// We're in overview tab
// section-42-overview exists!
// Button works! ✅
```

## Performance Impact

**Before:** 
- Collected all sections once
- Each header rendered unnecessary buttons

**After:**
- Collects sections per tab (slightly more work)
- Each header renders only relevant buttons
- Net result: Better UX, minimal performance difference

## Edge Cases Handled

1. **Empty Tabs:** Tabs with no collapsible sections show no toggle buttons
2. **Header-Only Tabs:** Header section doesn't get a toggle button for itself
3. **Hidden Sections:** Hidden sections don't get toggle buttons
4. **Non-Collapsible Sections:** Non-collapsible sections don't get buttons
5. **Fallback Mode:** Single-tab layouts still work correctly

## Deployment

Docker container rebuilt and deployed with fix.

To manually deploy:
```bash
docker compose up --build -d
```

## Verification Steps

1. Open an entry with multiple tabs
2. Check header in first tab - should only show buttons for sections in that tab
3. Click a toggle button - corresponding section should hide/show
4. Switch to second tab
5. Check header - should show different buttons for sections in that tab
6. Verify buttons work independently in each tab

## Summary

✅ **Fixed**: Toggle buttons now tab-aware
✅ **Fixed**: Buttons only target sections in current tab
✅ **Fixed**: Each tab operates independently
✅ **Fixed**: Correct element IDs are targeted
✅ **Maintained**: Fallback for single-tab layouts
✅ **Maintained**: Multiple section instance support

The show/hide toggle functionality now works correctly with the tab system!
