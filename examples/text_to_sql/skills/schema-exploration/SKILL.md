# Schema Exploration Skill

This skill provides guidelines for exploring database schemas.

## Exploration Process

1. **List all tables**: Get overview of available data
2. **Examine table schemas**: Understand column types and relationships
3. **Check sample data**: View actual values to understand context
4. **Identify relationships**: Find primary/foreign key connections

## Chinook Database Overview

### Main Tables

| Table | Description |
|-------|-------------|
| Artist | Music artists |
| Album | Albums linked to artists |
| Track | Individual songs/tracks |
| Genre | Music genres |
| MediaType | Media formats |
| Playlist | User playlists |
| PlaylistTrack | Tracks in playlists |
| Customer | Customer information |
| Employee | Store employees |
| Invoice | Sales invoices |
| InvoiceLine | Invoice line items |

### Key Relationships

- Artist → Album (one-to-many)
- Album → Track (one-to-many)
- Track → Genre (many-to-one)
- Customer → Invoice (one-to-many)
- Invoice → InvoiceLine (one-to-many)
- InvoiceLine → Track (many-to-one)
- Employee → Customer (sales support)

## Best Practices

1. Always check schema before writing queries
2. Understand data types for proper comparisons
3. Note nullable columns for NULL handling
4. Identify primary keys for efficient lookups
