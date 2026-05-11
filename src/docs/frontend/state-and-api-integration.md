# Frontend State and API Integration

## Scope

How frontend state is synchronized with backend APIs and SSE streaming responses.

## Current Implementation

### API Client Rules

- Base URL uses VITE_API_BASE_URL or defaults to http://localhost:8000.
- Bearer token is stored in localStorage and applied to outgoing requests.
- apiRequest helper parses standardized backend error detail messages.

### Thread Lifecycle State

- getThreads loads sidebar list.
- createThread inserts at beginning of local list.
- renameThread maps and replaces thread object in state.
- deleteThread removes thread and reselects fallback thread.

### Chat State

- ChatWindow fetches existing thread messages on thread switch.
- sendMessage appends local optimistic user + assistant placeholder messages.
- SSE token events append text into assistant placeholder.
- SSE attachment events append generated attachment metadata to assistant message.
- SSE done terminates stream processing.
- RAG fallback event disables ragEnabled state for current thread session.

### Mode-Driven Input State

- InputBar supports modes: normal, upload, upload_pdf_rag, generate_image.
- Upload modes dispatch selected files to useAttachments hook via custom event.
- PDF mode enables per-thread RAG toggle only after upload/indexing reaches ready state.
- Generate-image mode normalizes plain text prompts to /image command form before send.

## Step-by-Step Streaming State Flow

1. User submits input.
2. Draft is cleared locally.
3. User and empty assistant messages are appended.
4. API stream starts.
5. Every token mutates assistant message content.
6. Optional thread_name callback updates thread list title.
7. Stream completion leaves final assembled assistant message in UI.

## Known Frontend Constraints

- No reconnect logic for interrupted SSE stream.
- Thread operation error catch blocks currently suppress display.
- Single active stream assumption per chat window instance.

## Enhancement Hooks

- Add AbortController to cancel in-flight stream on thread switch.
- Add durable query cache with TanStack Query for threads/messages.
- Add exponential backoff retry on transient network errors.
- Add typed SSE event parser with versioned event schema.
