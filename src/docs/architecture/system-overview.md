# System Overview

## Scope

High-level architecture of AI_Forge across frontend and backend, including request flow, persistence, and LLM integration.

## Current Implementation

### Runtime Components

- Frontend: React + TypeScript + Vite application.
- Backend: FastAPI service with async SQLAlchemy.
- Database: PostgreSQL through asyncpg (configured via DATABASE_URL).
- LLM: LiteLLM/OpenAI-compatible endpoint via langchain-openai ChatOpenAI.
- Transport for chat responses: Server-Sent Events (SSE).

### Backend Modules

- API layer: auth, chat, threads routers.
- Service layer: chat_service, thread_service, user_service.
- Core layer: config, security, dependencies, passwords.
- Persistence layer: SQLAlchemy models and async DB session setup.

### Frontend Modules

- Page composition: ChatPage is root experience.
- API client: centralized in src/frontend/src/lib/api.ts.
- Chat UI: ThreadSidebar, ChatWindow, MessageList, InputBar.

## End-to-End Request Path

1. User action in UI calls function in lib/api.ts.
2. API request includes Bearer token if available.
3. FastAPI dependency resolves user from JWT token.
4. Router delegates to service functions.
5. Service reads/writes DB and invokes chain for LLM features.
6. Backend returns JSON or SSE stream.
7. Frontend applies response to local state and renders updates.

## Resilience and Degradation

- Backend startup continues even if DB initialization fails.
- In development mode without token, a development placeholder user can be used.
- Chat streaming continues when message persistence fails (best-effort persistence).

## Enhancement Hooks

- Add new domains as new router + service pair.
- Keep auth and token logic centralized in core/security.py and core/dependencies.py.
- Keep external AI provider integration centralized in app/ai/llm.py.
- Introduce background jobs later without changing API contracts by wrapping service operations.
