# PDF RAG Retrieval

## Scope

PDF upload, indexing, and retrieval-augmented answering for a specific thread.

## Current Implementation

- Endpoint(s):
  - POST /api/chat/upload-pdf
  - POST /api/chat (with rag_enabled=true)
- Service(s):
  - app/services/rag_service.py
  - app/services/chat_service.py (RAG routing + fallback)
- Schema(s):
  - app/schemas/rag.py
  - app/schemas/chat.py (rag_enabled)
- Model(s):
  - app/models/rag_document.py
  - app/models/file_attachment.py
- Frontend component(s):
  - components/attachments/PdfUploadButton.tsx
  - components/attachments/PdfAttachmentPreview.tsx
  - components/chat/InputBar.tsx
  - components/chat/ChatWindow.tsx
- Frontend API binding(s):
  - uploadPdf()
  - sendMessage(..., ragEnabled=true)

### Storage and Retrieval Shape

- PDF file bytes are stored as a normal attachment.
- Extracted text is split into chunks (default chunk_size=1000, overlap=200).
- Chunks are indexed in Chroma under collection user_<user_id>.
- rag_documents table tracks thread_id, attachment_id, and chunks_count.
- Query path retrieves top-k chunks with thread_id filter and relevance threshold.

## Step-by-Step Flow

1. User selects Upload PDF (RAG) mode and uploads one PDF.
2. Frontend calls POST /api/chat/upload-pdf with multipart (thread_id, file).
3. Backend validates file type/size and thread ownership.
4. PDF is saved to disk and attachment row is created.
5. Backend loads text, splits chunks, stores embeddings in Chroma, inserts rag_document row.
6. Frontend marks PDF as ready and enables RAG toggle for the thread.
7. User asks a question with rag_enabled=true.
8. Chat service runs similarity_search_with_score filtered by thread_id.
9. If relevance threshold is met, RAG chain answers from context and response is streamed.
10. If threshold is not met, backend emits event=rag_fallback and continues normal chat behavior.

## API Contract

### Upload

- Request: multipart form-data with thread_id and file
- Response: { attachment, chunks_indexed, status }

### Ask with RAG

- Request: { message, thread_id, attachment_ids, rag_enabled }
- Stream events:
  - { token }
  - { event: "rag_fallback" } optional
  - { done: true }

## State and Data Impact

- Created tables/rows:
  - file_attachments row for uploaded PDF
  - rag_documents row per indexed PDF
  - Chroma vectors for each chunk
- Frontend state updates:
  - hasRagDocument and ragEnabled flags in ChatWindow
  - PDF status transitions: uploading -> processing -> ready

## Error Handling

- Invalid file type or oversized PDF: 400 with pdf_upload_failed.
- Thread access denied/not found: 400 from validation path.
- Empty/unreadable PDF text: 400 validation failure.
- Indexing or storage exception: 500 with pdf_upload_failed.
- Retrieval misses threshold: rag_fallback event and standard chat fallback.

## Security and Compliance Notes

- Upload and query endpoints require authenticated user.
- Thread ownership is verified before PDF indexing.
- Retrieval is user-scoped and thread-filtered.
- Raw file paths are not exposed in API responses.

## Enhancement Hooks

- Add async job queue for heavy PDF ingestion and progress polling.
- Add source citation spans in RAG responses (chunk IDs + page ranges).
- Add per-thread TTL and cleanup for stale vector indexes.
