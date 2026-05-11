# Frontend Test Cases

## Scope

Comprehensive frontend test matrix for auth screens, thread lifecycle UX, chat streaming UI, attachments, PDF RAG toggling, image generation mode, and error handling.

## Current Implementation Areas Covered

- Core page orchestration: ChatPage and ChatWindow
- Chat UI components: InputBar, MessageList, MessageAttachments, ThreadSidebar
- Attachments state: useAttachments hook
- API integration and SSE parsing: src/frontend/src/lib/api.ts

## Test Data and Environment Baseline

- Mock API server for unit/component tests.
- E2E environment with backend test instance for flow tests.
- Seed user with multiple threads and mixed message types.

## Test Matrix

### A. Authentication UX

- FE-AUTH-001: Login screen renders by default when no valid token.
- FE-AUTH-002: Successful login stores token and transitions to chat screen.
- FE-AUTH-003: Failed login shows inline error text.
- FE-AUTH-004: Register success transitions with success feedback.
- FE-AUTH-005: Register failure shows inline error text.
- FE-AUTH-006: Google login success enters chat state.
- FE-AUTH-007: Token bootstrap with /me success restores session.
- FE-AUTH-008: Invalid token bootstrap clears session and returns to login.

### B. Thread Sidebar and Lifecycle

- FE-THR-001: Initial thread load selects first thread when present.
- FE-THR-002: Create thread adds new item and activates it.
- FE-THR-003: Rename thread updates sidebar item label.
- FE-THR-004: Delete thread removes item and selects fallback thread.
- FE-THR-005: Delete last thread results in empty-state behavior.
- FE-THR-006: Incoming thread_name SSE event updates current thread title.

### C. Chat History and Rendering

- FE-CHAT-001: Switching thread triggers message history fetch and render.
- FE-CHAT-002: History loading spinner shown while fetching.
- FE-CHAT-003: User and assistant bubbles render correct styles.
- FE-CHAT-004: Messages with attachments render attachment block.

### D. Streaming Behavior

- FE-SSE-001: On send, optimistic user + assistant placeholder appears.
- FE-SSE-002: token events append incrementally to assistant message.
- FE-SSE-003: done event stops streaming state and spinner text.
- FE-SSE-004: malformed or failed stream shows user-visible error.
- FE-SSE-005: multiple consecutive sends maintain correct message order.

### E. InputBar Modes and Interaction

- FE-INP-001: Plus menu opens/closes correctly.
- FE-INP-002: Mode switch to normal/upload/upload_pdf_rag/generate_image works.
- FE-INP-003: Enter submits and Shift+Enter inserts newline.
- FE-INP-004: Send button disabled when no text and no attachments.
- FE-INP-005: Send button disabled during upload or send pending.

### F. Attachment Upload UX

- FE-ATT-001: Selecting files triggers upload via useAttachments.
- FE-ATT-002: Uploaded non-PDF attachments render as chips with icon and size.
- FE-ATT-003: Removing attachment chip updates local state.
- FE-ATT-004: Upload error banner appears and is readable.
- FE-ATT-005: Attachment-only send path works (no message text).

### G. Attachment Rendering in Messages

- FE-ATT-RND-001: MessageAttachments renders non-image downloads.
- FE-ATT-RND-002: Image attachments fetch with auth and show thumbnails.
- FE-ATT-RND-003: Image modal expands/collapses properly.
- FE-ATT-RND-004: Download action triggers blob download for attachment.
- FE-ATT-RND-005: Missing image data shows graceful fallback icon.

### H. PDF RAG UX

- FE-RAG-001: PDF mode accepts only PDF in file picker.
- FE-RAG-002: PDF upload status transitions uploading -> processing -> ready.
- FE-RAG-003: Ready state enables RAG toggle.
- FE-RAG-004: ragFallback event from backend disables toggle state.
- FE-RAG-005: Sending with ragEnabled passes rag_enabled=true.

### I. Image Generation UX

- FE-IMG-001: Generate image mode placeholder text changes appropriately.
- FE-IMG-002: Plain prompt in generate mode is prefixed with /image before send.
- FE-IMG-003: Attachment event from stream appends generated image to assistant message.
- FE-IMG-004: Generated image is visible in message attachments after completion.

### J. API Client and Error Handling

- FE-API-001: apiRequest surfaces backend detail.message where available.
- FE-API-002: uploadAttachments surfaces validation error detail text.
- FE-API-003: uploadPdf surfaces backend error detail text.
- FE-API-004: downloadAttachment rejects on non-200 and UI handles failure.

### K. Accessibility and Responsiveness

- FE-A11Y-001: Interactive controls are keyboard reachable.
- FE-A11Y-002: Buttons include meaningful labels/titles.
- FE-A11Y-003: Modal close action is reachable and obvious.
- FE-RESP-001: Input bar and chips remain usable on narrow mobile widths.
- FE-RESP-002: Sidebar/chat layout remains navigable on tablet and desktop widths.

### L. Performance and Stability

- FE-PERF-001: Long streaming responses do not freeze typing or scrolling.
- FE-PERF-002: Large attachment chip counts remain scrollable and stable.
- FE-PERF-003: Rapid thread switching does not corrupt active thread messages.
- FE-PERF-004: Memory cleanup for image blob URLs prevents progressive leak.

## Suggested Automation Priority

1. P0: FE-AUTH-001..004, FE-THR-001..004, FE-SSE-001..003, FE-ATT-001..005.
2. P1: FE-ATT-RND group, FE-RAG group, FE-IMG group, FE-API group.
3. P2: FE-A11Y group, FE-RESP group, FE-PERF group.

## Enhancement Hooks

- Add component tests (React Testing Library) for ChatWindow/InputBar/MessageAttachments.
- Add e2e smoke and regression coverage for auth -> thread -> chat -> attachments -> RAG/image flows.
- Add visual regression checks for message/attachment rendering states.
