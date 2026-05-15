from __future__ import annotations

import pytest

from app.services.sql_query_service import _assert_safe_select_query, _ensure_limit, _extract_sql


def test_extract_sql_from_json_payload() -> None:
    payload = '{"sql": "SELECT email FROM contacts"}'
    assert _extract_sql(payload) == "SELECT email FROM contacts"


def test_extract_sql_from_code_block() -> None:
    payload = "```sql\nSELECT id FROM users\n```"
    assert _extract_sql(payload) == "SELECT id FROM users"


def test_assert_safe_select_query_accepts_select() -> None:
    sql = _assert_safe_select_query("SELECT * FROM contacts")
    assert sql == "SELECT * FROM contacts"


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM contacts",
        "UPDATE contacts SET email = 'x'",
        "SELECT * FROM contacts; DROP TABLE contacts",
    ],
)
def test_assert_safe_select_query_rejects_unsafe(sql: str) -> None:
    with pytest.raises(ValueError):
        _assert_safe_select_query(sql)


def test_ensure_limit_adds_limit_when_missing() -> None:
    assert _ensure_limit("SELECT name FROM contacts", 25).endswith("LIMIT 25")


def test_ensure_limit_keeps_existing_limit() -> None:
    sql = "SELECT name FROM contacts LIMIT 3"
    assert _ensure_limit(sql, 25) == sql
