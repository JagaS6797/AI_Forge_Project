from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ThreadOut(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    name: str
    created_at: datetime
    updated_at: datetime


class CreateThreadRequest(BaseModel):
    name: str = Field(default="New Chat", max_length=255)


class RenameThreadRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
