from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class AttachmentMetadata(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    file_name: str
    file_type: str
    attachment_type: str | None = None
    file_size: int
    created_at: datetime


class FileUploadResponse(BaseModel):
    attachments: list[AttachmentMetadata]


class ChatMessageOut(BaseModel):
    id: str
    role: str
    content: str
    attachment_ids: list[str] = Field(default_factory=list)
    created_at: datetime
