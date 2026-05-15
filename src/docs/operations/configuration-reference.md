# Configuration Reference

## Scope

Environment variables and runtime configuration values used by backend and frontend.

## Backend Configuration

### Core App

- SECRET_KEY: JWT signing secret.
- JWT_EXPIRE_MINUTES: token validity window.
- APP_NAME: FastAPI app title.
- ENVIRONMENT: development/other modes.
- FRONTEND_URL: optional additional CORS origin.
- CHAT_MEMORY_CONVERSATIONS: number of recent conversation turns in prompt memory (default 5).

### Database

- DATABASE_URL: PostgreSQL connection URL.
  - Can be postgresql://... or postgresql+asyncpg://...
- SUPABASE_SQL_DATABASE_URL: optional dedicated DB URL for natural-language SQL feature.
  - Falls back to DATABASE_URL when omitted.

### Project 8: NL to SQL

- NL2SQL_MAX_ROWS: default max rows returned by generated SELECT queries.
- NL2SQL_SCHEMA: schema name exposed to NL-to-SQL prompt context (default public).

### Project 10/12: Research Digest + MCP

- ARXIV_MCP_COMMAND: optional process command for MCP server runtime.
  - Default behavior uses active Python interpreter when empty.
- ARXIV_MCP_MODULE: MCP module name for arXiv tool server (default arxiv_mcp_server).
- ARXIV_MCP_STORAGE_PATH: storage path for MCP server state/cache (default ./.arxiv-mcp-server).

### LLM / LiteLLM

- LITELLM_PROXY_URL
- LITELLM_API_KEY
- LITELLM_USER_ID (optional, passed in model metadata)
- LLM_MODEL
- LITELLM_EMBEDDING_MODEL
- IMAGE_GEN_MODEL

### Google OAuth

- GOOGLE_CLIENT_ID
- GOOGLE_CLIENT_SECRET
- GOOGLE_REDIRECT_URI

### Misc

- CHROMA_PERSIST_DIR
- GOOGLE_SERVICE_ACCOUNT_JSON
- MAX_UPLOAD_MB
- UPLOAD_DIR

## Frontend Configuration

- VITE_API_BASE_URL: backend base URL (default http://localhost:8000).
- VITE_GOOGLE_CLIENT_ID: enables Google login button when set.

## Step-by-Step Config Load Behavior

1. Backend loads env from configured env file passed to uvicorn.
2. Settings object validates required fields at startup/import.
3. Frontend reads VITE_ variables at build/runtime through Vite.
4. API client applies fallback defaults when env vars are absent.

## Enhancement Hooks

- Introduce environment-specific typed config schema for frontend.
- Add startup config diagnostics endpoint (non-secret fields only).
- Add config linter script to verify required keys before boot.
