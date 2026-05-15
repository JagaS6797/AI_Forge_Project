"""Tests for Project 10: Research Digest Agent."""
from __future__ import annotations

import asyncio
import inspect
import json
from types import SimpleNamespace

import pytest

from app.schemas.research_digest import ResearchDigestRequest, ResearchDigestResponse, ResearchPaper
from app.api.research_digest import router
from app.services.research_digest_service import (
    _extract_mcp_payload,
    _is_live_sports_query,
    _normalize_research_topic,
    _paper_dict_to_schema,
    _paper_to_schema,
    _parse_mcp_payload_text,
    _sse,
    stream_research_digest,
)


# ── Schema tests ──────────────────────────────────────────────────────────────

class TestResearchDigestSchemas:
    def test_request_required_topic(self):
        req = ResearchDigestRequest(topic="deep learning")
        assert req.topic == "deep learning"

    def test_request_default_max_papers(self):
        req = ResearchDigestRequest(topic="test")
        assert req.max_papers == 5
        assert req.use_mcp is True

    def test_request_custom_max_papers(self):
        req = ResearchDigestRequest(topic="test", max_papers=3)
        assert req.max_papers == 3

    def test_request_custom_use_mcp(self):
        req = ResearchDigestRequest(topic="test", use_mcp=False)
        assert req.use_mcp is False

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

    def test_paper_dict_to_schema(self):
        paper = _paper_dict_to_schema(
            {
                "id": "2401.12345",
                "title": "MCP-based Retrieval",
                "authors": ["Alice", "Bob"],
                "abstract": "A paper about MCP integration.",
                "published": "2024-01-15",
            }
        )
        assert paper.title == "MCP-based Retrieval"
        assert paper.url == "https://arxiv.org/abs/2401.12345"

    def test_parse_mcp_payload_text_handles_wrapped_json(self):
        payload = _parse_mcp_payload_text(
            "Search results:\n{\"papers\": [{\"id\": \"2401.12345\", \"title\": \"Wrapped\"}]}"
        )
        assert payload["papers"][0]["title"] == "Wrapped"

    def test_extract_mcp_payload_skips_empty_chunks(self):
        result = SimpleNamespace(
            content=[
                SimpleNamespace(text=""),
                SimpleNamespace(text="   "),
                SimpleNamespace(text='{"papers": [{"id": "2401.12345", "title": "Recovered"}]}'),
            ]
        )

        payload = _extract_mcp_payload(result)

        assert payload["papers"][0]["title"] == "Recovered"

    def test_extract_mcp_payload_returns_empty_for_non_json(self):
        result = SimpleNamespace(content=[SimpleNamespace(text="temporary upstream error")])

        payload = _extract_mcp_payload(result)

        assert payload == {}

    def test_request_missing_topic_raises(self):
        with pytest.raises(Exception):
            ResearchDigestRequest()  # type: ignore[call-arg]

    def test_normalize_research_topic_from_prompt_sentence(self):
        topic = _normalize_research_topic("Give me a research digest on transformers in healthcare")
        assert topic == "transformers in healthcare"

    def test_normalize_research_topic_keeps_plain_topic(self):
        topic = _normalize_research_topic("multimodal llms for radiology")
        assert topic == "multimodal llms for radiology"


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
        import app.services.research_digest_service as svc
        original = svc._search_papers_via_mcp

        async def mock_search(*args, **kwargs):
            return []

        svc._search_papers_via_mcp = mock_search  # type: ignore[assignment]
        try:
            async for chunk in stream_research_digest(topic="", max_papers=3):
                events.append(chunk)
                if len(events) >= 3:
                    break
        finally:
            svc._search_papers_via_mcp = original  # type: ignore[assignment]

        # Should have received an error event
        combined = "".join(events)
        assert "error" in combined

    @pytest.mark.asyncio
    async def test_stream_no_results_yields_error(self):
        """If MCP and direct arXiv both return 0 papers, service yields an error event."""
        import app.services.research_digest_service as svc

        original = svc._search_papers_via_mcp
        original_direct = svc._search_papers_via_arxiv

        async def mock_no_results(*args, **kwargs):
            return []

        svc._search_papers_via_mcp = mock_no_results  # type: ignore[assignment]
        svc._search_papers_via_arxiv = mock_no_results  # type: ignore[assignment]
        try:
            chunks = []
            async for chunk in stream_research_digest(topic="xyzzy obscure topic 12345", max_papers=3):
                chunks.append(chunk)
                if len(chunks) >= 3:
                    break
        finally:
            svc._search_papers_via_mcp = original  # type: ignore[assignment]
            svc._search_papers_via_arxiv = original_direct  # type: ignore[assignment]

        combined = "".join(chunks)
        assert "event: error" in combined

    @pytest.mark.asyncio
    async def test_stream_toggle_off_uses_direct_arxiv_search(self):
        import app.services.research_digest_service as svc

        original_direct = svc._search_papers_via_arxiv
        original_mcp = svc._search_papers_via_mcp
        original_select = svc._select_relevant_papers

        async def mock_direct_search(*args, **kwargs):
            return [
                ResearchPaper(
                    title="Direct arXiv Paper",
                    authors=["A. Author"],
                    published="2024-01-01",
                    summary="Direct search path result.",
                    url="https://arxiv.org/abs/2401.00001",
                )
            ]

        async def mock_mcp_search(*args, **kwargs):
            raise AssertionError("MCP search should not be called when use_mcp=False")

        async def mock_select(topic: str, papers: list[ResearchPaper], max_papers: int):
            return papers[:max_papers]

        svc._search_papers_via_arxiv = mock_direct_search  # type: ignore[assignment]
        svc._search_papers_via_mcp = mock_mcp_search  # type: ignore[assignment]
        svc._select_relevant_papers = mock_select  # type: ignore[assignment]
        try:
            chunks = []
            async for chunk in stream_research_digest(topic="test topic", max_papers=1, use_mcp=False):
                chunks.append(chunk)
                if "event: selected_papers" in chunk:
                    break
        finally:
            svc._search_papers_via_arxiv = original_direct  # type: ignore[assignment]
            svc._search_papers_via_mcp = original_mcp  # type: ignore[assignment]
            svc._select_relevant_papers = original_select  # type: ignore[assignment]

        combined = "".join(chunks)
        assert "event: selected_papers" in combined

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
