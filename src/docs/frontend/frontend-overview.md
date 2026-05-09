# Frontend Overview

## Scope

React frontend architecture, screen states, and core component responsibilities.

## Current Implementation

### Root Composition

- App renders ChatPage.
- ChatPage handles auth and chat screens.

### Screen States

- login
- register
- chat

### Main UI Components

- ThreadSidebar: thread navigation and thread actions.
- ChatWindow: per-thread message history and streaming response rendering.
- MessageList: message display (already integrated).
- InputBar: message compose + send behavior.

### State Domains in ChatPage

- Auth state: token/user/screen.
- Thread state: list + active thread.
- Form state: credentials and validation messages.
- Runtime state: loading/submitting flags.

## Step-by-Step Interaction Flow

1. Bootstrap checks local token.
2. If token valid, fetch current user and thread list.
3. User selects or creates thread.
4. ChatWindow loads thread history.
5. User sends message; stream updates assistant content progressively.
6. Optional thread_name event updates sidebar title.

## Error UX

- Inline text for login/register failures.
- Chat stream errors shown above input area.
- Noncritical thread operation errors are currently ignored in UI handlers.

## Enhancement Hooks

- Introduce global toast system for ignored thread operation failures.
- Split ChatPage into route-level screens for maintainability.
- Add reusable auth form components to reduce duplication.
- Add offline/network-state indicator.
