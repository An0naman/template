# Relationship Filter Scope Fix

## Issue
When implementing multiple relationship sections within an entry, the state/status filtering was not working correctly. Filters from one section were interfering with filters in other sections.

## Root Cause
The JavaScript event listeners and query selectors were using `document.querySelector()` and `document.querySelectorAll()` which select elements across the **entire page**, not just within the specific section instance.

When you have multiple relationship sections on the same entry (e.g., Section 1 showing "Team Members", Section 2 showing "Projects"), the following problems occurred:

1. **Multiple event listeners attached to same elements**: Each section's `attachEventListeners()` function would attach listeners to ALL `.relationship-state-filter` elements on the page
2. **Cross-section interference**: Filtering in one section could trigger `applyFilters()` from a different section's closure/scope
3. **Wrong elements selected**: Functions would select cards/filters from the wrong section instance

## Solution
Changed all DOM query operations to be **scoped to the specific section's container** by using:
```javascript
const container = document.getElementById('groupedViewContainer' + entryId);
container.querySelector(...)  // Instead of document.querySelector(...)
```

## Files Modified
- `app/templates/sections/_relationships_section_v2.html`

## Functions Fixed

### 1. `attachEventListeners()`
**Before:**
```javascript
function attachEventListeners() {
    document.querySelectorAll('.relationship-state-filter').forEach(filter => {
        // Attaches to ALL filters on the page
    });
}
```

**After:**
```javascript
function attachEventListeners() {
    const container = document.getElementById('groupedViewContainer' + entryId);
    if (!container) return;
    
    container.querySelectorAll('.relationship-state-filter').forEach(filter => {
        // Only attaches to filters in THIS section
    });
}
```

### 2. `applyFilters(definitionId)`
**Before:**
```javascript
function applyFilters(definitionId) {
    const card = document.querySelector(`.relationship-type-card[data-definition-id="${definitionId}"]`);
    // Could select card from wrong section
}
```

**After:**
```javascript
function applyFilters(definitionId) {
    const container = document.getElementById('groupedViewContainer' + entryId);
    if (!container) return;
    
    const card = container.querySelector(`.relationship-type-card[data-definition-id="${definitionId}"]`);
    // Only selects card from THIS section
}
```

### 3. `loadStatesForDefinition(definitionId)`
**Before:**
```javascript
async function loadStatesForDefinition(definitionId) {
    const card = document.querySelector(`.relationship-type-card[data-definition-id="${definitionId}"]`);
    // Could load states into filter dropdown from wrong section
}
```

**After:**
```javascript
async function loadStatesForDefinition(definitionId) {
    const container = document.getElementById('groupedViewContainer' + entryId);
    if (!container) return;
    
    const card = container.querySelector(`.relationship-type-card[data-definition-id="${definitionId}"]`);
    // Only loads states into filter dropdown in THIS section
}
```

### 4. `saveFilterPreference(definitionId)`
**Before:**
```javascript
async function saveFilterPreference(definitionId) {
    const card = document.querySelector(`.relationship-type-card[data-definition-id="${definitionId}"]`);
    // Could read filter values from wrong section
}
```

**After:**
```javascript
async function saveFilterPreference(definitionId) {
    const container = document.getElementById('groupedViewContainer' + entryId);
    if (!container) return;
    
    const card = container.querySelector(`.relationship-type-card[data-definition-id="${definitionId}"]`);
    // Only reads filter values from THIS section
}
```

### 5. `loadFilterPreferences()`
**Before:**
```javascript
async function loadFilterPreferences() {
    preferences.forEach(pref => {
        const card = document.querySelector(`.relationship-type-card[data-definition-id="${pref.relationship_definition_id}"]`);
        // Could apply preferences to card in wrong section
    });
}
```

**After:**
```javascript
async function loadFilterPreferences() {
    const container = document.getElementById('groupedViewContainer' + entryId);
    if (!container) return;
    
    preferences.forEach(pref => {
        const card = container.querySelector(`.relationship-type-card[data-definition-id="${pref.relationship_definition_id}"]`);
        // Only applies preferences to cards in THIS section
    });
}
```

## Key Concept
Each relationship section is wrapped in an **IIFE (Immediately Invoked Function Expression)** that creates a closure with its own `entryId` and `currentEntryTypeId`. However, the DOM query operations were "escaping" this closure by using global `document` queries. By scoping all queries to the section's container element, we ensure true isolation between multiple section instances.

## Testing
To verify the fix works:
1. Create an entry type with multiple relationship sections
2. Configure each section to show different relationship types
3. Add filters to relationships in each section
4. Verify that:
   - Filters in Section 1 only affect Section 1's relationships
   - Filters in Section 2 only affect Section 2's relationships
   - Filter preferences are saved/loaded correctly per section
   - No cross-section interference occurs

## Date
November 8, 2025

## Related Documentation
- [RELATIONSHIP_SECTION_CONFIGURATION.md](./RELATIONSHIP_SECTION_CONFIGURATION.md) - Section-level configuration
- [MULTIPLE_SECTIONS_SUPPORT.md](./MULTIPLE_SECTIONS_SUPPORT.md) - Multiple section instances
- [RELATIONSHIP_STATE_FILTER_V2_UPDATE.md](./RELATIONSHIP_STATE_FILTER_V2_UPDATE.md) - Filter implementation details
