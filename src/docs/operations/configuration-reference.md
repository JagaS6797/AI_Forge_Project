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
