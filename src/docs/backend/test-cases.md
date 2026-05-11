# Backend Test Cases

## Scope

Comprehensive backend test matrix for auth, threads, chat streaming, attachments, PDF RAG, image generation, and cross-cutting concerns.

## Current Implementation Areas Covered

- API routers: auth, chat, threads
- Services: user, thread, chat, attachment, RAG, image generation
- Persistence: SQLAlchemy models + async DB sessions
- Streaming: SSE contract for chat responses

## Test Data and Environment Baseline

- Test DB isolated from development DB.
- Seed users:
  - valid amzur account
  - non-amzur account
- Seed threads and messages for ownership and history tests.
- Mock model providers for deterministic stream tests where needed.

## Test Matrix

### A. Authentication and Authorization

- BE-AUTH-001: Register valid amzur email and password.
- BE-AUTH-002: Reject register for non-amzur domain.
- BE-AUTH-003: Reject duplicate register email.
- BE-AUTH-004: Login succeeds with correct credentials.
- BE-AUTH-005: Login fails with wrong password.
- BE-AUTH-006: Login fails for non-amzur email.
- BE-AUTH-007: Google login succeeds with valid configured token.
- BE-AUTH-008: Google login fails when GOOGLE_CLIENT_ID missing.
- BE-AUTH-009: Me endpoint succeeds with valid bearer token.
- BE-AUTH-010: Me endpoint returns 401 for invalid/expired token.
- BE-AUTH-011: Development mode placeholder user works when token absent.
- BE-AUTH-012: Non-development mode rejects missing token.

### B. Threads

- BE-THR-001: Create thread with explicit name.
- BE-THR-002: Create thread with default name.
- BE-THR-003: List threads ordered by updated_at descending.
- BE-THR-004: Rename owned thread succeeds.
- BE-THR-005: Rename unknown thread returns 404.
- BE-THR-006: Delete owned thread succeeds.
- BE-THR-007: Delete unknown/unowned thread returns 404.
- BE-THR-008: Get thread messages includes attachment metadata array.
- BE-THR-009: Get messages for unowned thread returns 404.

### C. Chat Streaming Core

- BE-CHAT-001: Send normal message returns SSE stream with token events and done.
- BE-CHAT-002: First message in new thread emits optional thread_name event.
- BE-CHAT-003: Empty message with no attachments rejected.
- BE-CHAT-004: Attachment-only request accepted.
- BE-CHAT-005: History slicing respects CHAT_MEMORY_CONVERSATIONS.
- BE-CHAT-006: User message persistence failure does not kill stream.
- BE-CHAT-007: Assistant persistence failure does not kill stream.
- BE-CHAT-008: HTTPException during stream yields token error + done.
- BE-CHAT-009: Unexpected exception during stream yields token error + done.

### D. SSE Contract and Parsing Safety

- BE-SSE-001: Event payload JSON is parseable for token event.
- BE-SSE-002: done=true is final event and stream closes.
- BE-SSE-003: rag_fallback event appears only when RAG disabled by relevance path.
- BE-SSE-004: Image path emits attachment event with required fields.
- BE-SSE-005: No malformed partial JSON chunks are emitted.

### E. Attachments Upload and Download

- BE-ATT-001: Upload supported image MIME succeeds.
- BE-ATT-002: Upload supported text/code MIME succeeds.
- BE-ATT-003: Upload rejected for blocked extension (exe/bat/sh and similar).
- BE-ATT-004: Upload rejected for oversized file above MAX_UPLOAD_MB.
- BE-ATT-005: Upload rejected for unsupported MIME.
- BE-ATT-006: Download owned attachment succeeds.
- BE-ATT-007: Download unowned attachment returns 403.
- BE-ATT-008: Download missing attachment returns 404.
- BE-ATT-009: Download where file missing on disk returns 404.
- BE-ATT-010: Image endpoint rejects non-image attachment with 400.

### F. Attachment Message Linking and Retrieval

- BE-ATT-LNK-001: Sending attachment_ids links file_attachments.message_id.
- BE-ATT-LNK-002: chat_messages.attachment_ids contains sent IDs.
- BE-ATT-LNK-003: Thread message response includes matching attachment objects.
- BE-ATT-LNK-004: Mixed attachment types returned with attachment_type fields.

### G. PDF RAG Ingestion

- BE-RAG-UP-001: upload-pdf accepts valid PDF and thread_id.
- BE-RAG-UP-002: upload-pdf rejects non-PDF MIME.
- BE-RAG-UP-003: upload-pdf rejects oversized PDF.
- BE-RAG-UP-004: upload-pdf rejects unknown/unowned thread.
- BE-RAG-UP-005: upload-pdf fails for unreadable/empty text PDFs.
- BE-RAG-UP-006: upload-pdf response includes chunks_indexed and ready status.
- BE-RAG-UP-007: rag_documents row created with attachment_id uniqueness.

### H. RAG Answering Path

- BE-RAG-ANS-001: rag_enabled=true with relevant chunks returns RAG answer tokens.
- BE-RAG-ANS-002: rag_enabled=true with low relevance emits rag_fallback then normal path.
- BE-RAG-ANS-003: rag_enabled=false with available RAG docs follows normal non-RAG prompt policy.
- BE-RAG-ANS-004: No RAG documents in thread still allows normal chat.

### I. Image Generation Path

- BE-IMG-001: /image prefix triggers image generation route.
- BE-IMG-002: Natural language generation intent triggers image route.
- BE-IMG-003: Generated image persisted as file attachment.
- BE-IMG-004: SSE emits assistant token + attachment + done.
- BE-IMG-005: Provider returns no payload -> graceful error token + done.
- BE-IMG-006: Provider URL download failure -> graceful error token + done.

### J. Data Integrity and Cascades

- BE-DB-001: Deleting thread cascades chat_messages in that thread.
- BE-DB-002: Deleting message cascades linked file_attachments by message_id where applicable.
- BE-DB-003: Deleting user cascades threads, messages, attachments, and rag_documents.
- BE-DB-004: Migration path keeps existing deployments functional (attachment_ids and attachment_type columns).

### K. Security and Hardening

- BE-SEC-001: JWT tampering detected and rejected.
- BE-SEC-002: Cross-user thread/attachment access prevented.
- BE-SEC-003: File path traversal attempts in filenames do not escape upload directory.
- BE-SEC-004: Sensitive values (tokens/keys) not leaked in error payloads.

### L. Performance and Reliability

- BE-PERF-001: Streaming first-token latency under target threshold in local benchmark.
- BE-PERF-002: Concurrent streams from multiple users remain isolated.
- BE-PERF-003: Large thread history still returns within acceptable query time.
- BE-PERF-004: Multiple attachment upload batch under max count/size behaves predictably.

## Suggested Automation Priority

1. P0: BE-AUTH-001..006, BE-THR-001..007, BE-CHAT-001..004, BE-ATT-001..010.
2. P1: BE-ATT-LNK group, BE-RAG-UP group, BE-RAG-ANS group, BE-IMG group.
3. P2: BE-SSE group, BE-DB group, BE-SEC group, BE-PERF group.

## Enhancement Hooks

- Convert this matrix into pytest parametrized suites with shared fixtures.
- Add contract-test snapshot assertions for SSE event schema.
- Add load-test profile for streaming and upload-heavy scenarios.
