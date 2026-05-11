from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RagDocument(Base):
    __tablename__ = "rag_documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    thread_id: Mapped[str] = mapped_column(String(36), ForeignKey("chat_threads.id", ondelete="CASCADE"), index=True)
    attachment_id: Mapped[str] = mapped_column(String(36), ForeignKey("file_attachments.id", ondelete="CASCADE"), unique=True, index=True)
    file_name: Mapped[str] = mapped_column(String(255))
    collection_name: Mapped[str] = mapped_column(String(120), index=True)
    chunks_count: Mapped[int] = mapped_column(Integer(), default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
