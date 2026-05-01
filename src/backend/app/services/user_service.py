from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


async def get_or_create_user_id(db: AsyncSession, user_email: str) -> str:
    """Resolve a user row by email, creating one if it doesn't exist. Returns the user id."""
    normalized = user_email.lower().strip()
    user = await db.scalar(select(User).where(User.email == normalized))
    if user:
        return user.id

    user = User(email=normalized)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user.id
