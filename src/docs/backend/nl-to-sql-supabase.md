# NL to SQL (Project 8)

## Goal

Convert a natural-language question into a PostgreSQL SELECT query, execute it against Supabase, and return both SQL and result rows to the UI.

## API

- Endpoint: POST /api/sql/query
- Auth: same Bearer token flow as other API routes (dev fallback user in development mode)

Request body:

```json
{
  "question": "what is the email of the name jagadesh",
  "max_rows": 50
}
```

Response body:

```json
{
  "question": "what is the email of the name jagadesh",
  "generated_sql": "SELECT email FROM contacts WHERE name = 'jagadesh' LIMIT 50",
  "rows": [{"email": "jagadesh123.com"}],
  "row_count": 1,
  "columns": ["email"],
  "generated_at": "2026-05-15T00:00:00Z"
}
```

## Safety Guardrails

- Generated SQL must be SELECT/CTE SELECT.
- DML/DDL keywords are blocked (insert, update, delete, drop, alter, etc.).
- Multiple statements are blocked.
- LIMIT is enforced when not present.

## Configuration

- SUPABASE_SQL_DATABASE_URL (optional): dedicated connection URL for NL-to-SQL.
- DATABASE_URL: fallback DB URL when dedicated URL is not set.
- NL2SQL_MAX_ROWS: default max row cap.
- NL2SQL_SCHEMA: schema metadata exposed to prompt.

## Frontend

A new Project 8 view is available in the app switcher:

- Existing Chat (existing implementation)
- Project 8 NL-SQL (new screen)

The Project 8 screen displays:

- Question input
- Generated SQL
- Response table
