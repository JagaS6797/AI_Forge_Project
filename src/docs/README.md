# AI_Forge Documentation

This folder contains architecture-level and implementation-level technical documentation for the current system.

## Documentation Goals

- Document exactly what is implemented now.
- Keep each feature in its own file for targeted updates.
- Make future enhancement work easy by using stable sections and update checklists.

## Structure

- architecture/
  - system-overview.md
  - data-model.md
  - ai-capabilities.md
- backend/
  - backend-overview.md
  - authentication.md
  - chat-streaming-memory.md
  - threads.md
  - attachments.md
  - ATTACHMENTS_COMPLETE.md
  - rag-pdf-retrieval.md
  - image-generation.md
  - test-cases.md
- frontend/
  - frontend-overview.md
  - state-and-api-integration.md
  - test-cases.md
- flows/
  - 01-user-auth-flow.md
  - 02-thread-lifecycle-flow.md
  - 03-chat-streaming-flow.md
  - 04-pdf-rag-ingestion-and-query-flow.md
  - 05-image-generation-flow.md
- operations/
  - local-development.md
  - configuration-reference.md
  - testing-and-quality.md
  - api-endpoints-reference.md
  - attachment-fixes-history.md
  - production-readiness.md
  - history/
    - attachment-fixes-applied.md
    - image-viewing-fix-notes.md
    - attachment-implementation-summary.md
- roadmap/
  - enhancement-guide.md
- templates/
  - feature-doc-template.md

## Documentation Rules

1. One feature area per file.
2. Every file must contain:
   - Scope
   - Current Implementation
   - Step-by-Step Flow
   - Error Handling
   - Enhancement Hooks
3. When code changes, update only the impacted files.
4. Keep API and schema names aligned with source code.

## Update Workflow

1. Identify changed backend/frontend modules.
2. Update matching feature doc file(s).
3. Update one or more flow docs if request/response sequence changed.
4. Update configuration-reference.md if new env vars or defaults were introduced.
5. Add an entry in enhancement-guide.md if change introduces a new extensibility pattern.

## Ownership

- Backend docs: backend/ + architecture/
- Frontend docs: frontend/
- End-to-end behavior docs: flows/
- Runbook and maintenance docs: operations/
