# Production Readiness Guide

## Scope

Operational checklist and reference architecture for running AI_Forge safely in production.

## Current Implementation

### Existing Strengths

- JWT-based API authentication and per-user data ownership checks.
- Structured separation of API/service/model layers.
- Centralized AI client initialization for text and image models.
- RAG storage separated by user collection in Chroma.

### Current Gaps

- No request ID/tracing middleware.
- No explicit rate limiting or abuse controls.
- Best-effort persistence behavior can hide data durability failures.
- No production deployment topology documented.
- No formal backup/restore runbook for DB and upload/chroma storage.

## Step-by-Step Flow

1. Provision managed Postgres and secure credentials.
2. Provision persistent storage for uploads and Chroma data.
3. Configure environment variables for backend and frontend.
4. Deploy backend behind reverse proxy and TLS termination.
5. Deploy frontend with API base URL pointing to production backend.
6. Run smoke tests: auth, thread CRUD, chat stream, file upload, PDF RAG, image generation.
7. Enable monitoring and alerting for error rates and latency.

## Deployment Baseline

- Backend:
  - Run multiple FastAPI workers behind a process manager/reverse proxy.
  - Set strict CORS allowlist via frontend_url.
- Storage:
  - Persist uploads and chroma_persist_dir on durable volumes.
  - Schedule backups for Postgres + upload files + Chroma directory.
- Network:
  - Enforce HTTPS only.
  - Restrict database and internal services to private network.

## Observability Baseline

- Logs:
  - JSON structured logs with request_id, user_email hash, endpoint, and error type.
- Metrics:
  - Request latency, non-2xx rates, SSE stream duration, upload failures, LLM provider failures.
- Alerts:
  - Error rate spike, stream failure spike, DB connectivity failures, disk utilization threshold.

## Security Baseline

- Rotate SECRET_KEY and model provider keys on schedule.
- Disable development fallback auth in non-development environments.
- Add per-user and per-IP request limits for auth/chat/upload routes.
- Enforce file type and size policy already implemented for uploads.
- Add malware scanning for uploaded files before indexing or reuse.

## Error Handling

- External provider outage:
  - Return controlled stream failure messages and keep endpoint responsive.
- DB unavailable:
  - Surface service degradation clearly in health checks and dashboards.
- Storage full:
  - Reject uploads with explicit error and trigger storage alerts.

## Enhancement Hooks

- Add /health and /ready endpoints with dependency checks.
- Add OpenTelemetry tracing across frontend request ID to backend logs.
- Add chaos and load test profiles for stream and upload-heavy scenarios.
