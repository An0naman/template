# Hierarchy Configuration Guide

## Current Status
The serializer bug has been fixed - the API now returns `is_hierarchical` and `hierarchy_direction` fields.

## Relationships to Configure

### For Cherry Wine #1 Entry (Sample Bottle type):

#### Parents (appear above current entry in tree):

1. **Fermentation Chamber → Sample Bottle**
   - Relationship Name: `Fermentation Chamber_Sample Bottle_N:1`
   - ✓ Mark as Hierarchical
   - Direction: **From side is Parent → To side is Child**
   - This makes Chamber #1 a parent of Cherry Wine #1

2. **Recipe → Sample Bottle**
   - Relationship Name: `Recipe_Sample Bottle_N:N`
   - ✓ Mark as Hierarchical
   - Direction: **From side is Parent → To side is Child**
   - This makes Cherry Wine (recipe) a parent of Cherry Wine #1

3. **Style → Recipe** (for Recipe's parent)
   - Relationship Name: `Style_Recipe_N:1`
   - ✓ Mark as Hierarchical
   - Direction: **From side is Parent → To side is Child**
   - This makes Wine a parent of Cherry Wine (recipe)

#### Children (appear below current entry in tree):

4. **Sample Bottle → Fining Agent**
   - Relationship Name: `Sample Bottle_Fining Agent_1:N`
   - ✓ Mark as Hierarchical
   - Direction: **To side is Parent → From side is Child**
   - This makes Bentonite a child of Cherry Wine #1

5. **Sample Bottle → Ingredient**
   - Relationship Name: `Sample Bottle_Ingredient_N:N`
   - ✓ Mark as Hierarchical
   - Direction: **To side is Parent → From side is Child**
   - This makes Brown Sugar, Cherry Fruit Juice, etc. children of Cherry Wine #1

6. **Sample Bottle → Yeast**
   - Relationship Name: `Sample Bottle_Yeast_1:N`
   - ✓ Mark as Hierarchical
   - Direction: **To side is Parent → From side is Child**
   - This makes Wild Yeast a child of Cherry Wine #1

#### Do NOT make hierarchical:

7. **Comparison → Sample Bottle**
   - Relationship Name: `Comparison_Sample Bottle_N:N`
   - Either mark as inactive OR leave hierarchical unchecked
   - This relationship won't appear in hierarchy view

## Expected Hierarchy Tree Structure

After configuration, Cherry Wine #1 should show TWO separate trees:

### Tree 1 (via Chamber):
```
Chamber #1 (parent)
  └─ Cherry Wine #1 ★ (YOU ARE HERE)
      ├─ Bentonite (child - Fining Agent)
      ├─ Brown Sugar (child - Ingredient)
      ├─ Cherry Fruit Juice (Blackcurls) (child - Ingredient)
      ├─ Morello Cherries (child - Ingredient)
      └─ Wild Yeast (child - Yeast)
```

### Tree 2 (via Recipe):
```
Wine (grandparent - Style)
  └─ Cherry Wine (parent - Recipe)
      └─ Cherry Wine #1 ★ (YOU ARE HERE)
          ├─ Bentonite (child - Fining Agent)
          ├─ Brown Sugar (child - Ingredient)
          ├─ Cherry Fruit Juice (Blackcurls) (child - Ingredient)
          ├─ Morello Cherries (child - Ingredient)
          └─ Wild Yeast (child - Yeast)
```

## How to Configure

1. Navigate to: http://100.84.208.29:5001/manage_relationships
2. For each relationship listed above:
   - Click the Edit button (pencil icon)
   - Check "Hierarchical Relationship (Parent-Child)"
   - Select the correct "Hierarchy Direction" from dropdown
   - Click "Save Definition"
3. Return to Cherry Wine #1 entry page
4. Click the "Hierarchy View" tab in the Relationships section
5. Verify the trees appear correctly

## Troubleshooting

- If a relationship doesn't appear, check it's marked as both Active AND Hierarchical
- If parent/child is reversed, change the Hierarchy Direction setting
- If you see unwanted siblings, verify the relationship is configured with correct direction
- The hierarchy only shows direct lineage - no cousins or siblings from other branches
