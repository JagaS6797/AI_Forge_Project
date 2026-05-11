from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.db.base import Base


def _to_async_database_url(url: str) -> str:
    if url.startswith("postgresql+asyncpg://"):
        return url
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


engine = create_async_engine(
    _to_async_database_url(settings.database_url),
    pool_pre_ping=True,
)

SessionLocal = async_sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


async def init_db() -> None:
    async with engine.begin() as conn:
        # First create all tables
        await conn.run_sync(Base.metadata.create_all)
        
        # Migrate existing chat_messages table to add attachment_ids column if missing
        from sqlalchemy import text
        try:
            # Try to add the column if it doesn't exist
            await conn.execute(
                text("ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS attachment_ids JSON DEFAULT '[]'::json NOT NULL")
            )
        except Exception:
            # If error, it likely already exists - continue anyway
            pass

        try:
            await conn.execute(
                text("ALTER TABLE file_attachments ADD COLUMN IF NOT EXISTS attachment_type VARCHAR(32) DEFAULT 'file' NOT NULL")
            )
        except Exception:
            pass
