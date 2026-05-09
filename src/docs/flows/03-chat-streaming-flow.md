# Flow 03: Chat Streaming and Last-5 Memory

## Scope

Detailed message lifecycle from user input to streamed assistant output with memory windowing.

## Actors

- ChatWindow
- frontend sendMessage stream parser
- /api/chat endpoint
- chat_service
- LangChain chain and LLM endpoint
- chat_messages persistence

## Step-by-Step Flow (As Implemented)

1. User types a message in InputBar and submits.
2. ChatWindow appends local user message + empty assistant placeholder.
3. Frontend POSTs message and thread_id to /api/chat.
4. Backend loads existing messages for user and thread.
5. Backend converts history to ChatHistoryItem list.
6. Backend slices history to latest N user conversations using chat_memory_conversations (default 5).
7. Backend auto-names thread when first message condition is met.
8. Backend persists user message (best effort).
9. Backend calls chain.astream with:
   - message: current user text
   - history: formatted sliced history
10. Backend emits SSE token events continuously.
11. Frontend appends each token to assistant placeholder content.
12. Backend persists final assistant message (best effort).
13. Backend emits done event.
14. Frontend stream parser exits and UI remains with full response.

## Memory Window Clarification

- The algorithm counts user-role entries from newest to oldest.
- When the Nth user turn is reached, history is sliced from that index onward.
- This preserves interleaved assistant messages paired with the selected user turns.

## Failure Paths

- LLM provider errors -> 502 llm_error.
- Unexpected backend exception -> 500 unexpected.
- Persistence failures are logged but stream can continue.

## Enhancement Hooks

- Replace turn-count memory with token-budget memory.
- Add summarization for older turns outside active window.
- Add citation/grounding data in SSE events.
- Add server-side stream heartbeat events for long responses.
