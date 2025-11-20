# Relationships Section V2 - Import from Existing Feature

## 📋 Overview

Ported the **"Shared Relationships"** functionality from `entry_detail.html` (V1) to `_relationships_section_v2.html` (V2) with one key modification: **only shows when a relationship definition has no current related records**.

## 🎯 Feature Description

When adding relationships in V2, if:
1. The relationship definition has **zero** current relationships
2. There are **shared relationship opportunities** available (indirect connections via other entries)

Then the modal will display an **"Import from Existing"** section allowing bulk import of related entries.

## 🔄 What Was Changed

### Backend (No changes needed!)
- ✅ Uses existing V1 API: `/api/entries/<id>/shared_relationship_opportunities`
- ✅ Uses existing V1 API: `/api/entries/<id>/create_shared_relationships`
- ❌ Removed custom endpoint that was initially created

### Frontend (`app/templates/sections/_relationships_section_v2.html`)

#### Modified Function: `openAddRelationshipModal()`
**Key Logic:**
```javascript
// 1. Check if this definition has any current relationships
let hasCurrentRelationships = false;
const relationships = await fetch(`/api/entries/${entryId}/relationships`);
hasCurrentRelationships = relationships.some(rel => rel.definition_id == definitionId);

// 2. Only check for shared opportunities if NO current relationships
if (!hasCurrentRelationships) {
    const allOpportunities = await fetch(`/api/entries/${entryId}/shared_relationship_opportunities`);
    
    // 3. Filter to only show opportunities matching this specific definition
    const relevantOpportunities = allOpportunities.filter(opp => 
        opp.relationship_definition && opp.relationship_definition.id == definitionId
    );
}
```

**UI Elements Added:**
- Alert banner showing total available entries to import
- "Import from Existing" toggle button
- Collapsible import section with:
  - Grouped by source entry (intermediate connection)
  - Checkboxes for each available target entry
  - Shows quantity/unit from source relationships
  - "Select All" / "Deselect All" buttons per group
  - "Import Selected" button

#### Modified Function: `importMultipleEntries()`
**Changed from:** Individual POST requests per entry  
**Changed to:** Single batch POST to V1's `/create_shared_relationships` endpoint

**Payload Structure:**
```javascript
{
    "relationships": [
        {
            "definition_id": 1,
            "target_entry_id": 2,
            "quantity": 100,      // Optional, from source relationship
            "unit": "grams"       // Optional, from source relationship
        },
        // ... more relationships
    ]
}
```

## 🎨 UI/UX Flow

### User Experience:
1. User opens entry detail V2
2. Clicks "Add" button for a relationship type with 0 current relationships
3. Modal opens showing:
   - **If shared opportunities exist:** Blue info alert with "Import from Existing" button
   - Standard "Search Existing" and "Create New" options below
4. User clicks "Import from Existing"
5. Section expands showing:
   - Grouped entries by source (e.g., "From: Recipe ABC")
   - Checkboxes for each available entry (pre-selected)
   - Quantity/unit preserved from source relationships
6. User selects/deselects entries and clicks "Import Selected"
7. Relationships created in batch
8. Page refreshes showing new relationships

### Condition for Display:
```
SHOW import section IF:
  - Current definition has 0 relationships AND
  - Shared relationship opportunities exist for this definition AND
  - At least one opportunity matches this definition ID
```

## 📊 Example Scenario

**Scenario:** You have a "Sample" entry that needs "Ingredients"

**Current State:**
- Sample A is related to Recipe B (via "uses_recipe" relationship)
- Recipe B has relationships to Ingredient C, D, E (via "contains_ingredient" relationship)
- Sample A has 0 "contains_ingredient" relationships currently

**What Happens:**
1. User clicks "Add" for "Ingredients" relationship on Sample A
2. Modal detects: 0 current "contains_ingredient" relationships ✓
3. Modal calls shared opportunities API
4. API finds: Sample A → Recipe B → [Ingredients C, D, E]
5. Modal shows: "Quick Import Available: Found 3 ingredients from 1 related entry"
6. User clicks "Import from Existing"
7. Shows: "From: Recipe B" with checkboxes for C, D, E (all checked)
8. User clicks "Import Selected"
9. Creates 3 new relationships: Sample A → Ingredient C/D/E

## 🔍 Key Differences from V1

| Aspect | V1 (entry_detail.html) | V2 (this implementation) |
|--------|------------------------|---------------------------|
| **Display Location** | Separate section in page | Inside "Add Relationship" modal |
| **Trigger** | Auto-loaded on page load | On-demand when clicking "Add" |
| **Condition** | Always shown if opportunities exist | Only shown if definition has 0 relationships |
| **Scope** | All possible opportunities | Filtered to specific definition |
| **UI Style** | Standalone section | Embedded in modal with collapse |

## ✅ Testing Checklist

- [ ] Create entry with relationship to another entry
- [ ] Ensure other entry has relationships to multiple targets
- [ ] Open first entry in V2
- [ ] Click "Add" for relationship type with 0 current records
- [ ] Verify "Import from Existing" section appears
- [ ] Verify it does NOT appear if definition already has relationships
- [ ] Select some (not all) entries
- [ ] Click "Import Selected"
- [ ] Verify relationships created successfully
- [ ] Verify quantity/unit preserved from source
- [ ] Verify page refreshes and shows new relationships

## 📝 Files Modified

1. **`/app/templates/sections/_relationships_section_v2.html`**
   - Modified `openAddRelationshipModal()` function
   - Modified `importMultipleEntries()` function
   - Added dynamic group selection functions

## 🚀 API Endpoints Used

### GET `/api/entries/<id>/shared_relationship_opportunities`
**Returns:** Array of opportunity objects
```json
[
    {
        "intermediate_entry": {
            "id": 2,
            "title": "Recipe B",
            "entry_type_id": 1
        },
        "relationship_definition": {
            "id": 3,
            "name": "contains_ingredient",
            "label_from_side": "Contains",
            "allow_quantity_unit": true
        },
        "potential_targets": [
            {
                "target_entry": {
                    "id": 4,
                    "title": "Ingredient C",
                    "status": "Active"
                },
                "source_relationship": {
                    "quantity": 100,
                    "unit": "grams"
                }
            }
        ]
    }
]
```

### POST `/api/entries/<id>/create_shared_relationships`
**Payload:**
```json
{
    "relationships": [
        {
            "definition_id": 3,
            "target_entry_id": 4,
            "quantity": 100,
            "unit": "grams"
        }
    ]
}
```

**Response:**
```json
{
    "created": [...],
    "failed": [...],
    "summary": {
        "created_count": 3,
        "failed_count": 0,
        "total_requested": 3
    }
}
```

## 💡 Benefits

1. **Consistency:** Uses same proven API and logic as V1
2. **Efficiency:** Batch import instead of one-by-one creation
3. **Smart:** Only shows when relevant (0 current relationships)
4. **Contextual:** Appears right where user needs it (in Add modal)
5. **Preserves Data:** Quantity/unit copied from source relationships
6. **No Duplicates:** API handles checking for existing relationships

## 🔮 Future Enhancements (Optional)

- [ ] Add ability to edit quantity/unit before importing
- [ ] Show preview of relationships being created
- [ ] Add confirmation dialog for large imports (>10 relationships)
- [ ] Cache shared opportunities to avoid repeated API calls
- [ ] Add "Recently Used" quick-pick suggestions

---

**Implementation Date:** November 6, 2025  
**Status:** ✅ Complete  
**Compatibility:** Entry Detail V2 only
