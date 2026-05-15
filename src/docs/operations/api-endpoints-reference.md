# API Endpoints Reference

## Authentication Endpoints

### POST /api/auth/register
Create new account.
- Request: `{ user_id: string, password: string }`
- Response: `{ access_token: string, token_type: string, user: { email: string } }`
- Status: 201 Created

### POST /api/auth/login
Login with credentials.
- Request: `{ user_id: string, password: string }`
- Response: `{ access_token: string, token_type: string, user: { email: string } }`
- Status: 200 OK

### POST /api/auth/google
Login with Google token.
- Request: `{ credential: string }`
- Response: `{ access_token: string, token_type: string, user: { email: string } }`
- Status: 200 OK

### GET /api/auth/me
Get current authenticated user.
- Response: `{ email: string }`
- Status: 200 OK
- Auth: Required (Bearer token)

## Thread Endpoints

### GET /api/threads
List all threads for current user.
- Response: `[{ id: string, name: string, created_at: string, updated_at: string }, ...]`
- Status: 200 OK
- Auth: Required

### POST /api/threads
Create new thread.
- Request: `{ name: string }`
- Response: `{ id: string, name: string, created_at: string, updated_at: string }`
- Status: 201 Created
- Auth: Required

### PATCH /api/threads/{thread_id}
Rename thread.
- Request: `{ name: string }`
- Response: `{ id: string, name: string, created_at: string, updated_at: string }`
- Status: 200 OK
- Auth: Required

### DELETE /api/threads/{thread_id}
Delete thread and all messages.
- Status: 204 No Content
- Auth: Required

### GET /api/threads/{thread_id}/messages
List messages in thread.
- Response: `[{ id: string, role: "user" | "assistant", content: string, created_at: string, attachment_ids: string[], attachments: [{ id, file_name, file_type, attachment_type, file_size, created_at }] }, ...]`
- Status: 200 OK
- Auth: Required

## Chat Endpoints

### POST /api/chat
Send message with optional attachments.
- Request: `{ message: string, thread_id: string, attachment_ids?: string[], rag_enabled?: boolean }`
- Response: Server-Sent Events (text/event-stream)
  - `{ token: string }` (repeating)
  - `{ thread_name: string }` (optional, once)
  - `{ attachment: { id, file_name, file_type, file_size, created_at } }` (optional, image-generation path)
  - `{ event: "rag_fallback" }` (optional, when RAG retrieval is not relevant)
  - `{ done: true }` (final event)
- Status: 200 OK
- Auth: Required
- Transport: SSE streaming

### GET /api/chat/history
Get all messages for user (legacy).
- Response: `[{ id: string, role: string, content: string, created_at: string }, ...]`
- Status: 200 OK
- Auth: Required

### POST /api/chat/upload
Upload file attachment.
- Request: Multipart form-data with `files` field (array of files)
- Response: `{ attachments: [{ id, file_name, file_type, attachment_type, file_size, created_at }] }`
- Status: 200 OK
- Auth: Required
- Constraints: Max 20MB per file, supported types only

### POST /api/chat/upload-pdf
Upload and index a PDF for thread-scoped RAG.
- Request: Multipart form-data with `thread_id` and single `file`
- Response: `{ attachment: { id, file_name, file_type, attachment_type, file_size, created_at }, chunks_indexed: number, status: "ready" }`
- Status: 200 OK
- Auth: Required
- Constraints: PDF only, max size from MAX_UPLOAD_MB

### GET /api/chat/attachments/{attachment_id}
Download attachment.
- Response: File binary data with appropriate Content-Type
- Status: 200 OK
- Auth: Required

### GET /api/chat/images/{attachment_id}
View image attachment with image/* media type.
- Response: File binary data for image rendering/preview
- Status: 200 OK
- Auth: Required

## Research Endpoints

### POST /api/research/digest
Stream a structured research digest.
- Request: `{ topic: string, max_papers?: number, use_mcp?: boolean }`
- Response: Server-Sent Events (text/event-stream)
  - `event: status` with `{ message, step }`
  - `event: papers_found` with `{ count, message, step }`
  - `event: selected_papers` with `{ papers, message, step }`
  - `event: digest_chunk` with `{ token }`
  - `event: done` with `{ topic, papers_found, digest, key_papers, generated_at, step }`
  - `event: error` with `{ message }`
- Status: 200 OK
- Auth: Required
- Notes:
  - `use_mcp=true` (default): use MCP arXiv tool path first.
  - If MCP fails or returns no usable papers, backend retries using direct arXiv search.
  - `use_mcp=false`: force direct arXiv search path.

## Error Response Format

All endpoints return consistent error format:
```json
{
  "detail": {
    "error": "error_code",
    "message": "Human-readable error message"
  }
}
```

Common error codes:
- unauthorized: Missing or invalid token
- forbidden: User lacks permission
- not_found: Resource not found
- conflict: Resource already exists
- validation_error: Invalid input
- db_error: Database unavailable
- llm_error: LLM provider error
- file_type_not_supported: Upload file type not allowed
- file_too_large: Upload exceeds size limit
