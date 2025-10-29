# Entry Layout Implementation Plan

## Current Status

✅ **Backend Complete**: Layout configuration is loaded and passed to template
✅ **Layout Builder Complete**: Saves section order and configuration  
✅ **Partial Integration**: 5 sections have layout wrappers (header, ai_assistant, notes, label_printing, sensors)
❌ **Template Structure**: Sections are not rendered in configured order

## The Problem

Sections are currently hardcoded in the template like this:

```html
<div class="row g-4">
    <div class="col-lg-7">
        <!-- Sensors section -->
        <!-- Other sections -->
    </div>
    <div class="col-lg-5">
        <!-- AI Assistant -->
        <!-- Notes -->
    </div>
</div>
```

This ignores `section_order` entirely.

## The Solution - Two Approaches

### Approach 1: Full Refactor (Complex but Complete)
Restructure the entire template to:
1. Loop through `section_order`
2. Use `{% if section_type == 'notes' %}` blocks for each section
3. Render sections dynamically in configured order

**Pros**: Fully respects layout configuration  
**Cons**: Requires refactoring 10,000+ line template

### Approach 2: Hybrid (Simpler, Faster)
Keep existing structure but:
1. Add visibility checks using `section_config`
2. Accept that order might not match exactly
3. Focus on making width/collapsible/height work first

**Pros**: Minimal risk, faster implementation  
**Cons**: Order still somewhat fixed

## Recommendation: Approach 1 with Incremental Implementation

Create a new "dynamic section renderer" that:
1. Loops through `section_order`
2. Includes section partials based on type
3. Can be tested section-by-section

## Implementation Steps

### Step 1: Create Section Partials ✅
Extract each section into its own file:
- `sections/_header.html` (already exists)
- `sections/_notes.html`
- `sections/_sensors.html`
- `sections/_ai_assistant.html`
- etc.

### Step 2: Create Dynamic Renderer
```jinja2
{% for section_type in section_order %}
    {% set config = section_config.get(section_type, {}) %}
    {% if config.visible %}
        <div class="row mb-4">
            <div class="col-12 col-md-{{ config.width }}">
                {% if config.collapsible %}
                <div class="collapse {{ 'show' if not config.collapsed else '' }}" id="{{ section_type }}SectionContent">
                {% endif %}
                
                <div style="min-height: {{ config.height * 80 }}px;">
                    {% if section_type == 'header' %}
                        {% include 'sections/_header.html' %}
                    {% elif section_type == 'notes' %}
                        {% include 'sections/_notes.html' %}
                    {% elif section_type == 'sensors' %}
                        {% include 'sections/_sensors.html' %}
                    {# ... etc for all section types #}
                    {% endif %}
                </div>
                
                {% if config.collapsible %}
                </div>
                {% endif %}
            </div>
        </div>
    {% endif %}
{% endfor %}
```

### Step 3: Test Incrementally
1. Start with just header
2. Add notes
3. Add remaining sections one by one

## Quick Win Option

Since you have 5 sections already wrapped with layout config, I can:
1. Just fix the ordering for those 5 sections
2. Leave the rest as-is for now
3. You get immediate value with minimal risk

This would mean the entry page respects order for:
- header
- ai_assistant
- notes  
- label_printing
- sensors

And the remaining sections (relationships, reminders, etc.) stay in their current positions.

**Would you like me to implement the Quick Win option first?**
