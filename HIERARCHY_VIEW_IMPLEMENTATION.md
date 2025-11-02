# Hierarchy View Implementation - Siloed Parent/Child Relationships

## Overview

Implemented a hierarchical view for the relationships section in Entry Detail V2 that shows **only parent-child lineages** without siblings, nieces/nephews, or cousins. Each relationship type is displayed in a separate tree.

## Key Features

### ✅ 1. Relationship Type Grouping
- Each hierarchical relationship type gets its own separate tree
- Trees are clearly labeled with the relationship type name
- Multiple relationship types are separated with visual dividers

### ✅ 2. Pure Lineage Display (No Siblings)
The hierarchy shows:
- **Ancestors**: All parents up to the root (following only the path to current entry)
- **Current Entry**: Marked with a "Current" badge
- **Descendants**: ALL children, grandchildren, great-grandchildren, etc. (full recursive tree)

What's **excluded**:
- Siblings (other children of the same parent)
- Cousins (children of siblings)
- Nieces/Nephews (children of siblings)
- Any non-direct lineage relationships

### ✅ 3. Full Descendant Tree
- Shows complete recursive tree below the current entry
- Children of children are fully expanded
- All generations of descendants are visible

## Example Structure

```
└── Wine (Style - parent relationship type)
    └── Cherry Wine (Recipe - parent of current)
        └── Cherry Wine #1 ★ (Current Record)
            ├── Morello Cherries (child 1)
            ├── Brown Sugar (child 2)
            └── Cherry Fruit Juice (child 3)
                └── Blackcurrant Extract (grandchild)

────────────────────────────────────────────────

└── Chamber 1 (Fermentation - different relationship type)
    └── Cherry Wine #1 ★ (Current Record)
        ├── Temperature Log 1 (child 1)
        ├── Temperature Log 2 (child 2)
        │   └── Sensor Reading 1 (grandchild)
        └── Bentonite Addition (child 3)
```

## Technical Implementation

### Backend Changes (`app/api/relationships_api.py`)

#### New Functions

1. **`get_parents_by_relationship(child_id, relationship_type_id=None)`**
   - Gets all parents for an entry, optionally filtered by relationship type
   - Returns parent_id, relationship_type_id, relationship_type_name, and label

2. **`get_children_by_relationship(parent_id, relationship_type_id=None)`**
   - Gets all children for an entry, optionally filtered by relationship type
   - Returns child_id, relationship_type_id, and relationship_label

3. **`build_descendant_subtree(current_id, rel_type_id, depth, visited)`**
   - Builds complete recursive tree of ALL descendants
   - No target checking - just pure child → grandchild → great-grandchild recursion
   - Used for everything below the current entry

4. **`build_lineage_for_relationship_type(target_id, relationship_type_id, name)`**
   - Main tree builder for a single relationship type
   - Finds root ancestor for the relationship type
   - Builds tree showing: ancestors → target → all descendants
   - No siblings at any level

#### Main API Endpoint Changes

**`GET /api/entries/<id>/relationships/hierarchy`**

Changed from:
- Build one tree per parent lineage
- Show siblings when they exist

To:
- Build one tree per **relationship type**
- Group all hierarchical relationships by their relationship type
- Each tree shows pure lineage only (no siblings)

### Frontend Changes (`app/templates/sections/_relationships_section_v2.html`)

#### Updated `renderHierarchyTree()` Function

- Detects multiple relationship types
- Adds header with relationship type name for each tree
- Separates multiple trees with horizontal dividers
- Displays relationship type icon and name

```javascript
<h6 class="text-primary mb-0">
    <i class="fas fa-sitemap me-2"></i>Wine Style Hierarchy
</h6>
```

## Data Flow

```
1. User clicks "Hierarchy View" tab
   ↓
2. Frontend calls: GET /api/entries/123/relationships/hierarchy
   ↓
3. Backend finds all hierarchical relationship types for entry 123
   ↓
4. For each relationship type:
   a. Find root ancestor
   b. Build path: root → ... → current entry (no siblings)
   c. From current entry, build FULL descendant tree (all children recursively)
   ↓
5. Return array of trees (one per relationship type)
   ↓
6. Frontend renders each tree with relationship type header
```

## Configuration

### Marking Relationships as Hierarchical

1. Go to **Settings → Relationship Definitions**
2. Edit or create a relationship definition
3. Check **"Hierarchical Relationship (Parent-Child)"**
4. Select **Hierarchy Direction**:
   - "From side is Parent → To side is Child"
   - "To side is Parent → From side is Child"

### Example Relationship Definitions

**Wine Style Hierarchy:**
- Name: "Recipe is Style"
- From: Recipe, To: Style
- Hierarchical: Yes
- Direction: "To side is Parent → From side is Child"

**Batch Tracking:**
- Name: "Record is Batch"
- From: Record, To: Recipe
- Hierarchical: Yes
- Direction: "To side is Parent → From side is Child"

**Fermentation Chamber:**
- Name: "Sample in Chamber"
- From: Sample, To: Chamber
- Hierarchical: Yes
- Direction: "To side is Parent → From side is Child"

## Benefits

1. **Clear Lineage Visualization**: See direct ancestry without clutter
2. **Isolated Relationship Types**: Different relationship contexts are separated
3. **Full Descendant View**: See complete tree of everything below current entry
4. **No Confusion**: Siblings and cousins don't appear to clutter the view
5. **Multiple Parent Support**: If entry has multiple parents from different relationship types, each shows in its own tree

## Testing

Test scenarios:
- ✅ Entry with single parent → Shows root to current to all descendants
- ✅ Entry with multiple parents (different relationship types) → Shows separate trees
- ✅ Entry with siblings → Siblings are hidden, only direct lineage shown
- ✅ Entry with deep descendants (3+ levels) → All levels visible recursively
- ✅ Entry with multiple children → All children and their descendants shown
- ✅ Entry as root → Shows only descendants
- ✅ Entry as leaf → Shows only ancestors

## Notes

- Maximum depth is configurable (default: 10 levels)
- Circular relationships are prevented with visited tracking
- Each tree tracks visited nodes independently to handle complex graphs
- Relationship type metadata is stored at the tree root level
