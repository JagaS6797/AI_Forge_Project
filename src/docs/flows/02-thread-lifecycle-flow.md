# Flow 02: Thread Lifecycle

## Scope

How threads are created, selected, renamed, deleted, and auto-named during first chat.

## Actors

- ThreadSidebar
- ChatPage thread state
- /api/threads endpoints
- thread_service
- chat_service (auto-name integration)

## Step-by-Step Flow (As Implemented)

### A. Load Existing Threads

1. After successful auth, frontend calls GET /api/threads.
2. Backend resolves user by token email.
3. Service fetches threads sorted by updated_at desc.
4. Frontend stores list and selects first thread if present.

### B. Create New Thread

1. User clicks New Chat in sidebar.
2. Frontend calls POST /api/threads with name New Chat.
3. Backend creates thread linked to user.
4. Frontend prepends thread and marks it active.

### C. Rename Thread

1. User opens thread menu and selects Rename.
2. Frontend sends PATCH /api/threads/{id}.
3. Backend validates ownership and updates name.
4. Frontend patches thread entry in local list.

### D. Delete Thread

1. User selects Delete in thread menu.
2. Frontend sends DELETE /api/threads/{id}.
3. Backend validates ownership and deletes.
4. Frontend removes thread and picks next available thread.

### E. Auto-Name on First Message

1. User sends first message in a New Chat thread.
2. chat_service detects empty existing thread history.
3. maybe_set_thread_name generates short title from first message.
4. Backend emits SSE thread_name event.
5. Frontend updates the thread title in sidebar immediately.

## Failure Paths

- Missing thread or unauthorized ownership -> 404 not found.
- Internal DB failure during list -> empty list fallback.

## Enhancement Hooks

- Add thread move/group capability.
- Add batch delete/archive endpoint.
- Add audit metadata for rename/delete operations.
