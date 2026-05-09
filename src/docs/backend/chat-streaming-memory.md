# Chat Streaming and Memory

## Scope

How chat requests are processed, streamed to the UI, and constrained to last N conversations for prompt memory.

## Current Implementation

### Chain Composition

- Prompt includes system instruction plus two dynamic placeholders:
  - history
  - message
- Chain uses ChatOpenAI client from central ai/llm.py.
- Output parser emits plain string tokens.

### Streaming Contract

- Endpoint returns text/event-stream.
- Events contain JSON payload in data lines.
- Supported payload keys:
  - token: partial assistant output token
  - thread_name: auto-generated thread title
  - done: end-of-stream marker

### Memory Behavior

- chat_memory_conversations defaults to 5.
- Existing thread messages are loaded before saving current user message.
- Memory selection scans backward by user turns and slices history from the Nth most-recent user message.
- Selected history is formatted as lines: role: content.

## Step-by-Step Flow

1. Receive chat request with message + thread_id.
2. Fetch existing messages for user and thread.
3. Build in-memory history items.
4. Slice to configured conversation window.
5. Auto-name thread if this is first thread message.
6. Persist current user message (best effort).
7. Stream LLM tokens as SSE token events.
8. Persist final assistant text (best effort).
9. Emit done event.

## Error Handling

- Upstream LLM errors become HTTP 502 with llm_error type.
- Unexpected exceptions become HTTP 500 with unexpected type.
- Persistence failures log exceptions and do not stop stream.

## Enhancement Hooks

- Add message-level metadata and tool traces in SSE payload.
- Add model fallback chain for upstream provider outages.
- Add adaptive memory policy (token budget based instead of fixed turns).
- Add optional RAG context injection before chain invocation.
