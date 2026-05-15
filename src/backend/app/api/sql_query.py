from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.dependencies import CurrentUser, get_current_user
from app.schemas.sql_query import SqlQueryRequest, SqlQueryResponse
from app.services.sql_query_service import run_nl_to_sql_query

router = APIRouter(prefix="/api/sql", tags=["sql"])


@router.post("/query", response_model=SqlQueryResponse)
async def query_database_with_natural_language(
    payload: SqlQueryRequest,
    _current_user: CurrentUser = Depends(get_current_user),
) -> SqlQueryResponse:
    return await run_nl_to_sql_query(payload.question, payload.max_rows)
