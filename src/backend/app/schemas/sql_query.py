from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SqlQueryRequest(BaseModel):
    question: str = Field(min_length=1)
    max_rows: int = Field(default=50, ge=1, le=200)


class SqlQueryResponse(BaseModel):
    question: str
    generated_sql: str
    rows: list[dict[str, Any]]
    row_count: int
    columns: list[str]
    generated_at: datetime
