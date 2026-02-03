# Query Writing Skill

This skill provides guidelines for writing effective SQL queries.

## Query Structure

1. **SELECT clause**: Only select columns you need
2. **FROM clause**: Identify the main table
3. **JOIN clause**: Use appropriate join types (INNER, LEFT, etc.)
4. **WHERE clause**: Filter data appropriately
5. **GROUP BY**: For aggregations
6. **ORDER BY**: Sort results meaningfully
7. **LIMIT**: Restrict result count (default: 5)

## Common Patterns

### Counting Records
```sql
SELECT COUNT(*) as total FROM TableName WHERE condition;
```

### Aggregations with Grouping
```sql
SELECT column, SUM(amount) as total
FROM TableName
GROUP BY column
ORDER BY total DESC
LIMIT 5;
```

### Joining Tables
```sql
SELECT a.name, b.value
FROM TableA a
INNER JOIN TableB b ON a.id = b.a_id
WHERE condition;
```

## Error Handling

If a query fails:
1. Check column names exist in the schema
2. Verify table names are correct
3. Ensure JOIN conditions are valid
4. Look for syntax errors (missing commas, quotes)
