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
- /api/research
  - stream research digest events (status, papers_found, selected_papers, digest_chunk, done)
- /api/tic-tac-toe
  - start new game
  - submit player move and receive agent response state

### Dependency Injection

- Async DB session provided per request.
- Current user resolved from Bearer JWT.
- Development mode can fallback to placeholder user if token is absent.

### Service Layer Pattern

- Routers are thin and delegate business logic to services.
- Services isolate DB operations and error handling.
- Thread naming and chat memory slicing are implemented in services.
- RAG indexing/retrieval and image generation are handled in dedicated services.
- Research digest orchestration uses LangGraph state graph nodes for search and paper selection.
- MCP runtime configuration for arXiv tooling is centralized in app/ai/mcp_config.py.

### Research Digest Orchestration (Project 10 + Project 12)

- Search stage uses arXiv MCP tool invocation through stdio transport.
- Tool payload parsing includes resilience for empty, wrapped, or partially structured text responses.
- Request-level toggle `use_mcp` controls search mode:
  - true: MCP-first search strategy
  - false: direct arXiv search strategy
- MCP-first mode automatically falls back to direct arXiv if MCP fails or returns no usable papers.
- Selection stage uses LLM-based relevance filtering over retrieved papers.
- LangGraph flow currently composes:
  - START -> search -> select -> END
- Final digest writing is streamed token-wise through SSE for live UI updates.

## Error Handling Strategy

- Router-level HTTP errors for validation/not-found/unauthorized.
- Service-level try/except to protect stream continuity where possible.
- Distinguishes LLM upstream errors (mapped to 502) from unexpected errors (500).

## Enhancement Hooks

- Add versioned APIs under /api/v1 as module count grows.
- Add repository layer if DB query complexity increases.
- Add middleware for request IDs and structured tracing.
- Add rate limiting and per-user quotas on chat endpoints.
