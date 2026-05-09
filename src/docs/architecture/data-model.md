# Data Model

## Scope

Database entities currently used by authentication, threads, and chat history.

## Current Tables

### users

- id: string UUID-like (primary key)
- email: unique string, indexed
- created_at: timestamp with timezone

### auth_credentials

- id: string UUID-like (primary key)
- email: unique string, indexed
- password_hash: string
- created_at: timestamp with timezone

### chat_threads

- id: string UUID-like (primary key)
- user_id: FK -> users.id, indexed, cascade delete
- name: string (default New Chat)
- created_at: timestamp with timezone
- updated_at: timestamp with timezone

### chat_messages

- id: string UUID-like (primary key)
- user_id: FK -> users.id, indexed, cascade delete
- thread_id: FK -> chat_threads.id, indexed, nullable, cascade delete
- role: user or assistant in current usage
- content: text
- created_at: timestamp with timezone

## Relationship Summary

- One user has many threads.
- One thread has many chat messages.
- One user has many chat messages.
- Auth credentials are stored separately from user profile rows.

## Data Lifecycle

1. User authenticates.
2. User row is ensured/created.
3. Thread may be created.
4. User and assistant messages are stored against thread.
5. Deleting a thread cascades message deletes via FK.

## Enhancement Hooks

- Add explicit role enum constraint for chat_messages.role.
- Add soft-delete columns if audit requirements appear.
- Add message metadata JSON column for citations/tools in future.
- Add indexes on (thread_id, created_at) for large history retrieval efficiency.
