# Backend Overview

## Scope

FastAPI backend architecture, responsibilities by layer, and runtime behavior.

## Current Implementation

### Application Startup

- Entry point initializes FastAPI app with lifespan handler.
- DB schema initialization is attempted at startup.
- If DB init fails, server still starts and logs exception.
- CORS allows localhost frontend dev ports and optional configured frontend URL.

### API Surface

- /api/auth
  - register, login, google login, me
- /api/chat
  - stream chat responses
  - list user history (legacy endpoint)
  - upload generic attachments
  - upload PDF for RAG indexing
  - download attachments
  - view image attachments
- /api/threads
  - list/create/rename/delete threads
  - list messages by thread
- /api/sql
  - convert natural language question to SQL SELECT
  - execute query on Supabase PostgreSQL and return SQL + rows

### Dependency Injection

- Async DB session provided per request.
- Current user resolved from Bearer JWT.
- Development mode can fallback to placeholder user if token is absent.

### Service Layer Pattern

- Routers are thin and delegate business logic to services.
- Services isolate DB operations and error handling.
- Thread naming and chat memory slicing are implemented in services.
- RAG indexing/retrieval and image generation are handled in dedicated services.

## Error Handling Strategy

- Router-level HTTP errors for validation/not-found/unauthorized.
- Service-level try/except to protect stream continuity where possible.
- Distinguishes LLM upstream errors (mapped to 502) from unexpected errors (500).

## Enhancement Hooks

- Add versioned APIs under /api/v1 as module count grows.
- Add repository layer if DB query complexity increases.
- Add middleware for request IDs and structured tracing.
- Add rate limiting and per-user quotas on chat endpoints.
