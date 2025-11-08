# Quick Start: Relationship Section Configuration

## Overview

Your relationship sections can now filter which relationship types are displayed. This allows you to create focused, organized views of relationships.

---

## Current Status

✅ **Implemented:**
- Section-level filtering for relationship types
- Restored grid ordering within sections
- Support for multiple relationship sections with different configurations

⚠️ **Pending:**
- UI in Entry Layout Builder to configure visible/hidden types (currently manual configuration required)

---

## How to Use (Manual Configuration)

### Step 1: Identify Relationship Definition IDs

First, find the IDs of the relationship types you want to show or hide:

```sql
SELECT id, name, label_from_side, label_to_side 
FROM RelationshipDefinition 
ORDER BY name;
```

Example output:
```
id | name                 | label_from_side        | label_to_side
---+----------------------+------------------------+----------------------
1  | org_parent           | Parent Organization    | Child Organizations
2  | org_child            | Child Organizations    | Parent Organization  
3  | team_member          | Team Members           | Member Of
4  | project              | Projects               | Worked On By
5  | supplier             | Suppliers              | Customer Of
```

### Step 2: Find Your Section ID

Find the relationships section you want to configure:

```sql
SELECT els.id, els.title, els.section_type, etl.entry_type_id, et.singular_label
FROM EntryLayoutSection els
JOIN EntryTypeLayout etl ON els.layout_id = etl.id
JOIN EntryType et ON etl.entry_type_id = et.id
WHERE els.section_type = 'relationships'
ORDER BY et.singular_label, els.id;
```

### Step 3: Configure the Section

#### Option A: Show Only Specific Types (Whitelist)

```sql
-- Show only Parent Organization and Child Organizations
UPDATE EntryLayoutSection 
SET config = json_set(
    COALESCE(config, '{}'), 
    '$.visible_relationship_types', 
    json('[1, 2]')
)
WHERE id = <section_id>;
```

#### Option B: Hide Specific Types (Blacklist)

```sql
-- Hide Suppliers and Customers, show everything else
UPDATE EntryLayoutSection 
SET config = json_set(
    COALESCE(config, '{}'), 
    '$.hidden_relationship_types', 
    json('[5, 6]')
)
WHERE id = <section_id>;
```

#### Option C: Reset to Show All (Default)

```sql
-- Remove filtering, show all relationship types
UPDATE EntryLayoutSection 
SET config = json_set(
    json_set(
        COALESCE(config, '{}'), 
        '$.visible_relationship_types', 
        json('[]')
    ),
    '$.hidden_relationship_types', 
    json('[]')
)
WHERE id = <section_id>;
```

---

## Example Use Cases

### Use Case 1: Organizational Structure Section

Create a section that shows only organizational relationships:

```sql
-- Section showing Parent Organization and Child Organizations
UPDATE EntryLayoutSection 
SET 
    title = 'Organizational Structure',
    config = json_set(
        COALESCE(config, '{}'), 
        '$.visible_relationship_types', 
        json('[1, 2]')
    )
WHERE id = <section_id>;
```

### Use Case 2: Team & Projects Section

Create a section for people and project relationships:

```sql
-- Section showing Team Members and Projects
UPDATE EntryLayoutSection 
SET 
    title = 'Team & Projects',
    config = json_set(
        COALESCE(config, '{}'), 
        '$.visible_relationship_types', 
        json('[3, 4]')
    )
WHERE id = <section_id>;
```

### Use Case 3: Business Relationships Section

Create a section for external relationships, hiding internal ones:

```sql
-- Section hiding organizational and team relationships
UPDATE EntryLayoutSection 
SET 
    title = 'Business Relationships',
    config = json_set(
        COALESCE(config, '{}'), 
        '$.hidden_relationship_types', 
        json('[1, 2, 3]')
    )
WHERE id = <section_id>;
```

---

## Multiple Sections Example

You can create multiple relationship sections on the same entry type:

```sql
-- Step 1: Add a second relationships section
INSERT INTO EntryLayoutSection (
    layout_id, section_type, title, position_x, position_y,
    width, height, is_visible, is_collapsible, default_collapsed,
    config, display_order
)
SELECT 
    layout_id,
    'relationships',
    'Business Partners',
    6,  -- position on right half
    10, -- position below other sections
    6,  -- half width
    4,  -- height
    1,  -- visible
    1,  -- collapsible
    0,  -- not collapsed
    json('{"visible_relationship_types": [5, 6]}'), -- only suppliers and customers
    10  -- display order
FROM EntryLayoutSection
WHERE id = <existing_section_id>;

-- Step 2: Update the original section to show only organizational relationships
UPDATE EntryLayoutSection 
SET 
    title = 'Organization',
    config = json_set(
        COALESCE(config, '{}'), 
        '$.visible_relationship_types', 
        json('[1, 2]')
    )
WHERE id = <existing_section_id>;
```

---

## Verifying Configuration

### Check Current Configuration

```sql
SELECT 
    els.id,
    els.title,
    et.singular_label as entry_type,
    json_extract(els.config, '$.visible_relationship_types') as visible_types,
    json_extract(els.config, '$.hidden_relationship_types') as hidden_types
FROM EntryLayoutSection els
JOIN EntryTypeLayout etl ON els.layout_id = etl.id
JOIN EntryType et ON etl.entry_type_id = et.id
WHERE els.section_type = 'relationships';
```

### See Which Types Will Be Shown

```sql
-- For a specific section, see which relationship definitions will be displayed
WITH section_config AS (
    SELECT 
        json_extract(config, '$.visible_relationship_types') as visible,
        json_extract(config, '$.hidden_relationship_types') as hidden
    FROM EntryLayoutSection
    WHERE id = <section_id>
)
SELECT 
    rd.id,
    rd.name,
    rd.label_from_side,
    rd.label_to_side,
    CASE 
        WHEN (SELECT visible FROM section_config) IS NOT NULL 
             AND (SELECT visible FROM section_config) != '[]'
        THEN IIF(json_each.value = rd.id, 'SHOWN', 'HIDDEN')
        WHEN (SELECT hidden FROM section_config) IS NOT NULL 
             AND (SELECT hidden FROM section_config) != '[]'
        THEN IIF(json_each.value = rd.id, 'HIDDEN', 'SHOWN')
        ELSE 'SHOWN (default)'
    END as display_status
FROM RelationshipDefinition rd
LEFT JOIN section_config ON 1=1
LEFT JOIN json_each((SELECT visible FROM section_config)) ON 1=1
ORDER BY rd.name;
```

---

## Troubleshooting

### Issue: No relationship types showing

**Cause:** Empty `visible_relationship_types` array acts as whitelist with nothing selected.

**Fix:**
```sql
-- Reset to show all
UPDATE EntryLayoutSection 
SET config = json_set(
    COALESCE(config, '{}'), 
    '$.visible_relationship_types', 
    json('[]')
)
WHERE id = <section_id>;
```

### Issue: Section says "No relationship types configured"

**Cause:** All relationship types are filtered out by configuration.

**Fix:** Check your configuration and relationship definition IDs:
```sql
SELECT 
    json_extract(config, '$.visible_relationship_types') as visible,
    json_extract(config, '$.hidden_relationship_types') as hidden
FROM EntryLayoutSection
WHERE id = <section_id>;
```

### Issue: Wrong relationships showing

**Cause:** Incorrect relationship definition IDs in configuration.

**Fix:** Double-check the relationship definition IDs:
```sql
SELECT id, name, label_from_side, label_to_side 
FROM RelationshipDefinition 
ORDER BY id;
```

---

## Future: UI Configuration (Coming Soon)

The Entry Layout Builder will be updated with a visual interface for configuring relationship type filters:

**Planned Features:**
- ☐ Checkbox list of available relationship types
- ☐ "Show Only" vs "Hide" mode toggle
- ☐ Live preview of which types will be displayed
- ☐ Drag-and-drop to reorder (already supported, just needs UI)

---

## Notes

- **Ordering:** Custom grid order (from `RelationshipGridOrder` table) is preserved within filtered views
- **Empty Cards:** The "Show Empty" toggle still works with filtered views
- **Multiple Sections:** Each section filters independently - you can have different views on the same entry
- **Backward Compatible:** Sections without configuration show all types (default behavior)

---

## Questions?

If you encounter any issues or have questions about this feature, check:
1. [RELATIONSHIP_SECTION_CONFIGURATION.md](./RELATIONSHIP_SECTION_CONFIGURATION.md) - Full technical documentation
2. [RELATIONSHIP_GRID_ORDERING.md](./RELATIONSHIP_GRID_ORDERING.md) - Grid ordering feature
3. Docker logs: `docker compose logs -f template`
