# Flow 04: PDF RAG Ingestion and Query

## Scope

End-to-end sequence for uploading a PDF to a thread, indexing chunks, and answering a question with RAG.

## Actors

- InputBar (Upload PDF mode)
- ChatWindow and useAttachments hook
- POST /api/chat/upload-pdf
- rag_service and chat_service
- Chroma vector store

## Step-by-Step Flow (As Implemented)

1. User selects Upload PDF (RAG) mode in InputBar.
2. Frontend file picker restricts to a single PDF file.
3. Frontend calls POST /api/chat/upload-pdf with thread_id and file.
4. Backend validates MIME and size and verifies thread ownership.
5. Backend stores PDF as attachment and extracts text.
6. Extracted text is split and indexed into user-scoped Chroma collection.
7. Backend creates rag_documents row with chunks_count and collection name.
8. Frontend receives status=ready and enables RAG toggle for the thread.
9. User submits a question with rag_enabled=true.
10. Chat service retrieves top-k chunks filtered by thread_id.
11. If relevance threshold is met, RAG chain response is streamed.
12. If not met, backend emits event=rag_fallback and continues standard chat.
13. Stream completes with done=true.

## Failure Paths

- Non-PDF file or oversize input -> 400 pdf_upload_failed.
- Missing/unauthorized thread -> 400 validation failure.
- Empty PDF text extraction -> 400 validation failure.
- Chroma/storage failure -> 500 pdf_upload_failed.
- Query without relevant chunks -> rag_fallback event then normal model response.

## Error Handling

- Upload API returns structured error payloads for validation and server failures.
- Query path never hard-fails on low relevance; it degrades to normal chat.
- Stream always terminates with done=true on handled error paths.

## Enhancement Hooks

- Add inline citation blocks with source chunk IDs.
- Add asynchronous ingestion queue and progress API.
- Add multi-document ranking strategy per thread.
