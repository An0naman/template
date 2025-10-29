# Custom SQL Query Feature

## Overview
The Custom SQL Query feature allows you to write advanced SQL WHERE clauses to filter entries using complex logic that goes beyond the standard UI filters.

## Location
Navigate to the **Entries** page and expand the **Advanced Filters** section. Scroll down to find the **Custom SQL Query** section at the bottom.

## How to Use

### Basic Usage
1. Enter your SQL WHERE clause in the text area (without the `WHERE` keyword)
2. Click **Apply SQL Query** to execute
3. Results will be filtered based on your query
4. Use the checkbox to enable/disable the SQL filter

### Table Aliases Available
- `e` - Entry table
- `et` - EntryType table (joined)
- `er_from` - EntryRelationship (where entry is the source)
- `er_to` - EntryRelationship (where entry is the target)

### Direct Table Names (use in subqueries)
- `Entry` - Main entries table
- `EntryType` - Entry types definition
- `EntryState` - Entry states/statuses
- `EntryRelationship` - Relationships between entries

### Example Queries

#### 1. Simple text search
```sql
e.title LIKE '%wine%'
```

#### 2. Filter by entry type
```sql
e.entry_type_id = 2
```

#### 3. Combine multiple conditions
```sql
e.title LIKE '%Sample%' AND e.entry_type_id = 2
```

#### 4. Filter by relationships (Sample Bottles in Chamber #1)
```sql
e.id IN (
    SELECT source_entry_id 
    FROM EntryRelationship 
    WHERE target_entry_id = 5 
    AND relationship_type = 16
)
```

#### 5. Complex relationship query (Sample Bottles in Chamber#1 OR Chamber#2, with Recipe Style=Wine)
```sql
(
    e.id IN (
        SELECT source_entry_id 
        FROM EntryRelationship 
        WHERE target_entry_id IN (5, 6) 
        AND relationship_type = 16
    )
) AND (
    e.id IN (
        SELECT source_entry_id 
        FROM EntryRelationship er
        JOIN Entry recipe ON er.target_entry_id = recipe.id
        WHERE recipe.title LIKE '%Wine%'
        AND er.relationship_type = 15
    )
)
```

#### 6. Filter by date range
```sql
e.created_at >= '2024-01-01' AND e.created_at < '2025-01-01'
```

#### 7. Filter by status
```sql
e.status = 'Active' OR e.status = 'Fermenting'
```

#### 8. Entries without relationships
```sql
e.id NOT IN (
    SELECT DISTINCT source_entry_id FROM EntryRelationship
)
```

## Entry Table Columns

Common columns you can use in the `Entry` table (alias `e`):
- `id` - Entry ID (integer)
- `title` - Entry title (text)
- `description` - Entry description (text)
- `entry_type_id` - Entry type ID (integer)
- `status` - Status name (text, e.g. 'Active', 'Fermenting', etc.)
- `intended_end_date` - Intended end date (text)
- `actual_end_date` - Actual end date (text)
- `created_at` - Creation timestamp (text)

## Relationship Queries

### Find entries related to a specific entry
```sql
e.id IN (
    SELECT source_entry_id 
    FROM EntryRelationship 
    WHERE target_entry_id = <ENTRY_ID>
)
```

### Find entries with a specific relationship type
```sql
e.id IN (
    SELECT source_entry_id 
    FROM EntryRelationship 
    WHERE relationship_type = <RELATIONSHIP_TYPE_ID>
)
```

### Find entries related to entries matching a condition
```sql
e.id IN (
    SELECT er.source_entry_id 
    FROM EntryRelationship er
    JOIN Entry target ON er.target_entry_id = target.id
    WHERE target.title LIKE '%Chamber%'
)
```

## Security Features

The following SQL keywords are blocked for security:
- DROP
- DELETE
- INSERT
- UPDATE
- ALTER
- CREATE
- TRUNCATE
- EXEC/EXECUTE
- Comments (`--`)
- Multiple statements (`;`)

Only SELECT queries are allowed.

## Tips

1. **Test incrementally**: Start with simple queries and gradually add complexity
2. **Check syntax carefully**: SQL errors will be displayed in red below the query
3. **Use LIKE for text searches**: `e.title LIKE '%search%'` for partial matches
4. **Combine with UI filters**: SQL queries work alongside type, status, and other filters
5. **Save your queries**: Complex queries can be saved as part of a Saved Search
6. **Use IN for multiple values**: `e.id IN (1, 2, 3)` to match multiple IDs

## Troubleshooting

### "SQL query error: no such column"
- Check that you're using the correct table alias (`e`, `et`, `s`, etc.)
- Verify the column name exists in the table

### "Dangerous SQL keyword detected"
- Your query contains a blocked keyword
- Ensure you're only using SELECT-style queries

### Query returns no results
- Test parts of your query separately
- Check that the entry IDs or relationship IDs exist in your database
- Verify your logic (AND vs OR)

## Advanced: Debugging Your Query

To see the actual SQL being executed, check the browser console (F12) and look for:
```
Executing custom SQL query: SELECT DISTINCT e.id FROM entry e ...
```

The full query with your WHERE clause will be logged there.

## Performance Considerations

- Complex subqueries may be slower on large datasets
- Use specific conditions to reduce the result set
- Consider using indexes if queries are consistently slow
- The result limit (default 50) applies after SQL filtering

## Integration with Other Filters

SQL queries are combined with other filters using AND logic:
- Quick search
- Type filter
- Status filter
- Date range
- Relationship filters (UI-based)
- **AND** Custom SQL query

All must match for an entry to be displayed.
