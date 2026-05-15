from __future__ import annotations

import os

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.core.config import settings
from app.core.dependencies import CurrentUser, get_current_user
from app.schemas.dataframe_query import DataFrameQueryRequest, DataFrameQueryResponse
from app.services.dataframe_query_service import run_dataframe_query

router = APIRouter(prefix="/api/dataframe", tags=["dataframe"])


@router.post("/query", response_model=DataFrameQueryResponse)
async def query_dataframe_with_natural_language(
    payload: DataFrameQueryRequest,
    _current_user: CurrentUser = Depends(get_current_user),
) -> DataFrameQueryResponse:
    """Query Google Sheets or CSV data using natural language via a Pandas agent."""
    return await run_dataframe_query(
        question=payload.question,
        use_google_sheets=payload.use_google_sheets,
        csv_file_id=payload.csv_file_id,
    )


@router.post("/upload-csv", response_model=dict)
async def upload_csv_file(
    file: UploadFile = File(...),
    _current_user: CurrentUser = Depends(get_current_user),
) -> dict:
    """Upload a CSV file for querying."""
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No filename provided")

    allowed_extensions = {".csv", ".xlsx", ".xls"}
    _, ext = os.path.splitext(file.filename.lower())
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(allowed_extensions)}",
        )

    try:
        os.makedirs(settings.csv_upload_dir, exist_ok=True)
        file_id = file.filename
        file_path = os.path.join(settings.csv_upload_dir, file_id)
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        return {"file_id": file_id, "file_name": file.filename, "size": len(content)}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": f"CSV upload failed: {exc}"},
        ) from exc
