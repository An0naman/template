# Hierarchical Relationship Filter Groups Implementation Plan

## Data Structure

```javascript
// Filter tree structure
relationshipFilterTree = [
  {
    type: 'filter',
    id: 1,
    relationship_def_id: 16,
    target_entry_id: 5,
    direction: 'to',
    operator: 'AND'  // operator BEFORE this filter
  },
  {
    type: 'group',
    id: 2,
    operator: 'AND',  // operator BEFORE this group
    filters: [
      {
        type: 'filter',
        id: 3,
        relationship_def_id: 13,
        target_entry_id: 23,
        direction: 'from',
        operator: null  // first item in group has no operator
      },
      {
        type: 'filter',
        id: 4,
        relationship_def_id: 13,
        target_entry_id: 24,
        direction: 'from',
        operator: 'OR'
      }
    ]
  }
]
```

This represents: `Filter1 AND (Filter3 OR Filter4)`

## UI Features

1. **Visual Grouping**: Groups shown with borders and indentation
2. **Operator Buttons**: AND/OR buttons between filters
3. **Drag and Drop**: Reorder filters (future enhancement)
4. **Group Actions**: Add filter to group, delete group, nest groups

## Backend Evaluation

The backend will recursively evaluate the filter tree:
- Process each item in order
- For filters: get matching entries
- For groups: recursively evaluate group, then combine with parent using operator
- Combine results using the operator (AND = intersection, OR = union)

## Example Queries

### Simple: "Chamber#1 OR Chamber#2"
```javascript
[
  { type: 'filter', ...chamber1, operator: null },
  { type: 'filter', ...chamber2, operator: 'OR' }
]
```

### Complex: "(Chamber#1 OR Chamber#2) AND Style=Wine"
```javascript
[
  { 
    type: 'group', 
    operator: null,
    filters: [
      { type: 'filter', ...chamber1, operator: null },
      { type: 'filter', ...chamber2, operator: 'OR' }
    ]
  },
  { type: 'filter', ...wine, operator: 'AND' }
]
```
