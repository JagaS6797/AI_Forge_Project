from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.core.dependencies import CurrentUser, get_current_user
from app.schemas.research_digest import ResearchDigestRequest
from app.services.research_digest_service import stream_research_digest

router = APIRouter(prefix="/api/research", tags=["research"])


@router.post("/digest")
async def research_digest_endpoint(
    payload: ResearchDigestRequest,
    _current_user: CurrentUser = Depends(get_current_user),
) -> StreamingResponse:
    """Stream a structured research digest for a given topic via SSE."""
    return StreamingResponse(
        stream_research_digest(
            topic=payload.topic,
            max_papers=payload.max_papers,
            use_mcp=payload.use_mcp,
        ),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
