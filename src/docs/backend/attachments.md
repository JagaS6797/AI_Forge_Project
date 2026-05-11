# File Attachments

## Scope

Upload, persist, associate, render, and download user-owned chat attachments (images, videos, text/code, PDFs, spreadsheets, and documents).

## Current Implementation

### Endpoints

- POST /api/chat/upload
- GET /api/chat/attachments/{attachment_id}
- GET /api/chat/images/{attachment_id}
- POST /api/chat (accepts attachment_ids)
- GET /api/threads/{thread_id}/messages (returns attachment metadata per message)

### Backend Modules

- API: app/api/chat.py, app/api/threads.py
- Services: app/services/attachment_service.py, app/services/chat_service.py
- Models: app/models/file_attachment.py, app/models/chat_message.py
- Schemas: app/schemas/attachment.py, app/schemas/chat.py

### Frontend Modules

- Upload/state: src/frontend/src/hooks/useAttachments.ts
- Input and mode handling: src/frontend/src/components/chat/InputBar.tsx
- Message rendering: src/frontend/src/components/chat/MessageList.tsx, src/frontend/src/components/chat/MessageAttachments.tsx
- API client: src/frontend/src/lib/api.ts

### Data Model

- file_attachments:
  - id
  - message_id (nullable FK to chat_messages.id)
  - user_id (FK to users.id)
  - file_name
  - file_type
  - attachment_type (file | image | pdf)
  - file_size
  - file_path
  - created_at
- chat_messages:
  - attachment_ids JSON array

### Validation and Security

- MIME allowlist enforcement.
- Dangerous extension blocking in attachment_service (executables/installers/scripts/archives).
- Max file size enforcement via MAX_UPLOAD_MB.
- Download/view authorization by owner check.
- File path remains backend-only and is never exposed directly.

## Step-by-Step Flow

1. User selects files in UI.
2. Frontend uploads files to POST /api/chat/upload (multipart form-data).
3. Backend validates extension, MIME type, and file size.
4. Backend stores file bytes on disk and inserts file_attachments rows.
5. Frontend stores returned attachment metadata and IDs.
6. User sends chat request with message + attachment_ids.
7. Backend persists chat_messages row and links each attachment message_id to that message.
8. Backend builds attachment context for model input:
   - text/code: decoded content (truncated)
   - spreadsheets: parsed sample content
   - image/video/pdf/binary: metadata-first context
9. Assistant response streams over SSE and final assistant message is persisted.
10. Message history endpoint returns messages with attachment metadata for rendering.
11. User can download or view owned attachments via dedicated endpoints.

## API Contract

### Upload

- Request: multipart form-data with files[]
- Response:
  - { attachments: [{ id, file_name, file_type, attachment_type, file_size, created_at }] }

### Send Chat with Attachments

- Request:
  - { message, thread_id, attachment_ids, rag_enabled }
- Stream response events include token, optional thread_name, optional attachment, and done.

### Download and Image View

- GET /api/chat/attachments/{attachment_id} returns file payload.
- GET /api/chat/images/{attachment_id} returns image payload for image attachments.

## Error Handling

- Invalid extension/MIME/size -> 400 validation error.
- Unauthorized attachment access -> 403.
- Missing attachment/file -> 404.
- Upload/storage failures -> 500 with structured error detail.
- Attachment processing failures for LLM context are logged and degrade gracefully.

## Enhancement Hooks

- Add cloud object storage (S3/GCS/Azure Blob) via storage abstraction.
- Add malware scanning pipeline before attachment activation.
- Add image/video thumbnail generation and caching.
- Add attachment lifecycle policies (TTL, archival, cleanup jobs).
- Add richer multimodal routing for image/video-native model handling.
