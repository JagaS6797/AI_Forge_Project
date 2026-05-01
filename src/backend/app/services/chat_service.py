from __future__ import annotations

import json
import logging
from typing import AsyncIterator

from fastapi import HTTPException
from openai import OpenAIError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.chains.chat_chain import build_chat_chain
from app.core.config import settings
from app.models.chat_message import ChatMessage
from app.models.user import User
from app.schemas.chat import ChatHistoryItem
from app.services.user_service import get_or_create_user_id


logger = logging.getLogger(__name__)


def _format_history(history: list[ChatHistoryItem]) -> str:
    if not history:
        return "(none)"

    return "\n".join(f"{item.role}: {item.content}" for item in history)


def _recent_conversations(
    history: list[ChatHistoryItem],
    *,
    max_conversations: int,
) -> list[ChatHistoryItem]:
    if max_conversations <= 0 or not history:
        return []

    user_count = 0
    start_index = len(history)

    for index in range(len(history) - 1, -1, -1):
        if history[index].role == "user":
            user_count += 1
            if user_count == max_conversations:
                start_index = index
                break

    if user_count < max_conversations:
        return history

    return history[start_index:]


async def save_chat_message(
    *,
    db: AsyncSession,
    user_email: str,
    role: str,
    content: str,
    thread_id: str | None = None,
) -> ChatMessage:
    user_id = await get_or_create_user_id(db, user_email)
    message = ChatMessage(user_id=user_id, role=role, content=content, thread_id=thread_id)
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message


async def list_chat_messages(
    *, db: AsyncSession, user_email: str, thread_id: str | None = None
) -> list[ChatMessage]:
    try:
        user = await db.scalar(select(User).where(User.email == user_email.lower().strip()))
    except Exception:
        logger.exception("Failed to load chat history from database.")
        return []

    if not user:
        return []

    try:
        query = (
            select(ChatMessage)
            .where(ChatMessage.user_id == user.id)
            .order_by(ChatMessage.created_at.asc())
        )
        if thread_id is not None:
            query = query.where(ChatMessage.thread_id == thread_id)
        result = await db.scalars(query)
        return list(result.all())
    except Exception:
        logger.exception("Failed to query chat messages.")
        return []


async def stream_chat_events(
    *,
    db: AsyncSession,
    message: str,
    thread_id: str,
    user_email: str,
) -> AsyncIterator[str]:
    from app.services.thread_service import maybe_set_thread_name

    chain = build_chat_chain()
    assistant_chunks: list[str] = []

    try:
        # 1. Load existing history for this thread (before this new message)
        existing = await list_chat_messages(db=db, user_email=user_email, thread_id=thread_id)
        history_items = [ChatHistoryItem(role=m.role, content=m.content) for m in existing]
        memory_items = _recent_conversations(
            history_items,
            max_conversations=settings.chat_memory_conversations,
        )

        # 2. Auto-name thread on first message
        if not existing:
            new_name = await maybe_set_thread_name(db=db, thread_id=thread_id, first_message=message)
            if new_name:
                yield f"data: {json.dumps({'thread_name': new_name})}\n\n"

        # 3. Save user message
        try:
            await save_chat_message(
                db=db, user_email=user_email, role="user", content=message, thread_id=thread_id
            )
        except Exception:
            logger.exception("Failed to persist user message. Continuing chat stream.")

        async for token in chain.astream(
            {
                "message": message,
                "history": _format_history(memory_items),
            },
            config={
                "metadata": {
                    "user_email": user_email,
                }
            },
        ):
            if token:
                assistant_chunks.append(token)
                yield f"data: {json.dumps({'token': token})}\n\n"

        assistant_content = "".join(assistant_chunks).strip()
        if assistant_content:
            try:
                await save_chat_message(
                    db=db,
                    user_email=user_email,
                    role="assistant",
                    content=assistant_content,
                    thread_id=thread_id,
                )
            except Exception:
                logger.exception("Failed to persist assistant message. Continuing chat stream.")


        yield "data: {\"done\": true}\n\n"
    except OpenAIError as exc:
        raise HTTPException(
            status_code=502,
            detail={"error": "llm_error", "message": str(exc)},
        ) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={"error": "unexpected", "message": str(exc)},
        ) from exc
