# Hierarchy View Logic Fix

## Date: November 3, 2025

## Issue
The hierarchy view in the relationships section for entry v2 was loading records incorrectly. The logic for determining parent-child relationships and building the hierarchy tree was overly complex and contained bugs.

## Root Cause
The original implementation had several issues:

1. **Complex parent detection logic**: The `get_direct_parents()` function tried to infer if an entry was a child by examining entry types and relationship definitions, leading to confusing logic that didn't correctly identify all parent relationships.

2. **Incorrect use of hierarchy_direction**: The code wasn't properly using the `hierarchy_direction` field from `RelationshipDefinition` to determine parent-child relationships.

3. **Unused/duplicate code**: Multiple unused functions (`build_lineage_for_relationship_type`, `build_descendants_recursive`, `build_node_recursive`) existed alongside the actual implementation, causing confusion.

## Solution

### Simplified `get_direct_parents()` Function
The function now uses a single SQL query that correctly interprets `hierarchy_direction`:

- `'from_to_child'`: source_entry_id is parent, target_entry_id is child
- `'to_from_child'`: target_entry_id is parent, source_entry_id is child

```sql
SELECT DISTINCT 
    CASE 
        WHEN rd.hierarchy_direction = 'from_to_child' THEN er.source_entry_id
        WHEN rd.hierarchy_direction = 'to_from_child' THEN er.target_entry_id
    END as parent_id,
    ...
FROM EntryRelationship er
JOIN RelationshipDefinition rd ON er.relationship_type = rd.id
WHERE rd.is_hierarchical = 1
AND (
    (rd.hierarchy_direction = 'from_to_child' AND er.target_entry_id = ?)
    OR (rd.hierarchy_direction = 'to_from_child' AND er.source_entry_id = ?)
)
```

### Improved `build_complete_descendant_tree()` Function
Simplified to follow the correct 3-step logic:
- **Step 2**: Get all direct children of the current entry
- **Step 3**: Recursively get descendants for each child

### Rewritten `build_hierarchy_tree()` Function
Now properly implements the required 3-step logic:

#### STEP 1: Upwards
- Look at relationship definitions where the current record is a child
- If parents exist, create a structure for each parent lineage
- If no parents exist, start a structure with the current entry as root

#### STEP 2: Downwards  
- Look at relationship definitions where the current record is a parent
- Add all children records to the current structure

#### STEP 3: Recursive
- Undertake step 2 recursively for each child to build the complete descendant tree

### Key Functions

#### `build_upward_to_root(current_id, target_id, visited, depth)`
- Builds the path from root ancestor down to the target entry
- Only shows one path (no siblings above the target)
- Once it reaches the target, calls `build_complete_descendant_tree()`

#### `is_ancestor_of_target(current_id, target_id, checked)`
- Helper function to determine if a node is on the path to the target
- Used when building upward to avoid following wrong branches

#### `find_root_ancestor(start_id, visited)`
- Recursively finds the topmost ancestor for a given entry
- Follows parent relationships until no more parents exist

## Code Removed
- `build_lineage_for_relationship_type()` - Unused complex function
- `build_descendants_recursive()` - Duplicate of `build_complete_descendant_tree()`
- `build_node_recursive()` - Duplicate/orphaned code
- `is_ancestor_of()` - Orphaned code fragment

## Testing Recommendations

1. **Test with no parents**: Entry should appear as root with its descendants
2. **Test with single parent**: Should show root → ... → parent → target → descendants
3. **Test with multiple parents**: Should create separate trees for each parent lineage
4. **Test deep hierarchies**: Ensure recursion works correctly for multiple levels
5. **Test circular references**: Verify `visited` set prevents infinite loops

## Files Modified
- `/app/api/relationships_api.py` - Main hierarchy logic

## Related Documentation
- `HIERARCHY_TAB_FEATURE.md`
- `HIERARCHICAL_FIELD_ENHANCEMENT.md`
- `HIERARCHY_VIEW_IMPLEMENTATION.md`
