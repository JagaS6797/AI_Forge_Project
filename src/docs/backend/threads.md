# Thread Management

## Scope

Conversation thread lifecycle: create, list, rename, delete, and message retrieval by thread.

## Current Implementation

### Thread APIs

- GET /api/threads: list user threads ordered by updated_at descending.
- POST /api/threads: create thread with supplied name (default New Chat).
- PATCH /api/threads/{thread_id}: rename thread.
- DELETE /api/threads/{thread_id}: delete thread.
- GET /api/threads/{thread_id}/messages: retrieve messages for that thread.

### Service Responsibilities

- Resolve user ID from user email.
- Ensure thread ownership on read/update/delete.
- Auto-name thread on first chat message if still named New Chat.
- Return safe defaults (empty lists) on read failures.

## Step-by-Step Flow

### New Thread

1. UI calls create thread API.
2. Service resolves or creates user row.
3. Thread row created with name.
4. Thread returned and prepended in sidebar state.

### Rename Thread

1. UI submits new name.
2. Service validates ownership via get_thread.
3. Name trimmed and saved.
4. Updated thread returned to UI.

### Delete Thread

1. UI triggers delete.
2. Service validates ownership.
3. Thread row deleted.
4. UI removes thread and picks next available thread.

### Auto-Name on First Message

1. Chat service checks if thread has zero existing messages.
2. If thread name is New Chat, generate summary name from first message.
3. Persist new thread name and emit thread_name event.
4. UI updates sidebar title in real time.

## Enhancement Hooks

- Add pinned/favorite thread state.
- Add thread archival instead of hard delete.
- Add optimistic concurrency guard for parallel rename actions.
- Add pagination for users with large thread counts.
