# Entry Layout Quick Win - Implementation Guide

## What's Been Implemented ✅

### Backend (Complete)
1. ✅ Layout configuration passed to template via `section_config` and `section_order`
2. ✅ Helper macros added to template: `should_show_section()` and `get_section_title()`
3. ✅ Route modified to process layout into easy-to-use format

### Template Helpers Available
The entry_detail.html template now has these available:

**Variables:**
- `section_config` - Dictionary with visibility/order for each section type
- `section_order` - List of section types in display order

**Macros:**
- `should_show_section(section_type)` - Returns True/False if section should be visible
- `get_section_title(section_type, default)` - Returns configured title or default

## How to Apply Layouts (Manual Step Required)

The template is **9908 lines** and very complex. To apply your layouts, you need to wrap each major section with visibility checks.

### Section Type Mapping

Based on the 13 section types we defined, here's how they map to template content:

| Section Type | Template Location | What It Controls |
|---|---|---|
| `header` | Lines 2077-2200 | Entry title, dates, status badge, action buttons |
| `notes` | Lines ~2500-3500 | Notes list, add note form, note filters |
| `relationships` | Lines ~2500-2700 | Related entries, relationship management |
| `labels` | Lines ~2285-2400 | Label printing section |
| `sensors` | Lines ~4000-6000 | Sensor data charts and readings |
| `reminders` | Lines ~2740-2800 | Reminder management |
| `ai_assistant` | Lines ~2541-2600 | AI chat interface |
| `attachments` | Lines ~2763-2850 | File upload/download section |
| `form_fields` | Lines ~2200-2400 | Custom entry type form fields |
| `qr_code` | Embedded in header | QR code display |
| `label_printing` | Lines ~2285-2500 | Print label interface |
| `relationship_opportunities` | Not yet implemented | Suggested relationships |
| `timeline` | Not yet implemented | Activity history |

### Example: Making Notes Section Configurable

**Find the notes section** (around line 2500):
```html
<div class="content-section theme-section mb-4">
    <div class="section-header mb-3">
        <h3><i class="fas fa-sticky-note me-2"></i>Notes</h3>
        ...
    </div>
    ...
</div>
```

**Wrap it with visibility check:**
```jinja2
{% if should_show_section('notes') %}
<div class="content-section theme-section mb-4">
    <div class="section-header mb-3">
        <h3><i class="fas fa-sticky-note me-2"></i>{{ get_section_title('notes', 'Notes') }}</h3>
        ...
    </div>
    ...
</div>
{% endif %}
```

### Example: Making Header Section Configurable

**Find the header section** (line 2077):
```html
<div class="content-section theme-section mb-4">
    <div class="section-content">
        <div class="d-flex flex-column flex-md-row justify-content-between align-items-start align-items-md-center mb-3">
            <div class="flex-grow-1 me-md-3 mb-2 mb-md-0">
                <h1 class="h1 mb-0" id="entryTitleDisplay">{{ entry.title }}</h1>
                ...
```

**Wrap it:**
```jinja2
{% if should_show_section('header') %}
<div class="content-section theme-section mb-4">
    ...
</div>
{% endif %}
```

## Automated Script Approach

Since manual editing is tedious, I can create a Python script to automatically wrap sections. Here's what it would do:

1. **Read** entry_detail.html
2. **Find** each major section by searching for patterns
3. **Insert** `{% if should_show_section('...') %}` before each section
4. **Insert** `{% endif %}` after each section
5. **Replace** hardcoded titles with `{{ get_section_title(...) }}`
6. **Save** modified template

Would you like me to create this script?

## Quick Manual Test

To quickly test if the layout system is working:

1. **Wrap just the notes section** with visibility check
2. **Go to layout builder** and hide the notes section for a specific entry type
3. **View an entry** of that type
4. **Verify** notes section is hidden

This proves the concept works before doing all sections.

## Alternative: JavaScript-Based Hiding

If modifying the template is too risky, we could use JavaScript to hide/show sections based on layout config:

1. **Pass section_config to JavaScript**
2. **On page load, loop through section_config**
3. **Hide sections** where `visible: false`
4. **Reorder sections** based on display_order

This is **less elegant** but **safer** (no template changes).

### JavaScript Implementation:
```javascript
<script>
const sectionConfig = {{ section_config|tojson }};

// Hide sections based on layout
Object.entries(sectionConfig).forEach(([sectionType, config]) => {
    if (!config.visible) {
        // Find and hide the section (would need to add data-section-type attributes)
        document.querySelectorAll(`[data-section-type="${sectionType}"]`).forEach(el => {
            el.style.display = 'none';
        });
    }
});
</script>
```

## What Do You Want to Do?

**Option A:** I create an automated Python script to wrap all sections (30 min work)
**Option B:** I implement JavaScript-based hiding (15 min work, less invasive)
**Option C:** You manually wrap a few key sections to test (I'll guide you)
**Option D:** We create separate modular templates (full implementation, 10-14 hours)

Which approach would you prefer?

