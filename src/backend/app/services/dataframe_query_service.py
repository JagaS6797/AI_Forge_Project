from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

import gspread
import pandas as pd
from fastapi import HTTPException, status
from langchain_experimental.agents import create_pandas_dataframe_agent

from app.ai.llm import chat_llm
from app.core.config import settings
from app.schemas.dataframe_query import DataFrameQueryResponse

logger = logging.getLogger(__name__)


async def _load_google_sheet_data(sheet_id: str) -> pd.DataFrame:
    """Load data from Google Sheet into a Pandas DataFrame."""
    if not settings.google_service_account_json:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"message": "Google Sheets not configured (GOOGLE_SERVICE_ACCOUNT_JSON missing)"},
        )

    try:
        import os
        raw = settings.google_service_account_json.strip()
        if raw.startswith("{"):
            creds_dict = json.loads(raw)
        else:
            # File path fallback — read the JSON file
            candidates = [
                raw,
                os.path.join(os.getcwd(), raw),
                os.path.join(os.getcwd(), os.path.basename(raw)),
            ]
            file_path = next((p for p in candidates if os.path.isfile(p)), None)
            if not file_path:
                raise FileNotFoundError(f"Service account file not found. Tried: {candidates}")
            with open(file_path) as f:
                creds_dict = json.load(f)

        # gspread >= 6.x: use service_account_from_dict (authorize() removed)
        gc = gspread.service_account_from_dict(creds_dict)

        try:
            spreadsheet = gc.open_by_key(sheet_id)
            worksheet = spreadsheet.get_worksheet(0)
            records = worksheet.get_all_records()
        except gspread.exceptions.SpreadsheetNotFound:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": f"Spreadsheet not found (ID: {sheet_id}). Share the sheet with: {creds_dict.get('client_email', 'service account')}"},
            )
        except gspread.exceptions.APIError as api_exc:
            err_str = str(api_exc)
            if "403" in err_str:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={"message": f"Access denied. Share the Google Sheet with: {creds_dict.get('client_email', 'service account email')}"},
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"message": f"Google Sheets API error: {api_exc}"},
            )

        if not records:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"message": "The Google Sheet is empty or has no data."},
            )

        df = pd.DataFrame(records)
        return df

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(f"Failed to load Google Sheet {sheet_id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": f"Failed to load Google Sheet: {exc}"},
        )


async def _load_csv_data(csv_path: str) -> pd.DataFrame:
    """Load data from CSV or XLSX file into a Pandas DataFrame."""
    try:
        if csv_path.lower().endswith((".xlsx", ".xls")):
            df = pd.read_excel(csv_path)
        else:
            df = pd.read_csv(csv_path)
        return df
    except Exception as exc:
        logger.exception(f"Failed to load file {csv_path}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": f"Failed to load CSV: {exc}"},
        )


async def run_dataframe_query(
    question: str,
    use_google_sheets: bool = True,
    csv_file_id: str | None = None,
) -> DataFrameQueryResponse:
    """Run a natural-language question against a Pandas DataFrame using LangChain agent."""
    
    # Load appropriate data source
    if use_google_sheets:
        if not settings.google_sheets_spreadsheet_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Google Sheets spreadsheet ID not configured"},
            )
        df = await _load_google_sheet_data(settings.google_sheets_spreadsheet_id)
        source = "google_sheets"
    else:
        if not csv_file_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "CSV file ID required when use_google_sheets=False"},
            )
        csv_path = f"{settings.csv_upload_dir}/{csv_file_id}"
        df = await _load_csv_data(csv_path)
        source = "csv"

    # Create pandas dataframe agent
    try:
        agent = create_pandas_dataframe_agent(
            llm=chat_llm,
            df=df,
            verbose=True,
            agent_type="tool-calling",
            max_iterations=settings.dataframe_agent_max_iterations,
            handle_parsing_errors=True,
            allow_dangerous_code=True,
        )

        # Run agent with user question
        result = agent.invoke({"input": question})
        answer = str(result.get("output", "No answer generated"))

        # Build response
        return DataFrameQueryResponse(
            question=question,
            answer=answer,
            data_summary=f"Loaded {len(df)} rows × {len(df.columns)} columns",
            source=source,
            row_count=len(df),
            column_names=list(df.columns),
            generated_at=datetime.now(timezone.utc),
        )

    except Exception as exc:
        logger.exception(f"DataFrame agent failed for question '{question}': {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": f"Agent failed: {exc}"},
        )
