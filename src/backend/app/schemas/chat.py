from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ChatHistoryItem(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    message: str = Field(default="", min_length=0)
    thread_id: str
    attachment_ids: list[str] = Field(default_factory=list)
    rag_enabled: bool = False


class ChatMessageOut(BaseModel):
    id: str
    role: Literal["user", "assistant"]
    content: str
    attachment_ids: list[str] = Field(default_factory=list)
    created_at: datetime


class AttachmentInfo(BaseModel):
    id: str
    file_name: str
    file_type: str
    attachment_type: str | None = None
    file_size: int
    created_at: datetime


class ChatMessageWithAttachmentsOut(BaseModel):
    id: str
    role: Literal["user", "assistant"]
    content: str
    attachment_ids: list[str] = Field(default_factory=list)
    attachments: list[AttachmentInfo] = Field(default_factory=list)
    created_at: datetime
