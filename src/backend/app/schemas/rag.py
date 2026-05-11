from __future__ import annotations

from pydantic import BaseModel

from app.schemas.attachment import AttachmentMetadata


class PdfUploadResponse(BaseModel):
    attachment: AttachmentMetadata
    chunks_indexed: int
    status: str
