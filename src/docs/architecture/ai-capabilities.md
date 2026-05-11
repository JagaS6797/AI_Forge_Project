# AI Capabilities Overview

## Scope

Cross-cutting architecture for AI-powered features: normal chat generation, attachment-aware responses, PDF-based retrieval augmentation (RAG), and image generation.

## Current Implementation

### Capability Matrix

- Standard chat: text response streaming through SSE.
- Attachment-aware chat: request-scoped attachment context is injected into model input.
- PDF RAG: per-user Chroma collection retrieval with thread-level filtering.
- Image generation: prompt detection in chat and generated image persistence as attachment.

### Core Modules

- LLM gateway: app/ai/llm.py
- Chat orchestration: app/services/chat_service.py
- RAG ingestion/retrieval: app/services/rag_service.py
- Image generation orchestration: app/services/image_generation_service.py
- Vector store access: app/ai/rag/chroma_client.py
- RAG chain prompt composition: app/ai/chains/rag_chain.py

### Control Signals

- rag_enabled flag in chat request controls whether RAG answer path is attempted.
- SSE payload can include:
  - token
  - thread_name
  - attachment (generated image metadata)
  - event=rag_fallback
  - done=true

## Step-by-Step Flow

1. Frontend sends message to POST /api/chat with thread_id and optional attachment_ids and rag_enabled.
2. Chat service loads thread history and selects memory window.
3. Service checks for image-generation intent first.
4. If image path is selected, service generates image, stores attachment, and streams token + attachment event.
5. If RAG is enabled and thread has indexed PDF documents, service attempts retrieval and RAG answer.
6. If retrieval is not relevant, service emits rag_fallback and continues standard chat path.
7. Standard chat path streams model tokens and persists final assistant message.

## Error Handling

- Upstream OpenAI/LiteLLM errors are converted into user-visible stream messages and done termination.
- HTTP and unexpected errors are emitted as token text events, then stream is closed with done=true.
- Message persistence failures are best-effort and do not stop in-flight stream delivery.

## Enhancement Hooks

- Add tool-calling orchestration layer between capability detection and model invocation.
- Move capability routing into explicit policy engine for easier testing.
- Add typed SSE event schema versioning shared by backend and frontend.
