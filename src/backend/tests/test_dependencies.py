from __future__ import annotations

import pytest
from starlette.requests import Request

from app.core.dependencies import _extract_bearer_token, get_current_user


def _request(headers: dict[str, str] | None = None) -> Request:
    header_items = []
    for key, value in (headers or {}).items():
        header_items.append((key.lower().encode("latin-1"), value.encode("latin-1")))
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": header_items,
    }
    return Request(scope)


def test_extract_bearer_token_valid() -> None:
    request = _request({"Authorization": "Bearer abc123"})
    assert _extract_bearer_token(request) == "abc123"


def test_extract_bearer_token_invalid_scheme() -> None:
    request = _request({"Authorization": "Basic abc123"})
    assert _extract_bearer_token(request) is None


@pytest.mark.asyncio
async def test_get_current_user_returns_dev_placeholder_without_token() -> None:
    request = _request()
    user = await get_current_user(request)
    assert user.email == "dev@example.com"
