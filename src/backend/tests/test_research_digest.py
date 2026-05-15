"""Tests for Project 10: Research Digest Agent."""
from __future__ import annotations

import asyncio
import inspect
import json

import pytest

from app.schemas.research_digest import ResearchDigestRequest, ResearchDigestResponse, ResearchPaper
from app.api.research_digest import router
from app.services.research_digest_service import _is_live_sports_query, _sse, _paper_to_schema, stream_research_digest


# ── Schema tests ──────────────────────────────────────────────────────────────

class TestResearchDigestSchemas:
    def test_request_required_topic(self):
        req = ResearchDigestRequest(topic="deep learning")
        assert req.topic == "deep learning"

    def test_request_default_max_papers(self):
        req = ResearchDigestRequest(topic="test")
        assert req.max_papers == 5

    def test_request_custom_max_papers(self):
        req = ResearchDigestRequest(topic="test", max_papers=3)
        assert req.max_papers == 3

    def test_research_paper_model(self):
        paper = ResearchPaper(
            title="Attention Is All You Need",
            authors=["Vaswani et al."],
            published="2017-06-12",
            summary="Transformer architecture…",
            url="https://arxiv.org/abs/1706.03762",
        )
        assert paper.title == "Attention Is All You Need"
        assert paper.url.startswith("https://")

    def test_request_missing_topic_raises(self):
        with pytest.raises(Exception):
            ResearchDigestRequest()  # type: ignore[call-arg]


# ── SSE helper tests ──────────────────────────────────────────────────────────

class TestSseHelper:
    def test_sse_format(self):
        result = _sse("status", {"message": "Searching", "step": 1})
        assert result.startswith("event: status\n")
        assert result.endswith("\n\n")

    def test_sse_data_is_valid_json(self):
        result = _sse("done", {"topic": "ai", "papers_found": 3})
        data_line = [l for l in result.split("\n") if l.startswith("data: ")][0]
        parsed = json.loads(data_line[6:])
        assert parsed["topic"] == "ai"
        assert parsed["papers_found"] == 3

    def test_sse_error_event(self):
        result = _sse("error", {"message": "Rate limited"})
        assert "event: error\n" in result

    def test_sse_empty_data(self):
        result = _sse("status", {})
        assert "data: {}" in result


# ── Router tests ──────────────────────────────────────────────────────────────

class TestResearchRouter:
    def test_router_prefix(self):
        assert router.prefix == "/api/research"

    def test_digest_route_registered(self):
        paths = [r.path for r in router.routes]
        assert "/api/research/digest" in paths

    def test_router_tag(self):
        assert "research" in router.tags


# ── Service tests ─────────────────────────────────────────────────────────────

class TestResearchDigestService:
    def test_live_sports_query_detection(self):
        assert _is_live_sports_query("What teams are participating in today's IPL match?") is True
        assert _is_live_sports_query("Latest research papers on transformers") is False

    def test_stream_is_async_generator(self):
        assert inspect.isasyncgenfunction(stream_research_digest)

    def test_stream_signature(self):
        sig = inspect.signature(stream_research_digest)
        params = list(sig.parameters)
        assert "topic" in params
        assert "max_papers" in params

    @pytest.mark.asyncio
    async def test_stream_empty_topic_yields_error(self):
        """An empty string topic should yield an error SSE event (no papers found)."""
        events = []
        # We don't actually call arXiv — monkeypatch the blocking call
        import app.services.research_digest_service as svc
        import asyncio

        original = asyncio.to_thread

        async def mock_to_thread(fn, *args, **kwargs):
            return []  # simulate no results from arXiv

        asyncio.to_thread = mock_to_thread  # type: ignore[assignment]
        try:
            async for chunk in stream_research_digest(topic="", max_papers=3):
                events.append(chunk)
                if len(events) >= 3:
                    break
        finally:
            asyncio.to_thread = original

        # Should have received an error event
        combined = "".join(events)
        assert "error" in combined

    @pytest.mark.asyncio
    async def test_stream_no_results_yields_error(self):
        """If arXiv returns 0 papers, service yields an error event."""
        import asyncio

        original = asyncio.to_thread

        async def mock_no_results(fn, *args, **kwargs):
            return []

        asyncio.to_thread = mock_no_results  # type: ignore[assignment]
        try:
            chunks = []
            async for chunk in stream_research_digest(topic="xyzzy obscure topic 12345", max_papers=3):
                chunks.append(chunk)
                if len(chunks) >= 3:
                    break
        finally:
            asyncio.to_thread = original

        combined = "".join(chunks)
        assert "event: error" in combined

    @pytest.mark.asyncio
    async def test_stream_live_sports_query_yields_done(self):
        """Sports/IPL query should use live path and emit done."""
        import asyncio

        original = asyncio.to_thread

        async def mock_fixture(*args, **kwargs):
            return {
                "match_number": "59",
                "team_a": "LSG",
                "team_b": "CSK",
                "time": "7:30 pm IST",
                "venue": "Lucknow",
                "source": "https://www.iplt20.com/matches/fixtures",
            }

        asyncio.to_thread = mock_fixture  # type: ignore[assignment]
        try:
            chunks = []
            async for chunk in stream_research_digest(
                topic="What teams are participating in today's IPL match?",
                max_papers=3,
            ):
                chunks.append(chunk)
                if "event: done" in chunk:
                    break
        finally:
            asyncio.to_thread = original

        combined = "".join(chunks)
        assert "event: done" in combined
        assert "LSG" in combined and "CSK" in combined
