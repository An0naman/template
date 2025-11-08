# Multiple Relationship Sections - Unique ID Fix

## Issue
When implementing multiple relationship sections within the same entry (e.g., "Relationships" and "Relationships1"), the state/status filter dropdowns were not appearing in the second and subsequent sections.

## Root Cause
All HTML element IDs in the relationships section template were based solely on `{{ entry.id }}`. When multiple relationship sections existed on the same entry, they all generated **identical element IDs**, causing:

1. **ID conflicts**: Multiple elements with the same ID (invalid HTML)
2. **JavaScript targeting wrong sections**: `document.getElementById()` always returns the first matching ID
3. **Missing UI elements**: Filters and controls only worked in the first section instance

### Example Problem:
```html
<!-- Section 1 "Relationships" -->
<div id="groupedViewContainer69">...</div>

<!-- Section 2 "Relationships1" --> 
<div id="groupedViewContainer69">...</div>  <!-- DUPLICATE ID! -->
```

When JavaScript tried to find `getElementById('groupedViewContainer69')`, it would always find the first one, so the second section's JavaScript couldn't manipulate its own DOM elements.

## Solution
Modified the template to include **both** `entry.id` and `section.id` in all element IDs, creating a unique identifier for each section instance.

### Implementation:

**1. Created section-specific unique ID in Jinja2:**
```jinja2
{% set section_unique_id = entry.id ~ '_' ~ (section_id|default('default')) %}
```

**2. Passed section_id from parent template:**
```jinja2
{# In entry_detail_v2.html #}
{% elif section_type == 'relationships' %}
    {% with section_id=section.id %}{% include 'sections/_relationships_section_v2.html' %}{% endwith %}
```

**3. Updated all HTML element IDs:**
```html
<!-- Before -->
<div id="groupedViewContainer{{ entry.id }}">

<!-- After -->
<div id="groupedViewContainer{{ section_unique_id }}">
```

**4. Updated all JavaScript references:**
```javascript
// Before
const container = document.getElementById('groupedViewContainer' + entryId);

// After  
const sectionUniqueId = '{{ section_unique_id }}';
const container = document.getElementById('groupedViewContainer' + sectionUniqueId);
```

### Example Result:
```html
<!-- Section 1 "Relationships" (section_id = 45) -->
<div id="groupedViewContainer69_45">...</div>

<!-- Section 2 "Relationships1" (section_id = 52) -->
<div id="groupedViewContainer69_52">...</div>  <!-- UNIQUE! -->
```

## Files Modified

### 1. `app/templates/entry_detail_v2.html`
- Updated to pass `section_id` when including the relationships section template

### 2. `app/templates/sections/_relationships_section_v2.html`
- Added `section_unique_id` variable creation
- Updated ALL element IDs to use `section_unique_id` instead of just `entry.id`:
  - `relationshipsSection`
  - `toggleReorderMode`
  - `toggleEmptyRelationships`
  - `relationshipsLoading`
  - `relatedRecordsContainer`
  - `relationshipsTabs`
  - `groupedTab`
  - `hierarchyTab`
  - `groupedViewContainer` 
  - `hierarchyLoading`
  - `hierarchyContent`
  
- Updated JavaScript variables:
  - Added `sectionId` constant
  - Added `sectionUniqueId` constant
  - Updated all `getElementById()` calls to use `sectionUniqueId`
  - Updated all window function names to use `sectionUniqueId`

## Benefits

1. ✅ **Multiple sections work independently**: Each section has its own unique DOM elements
2. ✅ **Filters appear correctly**: State/status filters now render in all sections
3. ✅ **No JavaScript interference**: Each section's JavaScript operates on its own elements
4. ✅ **Valid HTML**: No duplicate IDs in the DOM
5. ✅ **Scalable**: Can add unlimited relationship sections to an entry type

## Testing

To verify the fix:
1. Create an entry type with multiple relationship sections
2. Configure each section with different relationship types
3. Open an entry of that type
4. Verify:
   - All sections load and display correctly
   - State/status filters appear in each section
   - Filters work independently in each section
   - Reorder buttons work independently
   - Add relationship buttons work in each section
   - No console errors about duplicate IDs

## Related Issues

This fix resolves two related problems:
1. **Missing filters**: Filters not appearing in additional relationship sections
2. **Filter scoping**: Filters from one section affecting another (fixed in RELATIONSHIP_FILTER_SCOPE_FIX.md)

Both issues stemmed from improper scoping/identification of DOM elements when multiple section instances exist.

## Date
November 8, 2025

## Version
Updated from Version 2025-11-02-20:20 to Version 2025-11-08 (Multi-Section Support)

## Related Documentation
- [RELATIONSHIP_FILTER_SCOPE_FIX.md](./RELATIONSHIP_FILTER_SCOPE_FIX.md) - Filter scoping for multiple sections
- [RELATIONSHIP_SECTION_CONFIGURATION.md](./RELATIONSHIP_SECTION_CONFIGURATION.md) - Section-level configuration
- [MULTIPLE_SECTIONS_SUPPORT.md](./MULTIPLE_SECTIONS_SUPPORT.md) - Multiple section instances feature
