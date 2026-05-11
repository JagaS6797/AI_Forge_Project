from __future__ import annotations

import os
from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class FileAttachment(Base):
    __tablename__ = "file_attachments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    message_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("chat_messages.id", ondelete="CASCADE"), nullable=True, index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    file_name: Mapped[str] = mapped_column(String(255))
    file_type: Mapped[str] = mapped_column(String(100))
    attachment_type: Mapped[str] = mapped_column(String(32), default="file", index=True)
    file_size: Mapped[int] = mapped_column(Integer())
    file_path: Mapped[str] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
