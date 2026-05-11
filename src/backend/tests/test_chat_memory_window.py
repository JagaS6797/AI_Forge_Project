from __future__ import annotations

from app.schemas.chat import ChatHistoryItem
from app.services.chat_service import _recent_conversations


def test_recent_conversations_keeps_latest_n_user_turns() -> None:
    history = [
        ChatHistoryItem(role="user", content="u1"),
        ChatHistoryItem(role="assistant", content="a1"),
        ChatHistoryItem(role="user", content="u2"),
        ChatHistoryItem(role="assistant", content="a2"),
        ChatHistoryItem(role="user", content="u3"),
        ChatHistoryItem(role="assistant", content="a3"),
    ]

    result = _recent_conversations(history, max_conversations=2)

    assert [item.content for item in result] == ["u2", "a2", "u3", "a3"]


def test_recent_conversations_returns_all_when_under_limit() -> None:
    history = [
        ChatHistoryItem(role="user", content="u1"),
        ChatHistoryItem(role="assistant", content="a1"),
    ]

    result = _recent_conversations(history, max_conversations=5)

    assert [item.content for item in result] == ["u1", "a1"]


def test_recent_conversations_zero_limit_returns_empty() -> None:
    history = [
        ChatHistoryItem(role="user", content="u1"),
        ChatHistoryItem(role="assistant", content="a1"),
    ]

    result = _recent_conversations(history, max_conversations=0)

    assert result == []
