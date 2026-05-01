from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat_thread import ChatThread
from app.models.user import User
from app.services.user_service import get_or_create_user_id

logger = logging.getLogger(__name__)


def _auto_name(message: str) -> str:
    """Generate a short thread name from the first user message."""
    text = message.strip()
    if len(text) <= 50:
        return text or "New Chat"
    truncated = text[:50]
    last_space = truncated.rfind(" ")
    if last_space > 20:
        return truncated[:last_space] + "…"
    return truncated + "…"


async def _get_user_id(db: AsyncSession, user_email: str) -> str | None:
    user = await db.scalar(select(User).where(User.email == user_email.lower().strip()))
    return user.id if user else None


async def create_thread(*, db: AsyncSession, user_email: str, name: str = "New Chat") -> ChatThread:
    user_id = await get_or_create_user_id(db, user_email)

    thread = ChatThread(user_id=user_id, name=name)
    db.add(thread)
    await db.commit()
    await db.refresh(thread)
    return thread


async def list_threads(*, db: AsyncSession, user_email: str) -> list[ChatThread]:
    try:
        user_id = await _get_user_id(db, user_email)
        if not user_id:
            return []
        result = await db.scalars(
            select(ChatThread)
            .where(ChatThread.user_id == user_id)
            .order_by(ChatThread.updated_at.desc())
        )
        return list(result.all())
    except Exception:
        logger.exception("Failed to list threads.")
        return []


async def get_thread(*, db: AsyncSession, thread_id: str, user_email: str) -> ChatThread | None:
    user_id = await _get_user_id(db, user_email)
    if not user_id:
        return None
    return await db.scalar(
        select(ChatThread).where(ChatThread.id == thread_id, ChatThread.user_id == user_id)
    )


async def rename_thread(*, db: AsyncSession, thread_id: str, user_email: str, name: str) -> ChatThread | None:
    thread = await get_thread(db=db, thread_id=thread_id, user_email=user_email)
    if not thread:
        return None
    thread.name = name.strip()
    await db.commit()
    await db.refresh(thread)
    return thread


async def delete_thread(*, db: AsyncSession, thread_id: str, user_email: str) -> bool:
    thread = await get_thread(db=db, thread_id=thread_id, user_email=user_email)
    if not thread:
        return False
    await db.delete(thread)
    await db.commit()
    return True


async def maybe_set_thread_name(*, db: AsyncSession, thread_id: str, first_message: str) -> str | None:
    """If the thread still has the default name 'New Chat', replace it with an auto-generated name."""
    try:
        thread = await db.scalar(select(ChatThread).where(ChatThread.id == thread_id))
        if thread and thread.name == "New Chat":
            new_name = _auto_name(first_message)
            thread.name = new_name
            await db.commit()
            return new_name
        return None
    except Exception:
        logger.exception("Failed to auto-name thread.")
        return None
