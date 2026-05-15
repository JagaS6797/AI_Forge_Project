from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any

import asyncpg
from fastapi import HTTPException, status
from langchain_core.messages import HumanMessage, SystemMessage

from app.ai.llm import chat_llm
from app.core.config import settings
from app.schemas.sql_query import SqlQueryResponse


_BLOCKED_SQL_KEYWORDS = {
    "insert",
    "update",
    "delete",
    "drop",
    "alter",
    "truncate",
    "create",
    "grant",
    "revoke",
    "comment",
    "copy",
    "execute",
    "call",
}


def _to_asyncpg_database_url(url: str) -> str:
    if url.startswith("postgresql+asyncpg://"):
        return url.replace("postgresql+asyncpg://", "postgresql://", 1)
    return url


def _extract_sql(content: str) -> str:
    text = content.strip()

    # Try JSON format first
    if text.startswith("{"):
        try:
            payload = json.loads(text)
            if isinstance(payload, dict) and isinstance(payload.get("sql"), str):
                return payload["sql"].strip()
        except json.JSONDecodeError:
            pass

    # Try SQL code block format
    code_match = re.search(r"```(?:sql)?\s*(.*?)```", text, flags=re.IGNORECASE | re.DOTALL)
    if code_match:
        return code_match.group(1).strip()

    # Return as-is if it looks like raw SQL (starts with SELECT or WITH)
    if text.lower().startswith("select") or text.lower().startswith("with"):
        return text

    return text


def _assert_safe_select_query(sql: str) -> str:
    normalized = sql.strip().rstrip(";").strip()
    lowered = normalized.lower()

    if not normalized:
        raise ValueError("No SQL query generated")

    starts_valid = lowered.startswith("select") or lowered.startswith("with")
    if not starts_valid:
        raise ValueError("Only SELECT queries are allowed")

    if ";" in normalized:
        raise ValueError("Multiple SQL statements are not allowed")

    for keyword in _BLOCKED_SQL_KEYWORDS:
        if re.search(rf"\b{keyword}\b", lowered):
            raise ValueError(f"Blocked SQL keyword detected: {keyword}")

    return normalized


def _ensure_limit(sql: str, max_rows: int) -> str:
    if re.search(r"\blimit\s+\d+\b", sql, flags=re.IGNORECASE):
        return sql
    return f"{sql}\nLIMIT {max_rows}"


async def _load_schema_description(conn: asyncpg.Connection) -> str:
    schema_name = settings.nl2sql_schema
    tables = await conn.fetch(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = $1 AND table_type = 'BASE TABLE'
        ORDER BY table_name
        LIMIT 40
        """,
        schema_name,
    )

    lines: list[str] = [f"Schema: {schema_name}"]

    for table in tables:
        table_name = table["table_name"]
        cols = await conn.fetch(
            """
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = $1 AND table_name = $2
            ORDER BY ordinal_position
            """,
            schema_name,
            table_name,
        )
        col_parts = [f"{c['column_name']} ({c['data_type']})" for c in cols]
        lines.append(f"- {table_name}: {', '.join(col_parts)}")

    return "\n".join(lines)


async def _generate_sql(question: str, schema_description: str, max_rows: int) -> str:
    system_prompt = (
        "You are a PostgreSQL query generator. Your ONLY task is to generate a valid SELECT query.\n"
        "Rules:\n"
        "- ALWAYS start with SELECT or WITH (no explanations, comments, or text before)\n"
        "- Only SELECT queries allowed - NO INSERT/UPDATE/DELETE/DROP/ALTER/CREATE\n"
        "- Return raw SQL starting with SELECT, nothing else\n"
        "- Do NOT wrap in JSON or backticks\n"
        "- Keep queries simple and efficient\n"
        f"- Limit results to {max_rows} rows maximum\n"
        "Example output format: SELECT column FROM table WHERE condition LIMIT 50"
    )

    human_prompt = (
        f"Database schema available:\n{schema_description}\n\n"
        f"User question: {question}\n\n"
        "Write the SELECT query only. Start with SELECT or WITH. No other text."
    )

    llm_response = await chat_llm.ainvoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt),
        ]
    )

    raw_content = str(llm_response.content).strip()
    extracted = _extract_sql(raw_content)
    import logging
    logger = logging.getLogger(__name__)
    logger.debug(f"Generated SQL for question '{question}': {extracted}")
    return extracted


async def run_nl_to_sql_query(question: str, max_rows: int) -> SqlQueryResponse:
    sql_url = settings.supabase_sql_database_url or settings.database_url
    dsn = _to_asyncpg_database_url(sql_url)

    try:
        conn = await asyncpg.connect(dsn=dsn, timeout=20)
    except Exception as exc:  # pragma: no cover - environment dependent
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"message": f"Could not connect to SQL database: {exc}"},
        )

    try:
        import logging
        logger = logging.getLogger(__name__)
        
        schema_description = await _load_schema_description(conn)
        generated = await _generate_sql(question=question, schema_description=schema_description, max_rows=max_rows)
        
        logger.debug(f"Raw LLM output for '{question}': {repr(generated)}")
        
        safe_sql = _assert_safe_select_query(generated)
        executable_sql = _ensure_limit(safe_sql, max_rows)

        records = await conn.fetch(executable_sql)
        rows = [dict(r) for r in records]
        columns = list(rows[0].keys()) if rows else []

        return SqlQueryResponse(
            question=question,
            generated_sql=executable_sql,
            rows=rows,
            row_count=len(rows),
            columns=columns,
            generated_at=datetime.now(timezone.utc),
        )
    except ValueError as exc:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"SQL validation failed for question '{question}': {exc}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": str(exc), "question": question},
        )
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - environment dependent
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": f"Failed to run SQL query: {exc}"},
        )
    finally:
        await conn.close()
