from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class DataFrameQueryRequest(BaseModel):
    question: str = Field(min_length=1)
    use_google_sheets: bool = True  # True for Google Sheets, False for CSV upload
    csv_file_id: str | None = None  # File ID when use_google_sheets=False


class DataFrameQueryResponse(BaseModel):
    question: str
    answer: str
    data_summary: str
    source: str  # "google_sheets" or "csv"
    row_count: int
    column_names: list[str]
    generated_at: datetime
