# Testing and Quality

## Scope

Current quality tooling and recommended extension path for coverage.

## Current Tooling

### Backend

- pytest
- pytest-asyncio
- pytest-cov
- ruff
- pre-commit

### Frontend

- eslint
- TypeScript project build checks via tsc -b in build script

## Current Gaps

- No documented automated end-to-end test suite yet.
- No explicit SSE stream contract tests documented.
- No integration test matrix for auth + threads + chat combined.

## Recommended Test Layers

1. Unit tests
   - _recent_conversations behavior under edge cases.
   - auth validators and token decode failure paths.
2. Integration tests
   - auth endpoints against test DB.
   - thread CRUD ownership checks.
   - chat stream endpoint with mocked LLM provider.
3. Frontend component tests
   - ChatWindow token-append behavior.
   - ThreadSidebar rename/delete interactions.
4. End-to-end smoke tests
   - login -> create thread -> send message -> verify stream completion.

## Quality Gates Proposal

- Backend: ruff + pytest must pass.
- Frontend: eslint + build must pass.
- Optional future gate: minimal integration coverage threshold for core flows.

## Enhancement Hooks

- Add contract tests for SSE event payload schema.
- Add load/perf test for long streaming responses.
- Add static analysis for dependency vulnerability checks.
