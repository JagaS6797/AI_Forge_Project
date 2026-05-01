from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser, get_current_user
from app.db.session import get_db_session
from app.schemas.chat import ChatMessageOut, ChatRequest
from app.services.chat_service import list_chat_messages, stream_chat_events

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("")
async def chat_endpoint(
    payload: ChatRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> StreamingResponse:
    return StreamingResponse(
        stream_chat_events(
            db=db,
            message=payload.message,
            thread_id=payload.thread_id,
            user_email=current_user.email,
        ),
        media_type="text/event-stream",
    )


@router.get("/history", response_model=list[ChatMessageOut])
async def chat_history_endpoint(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[ChatMessageOut]:
    """Backward-compat: returns all messages for the user (no thread filter)."""
    messages = await list_chat_messages(db=db, user_email=current_user.email)
    return [
        ChatMessageOut(
            id=item.id,
            role=item.role,
            content=item.content,
            created_at=item.created_at,
        )
        for item in messages
    ]
