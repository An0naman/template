# 🏗️ Hierarchical Relationship Field Enhancement

## Overview

Added an `is_hierarchical` field to the RelationshipDefinition model that explicitly marks parent-child relationships for display in the hierarchy tree view. This replaces the previous keyword-based detection method with a more flexible and explicit flag.

## What Changed

### Database Schema

#### RelationshipDefinition Table
Added new column:
- `is_hierarchical` (INTEGER DEFAULT 0) - Set to 1 for parent-child relationships, 0 for regular relationships

### Migration
The database migration automatically adds the `is_hierarchical` column to existing installations.

## Files Modified

### 1. Database Schema (`app/db.py`)
- **Added**: `is_hierarchical` column to RelationshipDefinition table creation
- **Added**: Migration code to add the column to existing databases

### 2. API Endpoints (`app/api/relationships_api.py`)

#### Updated Endpoints:
- **POST /api/relationship_definitions** - Now accepts `is_hierarchical` field
- **PATCH /api/relationship_definitions/<id>** - Now updates `is_hierarchical` field
- **GET /api/entries/<id>/relationships/hierarchy** - Now uses `is_hierarchical` instead of label keywords

#### Query Changes:
**Before:**
```sql
WHERE ... AND (
    rd.label_from_side LIKE '%Parent%' OR 
    rd.label_from_side LIKE '%parent%' OR
    rd.label_from_side LIKE '%Contains%' OR
    rd.label_from_side LIKE '%Has%'
)
```

**After:**
```sql
WHERE ... AND rd.is_hierarchical = 1
```

### 3. UI Template (`app/templates/relationship_definitions.html`)

#### Added UI Elements:
1. **Checkbox in Form**:
   ```html
   <div class="form-check mb-3">
       <input class="form-check-input" type="checkbox" id="isHierarchical">
       <label class="form-check-label" for="isHierarchical">
           Hierarchical Relationship (Parent-Child)
       </label>
       <div class="form-text">
           Enable this to show this relationship in the hierarchy tree view.
           Use for parent-child, contains, or has-part relationships.
       </div>
   </div>
   ```

2. **Column in Table**:
   - Header: "Hierarchical"
   - Shows tree icon (fa-sitemap) if hierarchical
   - Shows X icon (fa-times-circle) if not

3. **JavaScript Updates**:
   - Added `isHierarchical` to form elements
   - Included in form submission data
   - Added to edit button data attributes
   - Populated when editing existing definition

## Benefits

### 1. **Explicit Control**
- Users can explicitly mark which relationships should appear in hierarchy
- No guessing based on label naming conventions
- More flexibility in naming relationships

### 2. **Clearer Intent**
- The checkbox label clearly explains what it does
- Help text guides users on when to use it
- Visual indicator (tree icon) in the table

### 3. **Better Performance**
- Direct column check vs. multiple LIKE queries
- Indexed column for faster filtering
- No string pattern matching overhead

### 4. **More Flexible**
- Can have parent-child relationships with any label
- Don't need specific keywords in labels
- Support for internationalization/custom terminology

## Usage Guide

### For Users

#### Creating a Hierarchical Relationship

1. Navigate to **Relationship Definitions** page
2. Click **"Add New Definition"**
3. Fill in the relationship details:
   - From Type: Parent entry type (e.g., "Project")
   - To Type: Child entry type (e.g., "Task")
   - Labels: Describe the relationship from both sides
4. **Check the "Hierarchical Relationship" checkbox**
5. Save the definition

#### When to Use Hierarchical Flag

✅ **Use hierarchical for:**
- Parent → Child relationships
- Container → Contained relationships
- Whole → Part relationships
- Organization → Member relationships
- Category → Item relationships

❌ **Don't use hierarchical for:**
- Peer relationships (related to, associated with)
- Dependency relationships (depends on, requires)
- Reference relationships (references, mentioned in)
- Temporal relationships (follows, precedes)

#### Viewing Hierarchy

Once relationships are marked as hierarchical:
1. Go to any entry detail page (v2)
2. Scroll to "Related Records" section
3. Click the **"Hierarchy View"** tab
4. See the tree structure of parent-child relationships

### For Developers

#### API Request Format

**Creating with hierarchical flag:**
```json
POST /api/relationship_definitions
{
    "name": "Project-Task",
    "entry_type_id_from": 1,
    "entry_type_id_to": 2,
    "label_from_side": "Tasks",
    "label_to_side": "Parent Project",
    "is_hierarchical": 1,  // ← New field
    ...
}
```

**Updating hierarchical flag:**
```json
PATCH /api/relationship_definitions/123
{
    "is_hierarchical": 1
}
```

#### Database Query

**Check if relationship is hierarchical:**
```sql
SELECT * FROM RelationshipDefinition 
WHERE is_hierarchical = 1 AND is_active = 1;
```

**Get hierarchy for entry:**
```sql
SELECT er.* 
FROM EntryRelationship er
JOIN RelationshipDefinition rd ON er.relationship_type = rd.id
WHERE er.source_entry_id = ? AND rd.is_hierarchical = 1;
```

## Migration Guide

### Updating Existing Relationships

If you have existing parent-child relationships that were detected by label keywords, you should:

1. **Navigate to Relationship Definitions** page
2. **For each parent-child relationship**:
   - Click the Edit button
   - Check the "Hierarchical Relationship" checkbox
   - Save the changes

Common relationship types to update:
- "Parent of" / "Child of"
- "Contains" / "Part of"
- "Has" / "Belongs to"
- "Owns" / "Owned by"

### SQL Script (Optional)

If you want to bulk-update existing relationships:

```sql
-- Update relationships with "parent" in the label
UPDATE RelationshipDefinition
SET is_hierarchical = 1
WHERE lower(label_from_side) LIKE '%parent%'
   OR lower(label_from_side) LIKE '%child%'
   OR lower(label_from_side) LIKE '%contains%'
   OR lower(label_from_side) LIKE '%has%';
```

**Note:** Review the results and manually adjust any false positives.

## Examples

### Example 1: Project Management Hierarchy

```
Definition:
- Name: "Project-Task"
- From: Project → To: Task
- Label From: "Tasks"
- Label To: "Parent Project"
- Is Hierarchical: ✓ (checked)
```

Result in Hierarchy View:
```
▼ My Website Redesign [Project]
  ├─ Design Phase [Task]
  ├─ Development Phase [Task]
  └─ Testing Phase [Task]
```

### Example 2: Organization Structure

```
Definition:
- Name: "Department-Employee"
- From: Department → To: Employee
- Label From: "Team Members"
- Label To: "Department"
- Is Hierarchical: ✓ (checked)
```

Result in Hierarchy View:
```
▼ Engineering Department [Department]
  ├─ John Doe [Employee]
  ├─ Jane Smith [Employee]
  └─ Bob Johnson [Employee]
```

### Example 3: Category-Item (Non-Hierarchical)

```
Definition:
- Name: "Recipe-Ingredient"
- From: Recipe → To: Ingredient
- Label From: "Ingredients"
- Label To: "Used In"
- Is Hierarchical: ✗ (unchecked)
```

This won't appear in Hierarchy View, only in Grouped View.

## UI Reference

### Form Checkbox
<img src="form-checkbox-hierarchical.png" alt="Hierarchical checkbox in form">

**Location**: Relationship Definition Form  
**Position**: Between "Allow Quantity/Unit" and "Is Active" checkboxes

### Table Column
<img src="table-column-hierarchical.png" alt="Hierarchical column in table">

**Icons**:
- ✓ Hierarchical: 🌲 (tree icon, blue/primary color)
- ✗ Not Hierarchical: ✕ (X icon, muted gray)

### Hierarchy Tab
The hierarchy tab only shows relationships where `is_hierarchical = 1`.

## Technical Details

### Database Migration Code

```python
# Migration: Add is_hierarchical column to RelationshipDefinition
try:
    cursor.execute("PRAGMA table_info(RelationshipDefinition)")
    rd_columns = [col[1] for col in cursor.fetchall()]
    
    if 'is_hierarchical' not in rd_columns:
        cursor.execute('''
            ALTER TABLE RelationshipDefinition
            ADD COLUMN is_hierarchical INTEGER DEFAULT 0
        ''')
        logger.info("Added is_hierarchical column to RelationshipDefinition table")
except Exception as e:
    logger.error(f"Error adding is_hierarchical column: {e}")
```

### API Validation

The field is optional and defaults to 0 (false) if not provided:
```python
is_hierarchical = data.get('is_hierarchical', False)
```

Stored as integer (0 or 1) in the database:
```python
int(is_hierarchical)  # Converts boolean/int to 0 or 1
```

## Testing Checklist

### Database
- [ ] New installations have `is_hierarchical` column
- [ ] Existing databases get column via migration
- [ ] Column defaults to 0
- [ ] Column accepts 0 and 1 values

### API
- [ ] POST creates relationship with `is_hierarchical` field
- [ ] PATCH updates `is_hierarchical` field
- [ ] GET returns `is_hierarchical` in response
- [ ] Hierarchy endpoint uses `is_hierarchical` flag

### UI
- [ ] Checkbox appears in create/edit form
- [ ] Checkbox state saves correctly
- [ ] Checkbox state loads when editing
- [ ] Column shows correct icon in table
- [ ] Hierarchy tab only shows hierarchical relationships

### Functionality
- [ ] Hierarchical relationships appear in tree
- [ ] Non-hierarchical relationships don't appear in tree
- [ ] Can toggle hierarchical flag on existing relationships
- [ ] Tree updates after changing hierarchical flag

## Troubleshooting

### Issue: Relationships not showing in hierarchy

**Check:**
1. Is `is_hierarchical` set to 1?
   ```sql
   SELECT * FROM RelationshipDefinition WHERE id = <relationship_id>;
   ```
2. Are there actual relationships using this definition?
   ```sql
   SELECT * FROM EntryRelationship WHERE relationship_type = <definition_id>;
   ```

**Solution:**
Edit the relationship definition and check the "Hierarchical" checkbox.

### Issue: Wrong relationships showing in hierarchy

**Check:**
Which relationships have `is_hierarchical = 1`:
```sql
SELECT * FROM RelationshipDefinition WHERE is_hierarchical = 1;
```

**Solution:**
Uncheck "Hierarchical" for relationships that shouldn't be in the tree.

### Issue: Column not appearing after upgrade

**Check:**
```sql
PRAGMA table_info(RelationshipDefinition);
```

**Solution:**
Restart the application to trigger migrations, or run:
```sql
ALTER TABLE RelationshipDefinition ADD COLUMN is_hierarchical INTEGER DEFAULT 0;
```

## Future Enhancements

Potential improvements:
1. **Hierarchy Direction**: Add field to specify if relationship goes up or down the tree
2. **Multiple Hierarchies**: Allow entries to participate in multiple hierarchy types
3. **Hierarchy Depth Limit**: Per-definition max depth settings
4. **Validation**: Prevent circular hierarchies
5. **Bulk Operations**: Bulk mark/unmark relationships as hierarchical
6. **Import/Export**: Include hierarchical flag in definition import/export

---

**Implementation Date**: 2025-11-02  
**Status**: ✅ Complete  
**Version**: 1.0  
**Breaking Changes**: None (backward compatible)
