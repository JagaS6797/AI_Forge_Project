# Attachment Fixes History

## Scope

Historical summary of major attachment-related fixes that were applied during implementation hardening.

## Why This Exists

Several ad-hoc implementation notes were created during rapid development. This file preserves the important decisions and outcomes in one stable location under docs/.

Source historical notes are retained in:
- src/docs/operations/history/attachment-fixes-applied.md
- src/docs/operations/history/image-viewing-fix-notes.md
- src/docs/operations/history/attachment-implementation-summary.md

## Key Fixes Applied

### 1. Chat Request Validation (422 fix)

- Problem: chat endpoint rejected attachment-only requests.
- Change: chat request schema and stream validation now allow empty message when attachment_ids are present.
- Outcome: users can send attachment-only requests without 422 errors.

### 2. Attachment Download Robustness (500 fix)

- Problem: download endpoint could return 500 on user-id lookup or missing path edge cases.
- Change: added clearer validation and explicit error paths for missing ownership/path/content.
- Outcome: better 401/403/404 handling and safer failure behavior.

### 3. UI Upload UX Shift to Plus-Menu Pattern

- Problem: upload UX was modal-heavy and inconsistent with current compose pattern.
- Change: InputBar moved to mode-based + button flow with immediate file picking and chip previews.
- Outcome: faster upload flow and lower friction for mixed message + attachment interactions.

### 4. message_id Association Integrity

- Problem: file attachments could remain unlinked (message_id null) after message send.
- Change: message persistence path now links attachment rows to the newly created message.
- Outcome: message history and attachment rendering remain consistent after refresh.

### 5. Attachment Metadata in Thread History

- Problem: thread message payloads did not include rich attachment metadata.
- Change: thread messages endpoint now returns attachments payload per message.
- Outcome: frontend can render attachment chips/previews without extra lookup roundtrips.

### 6. Image Rendering and Access Flow

- Problem: image previews failed without authenticated fetch path.
- Change: frontend uses authorized fetch + blob URL for image previews; backend includes image view endpoint.
- Outcome: secure previews and download behavior for owned image attachments.

## Current Canonical Docs

- Feature specification: src/docs/backend/attachments.md
- Status snapshot: src/docs/backend/ATTACHMENTS_COMPLETE.md
- API contracts: src/docs/operations/api-endpoints-reference.md

## Notes

- Treat this file as historical context and rationale.
- Keep implementation behavior updates in canonical feature/API docs above.
