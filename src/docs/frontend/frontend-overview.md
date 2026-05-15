# Frontend Overview

## Scope

React frontend architecture, screen states, and core component responsibilities.

## Current Implementation

### Root Composition

- App shell renders authentication entry and multi-module workspace.
- ChatPage is shown only for unauthenticated state.
- Authenticated shell includes:
	- left module rail
	- chat-only submodule panel (thread history)
	- top header with user avatar initials and logout action
	- module content area

### Screen States

- login
- register
- chat
- project8 (NL-SQL)
- project9 (DataFrame)
- project10 (Research Digest)
- project11 (Tic Tac Toe)

### Main UI Components

- ThreadSidebar: thread navigation and thread actions.
- ChatWindow: per-thread message history and streaming response rendering.
- MessageList: message display (already integrated).
- InputBar: message compose + send behavior.
- App module rail labeled Modules.
- Header user chip with initials and top-right logout.
- Chat submodule panel with differentiated background from main canvas.

### State Domains in ChatPage

- Auth state: token/user/screen.
- Thread state: list + active thread.
- Form state: credentials and validation messages.
- Runtime state: loading/submitting flags.

### Current Layout Decisions

- Left module rail width increased for clearer labels and module navigation.
- Module badge text AF replaced with Modules.
- Logout moved from module rail footer into top-right header.
- User avatar initials are shown beside logout action.
- Main module pages share the same background tone for visual consistency.
- Chat submodule panel intentionally uses a distinct background to separate thread navigation from main content.

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
