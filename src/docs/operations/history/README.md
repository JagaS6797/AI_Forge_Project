# Operations History Notes

## Scope

Historical implementation notes captured during rapid development. These are retained for context and audit trail, while canonical behavior docs live in feature/operations references.

## Files

- attachment-fixes-applied.md
- image-viewing-fix-notes.md
- attachment-implementation-summary.md

## Recent Additions (Today)

- Research digest migrated to LangGraph-orchestrated search/select flow while preserving SSE contract.
- arXiv MCP runtime configuration extracted into dedicated backend module (app/ai/mcp_config.py).
- MCP payload parsing hardened for non-ideal tool output (empty/wrapped/multi-part text).
- App shell UI refinements:
	- module rail widened
	- AF badge renamed to Modules
	- logout moved to top-right header with user initials avatar
	- chat submodule background differentiated from main area
	- module page backgrounds normalized for consistency

## Canonical Documents

Use these for current truth:

- src/docs/backend/attachments.md
- src/docs/operations/api-endpoints-reference.md
- src/docs/operations/attachment-fixes-history.md
