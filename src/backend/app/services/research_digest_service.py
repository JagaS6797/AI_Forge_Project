from __future__ import annotations

import asyncio
import json
import logging
import re
from datetime import datetime, timezone
from typing import AsyncIterator, Any, TypedDict

import arxiv
from mcp import ClientSession
from mcp.client.stdio import stdio_client
import requests
from langgraph.graph import END, START, StateGraph
from langchain_core.messages import HumanMessage, SystemMessage

from app.ai.llm import chat_llm
from app.ai.mcp_config import get_arxiv_mcp_server_params
from app.schemas.research_digest import ResearchPaper

logger = logging.getLogger(__name__)

_IPL_FIXTURES_URL = "https://www.cricbuzz.com/cricket-match/live-scores"
_LIVE_SPORTS_KEYWORDS = (
    "ipl",
    "cricket",
    "today match",
    "today's match",
    "teams are participating",
    "who is playing",
)

_RESEARCH_PROMPT_PREFIXES = (
    "give me a research digest on",
    "create a research digest on",
    "generate a research digest on",
    "research digest on",
    "give me research on",
    "summarize research on",
    "summarise research on",
    "what does research say about",
)


class ResearchDigestState(TypedDict, total=False):
    topic: str
    max_papers: int
    papers: list[ResearchPaper]
    selected_papers: list[ResearchPaper]

# ── helpers ──────────────────────────────────────────────────────────────────

def _sse(event: str, data: dict) -> str:
    """Format a single SSE message."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _paper_to_schema(result: Any) -> ResearchPaper:
    return ResearchPaper(
        title=result.title,
        authors=[str(a) for a in result.authors[:4]],
        published=result.published.strftime("%Y-%m-%d") if result.published else "unknown",
        summary=result.summary[:400].replace("\n", " ") + "…",
        url=result.entry_id,
    )


def _paper_dict_to_schema(result: dict[str, Any]) -> ResearchPaper:
    authors = result.get("authors", [])
    published = result.get("published") or result.get("published_date") or "unknown"
    summary = (result.get("abstract") or result.get("summary") or "").replace("\n", " ").strip()
    if len(summary) > 400:
        summary = summary[:400] + "…"

    paper_id = result.get("id") or result.get("paper_id") or ""
    paper_url = paper_id if str(paper_id).startswith("http") else f"https://arxiv.org/abs/{paper_id}"

    return ResearchPaper(
        title=result.get("title", "Untitled paper"),
        authors=[str(author) for author in authors[:4]],
        published=str(published),
        summary=summary or "No abstract available.",
        url=paper_url,
    )


def _coerce_mcp_payload(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, list):
        return {"papers": value}
    return {}


def _extract_json_candidate(text: str) -> str:
    stripped = text.strip()
    if not stripped:
        return ""

    start_positions = [pos for pos in (stripped.find("{"), stripped.find("[")) if pos != -1]
    end_positions = [pos for pos in (stripped.rfind("}"), stripped.rfind("]")) if pos != -1]
    if not start_positions or not end_positions:
        return stripped

    start = min(start_positions)
    end = max(end_positions)
    return stripped[start:end + 1]


def _parse_mcp_payload_text(payload_text: str) -> dict[str, Any]:
    candidate = _extract_json_candidate(payload_text)
    if not candidate:
        return {}

    parsed: Any = candidate
    for _ in range(2):
        if not isinstance(parsed, str):
            break
        parsed = json.loads(parsed)

    return _coerce_mcp_payload(parsed)


def _normalize_research_topic(topic: str) -> str:
    normalized = re.sub(r"\s+", " ", topic).strip()
    lowered = normalized.lower()

    for prefix in _RESEARCH_PROMPT_PREFIXES:
        if lowered.startswith(prefix):
            normalized = normalized[len(prefix):].strip(" :.-")
            break

    # Remove trailing punctuation that usually comes from conversational prompts.
    normalized = normalized.rstrip("?.!").strip()
    return normalized or topic.strip()


def _extract_mcp_payload(result: Any) -> dict[str, Any]:
    content = getattr(result, "content", None) or []
    text_chunks = [item.text.strip() for item in content if getattr(item, "text", "").strip()]

    if not text_chunks:
        logger.warning("arXiv MCP returned no text payload")
        return {}

    for text in text_chunks:
        try:
            payload = _parse_mcp_payload_text(text)
        except json.JSONDecodeError:
            continue
        if payload:
            return payload

    combined = "\n".join(text_chunks)
    try:
        payload = _parse_mcp_payload_text(combined)
    except json.JSONDecodeError:
        logger.warning("Unexpected arXiv MCP payload: %s", combined[:500])
        return {}

    if payload:
        return payload

    logger.warning("arXiv MCP payload did not contain paper JSON: %s", combined[:500])
    return {}


async def _search_papers_via_mcp(topic: str, max_results: int) -> list[ResearchPaper]:
    """Search arXiv through the MCP server instead of the direct arxiv client."""
    server_params = get_arxiv_mcp_server_params()

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool(
                "search_papers",
                {
                    "query": topic,
                    "max_results": max_results,
                    "sort_by": "relevance",
                },
            )

    if not result.content:
        return []

    payload = _extract_mcp_payload(result)
    papers = payload.get("papers", [])
    return [_paper_dict_to_schema(paper) for paper in papers]


async def _search_papers_via_arxiv(topic: str, max_results: int) -> list[ResearchPaper]:
    def _run_search() -> list[ResearchPaper]:
        client = arxiv.Client()
        search = arxiv.Search(
            query=topic,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance,
        )
        return [_paper_to_schema(result) for result in client.results(search)]

    return await asyncio.to_thread(_run_search)


async def _select_relevant_papers(topic: str, papers: list[ResearchPaper], max_papers: int) -> list[ResearchPaper]:
    paper_list_text = "\n\n".join(
        f"[{i+1}] {p.title}\nAuthors: {', '.join(p.authors)}\nPublished: {p.published}\nSummary: {p.summary}"
        for i, p in enumerate(papers)
    )

    min_papers = min(3, max_papers)
    max_selection = min(max_papers, len(papers))

    selection_messages = [
        SystemMessage(content=(
            "You are a research evaluation agent. Given a topic and a list of arXiv papers, "
            "decide which papers are most relevant. Return ONLY a JSON array of 1-based indices "
            f"of the selected papers (e.g. [1, 2, 4]). Select between {min_papers} and {max_selection} papers. "
            f"Aim to select as many as possible (closer to {max_selection}) if they are relevant. "
            "No explanation — just the JSON array."
        )),
        HumanMessage(content=(
            f"Topic: {topic}\n\nPapers:\n{paper_list_text}\n\n"
            "Which papers (by number) best cover this topic? Return a JSON array of indices."
        )),
    ]

    try:
        selection_response = await chat_llm.ainvoke(selection_messages)
        raw = selection_response.content.strip()
        start, end = raw.find("["), raw.rfind("]")
        indices: list[int] = json.loads(raw[start:end + 1]) if start != -1 else list(range(1, min(4, len(papers)) + 1))
        return [papers[i - 1] for i in indices if 1 <= i <= len(papers)][:max_papers]
    except Exception:
        logger.warning("LLM selection failed, falling back to top papers")
        return papers[:max_papers]


async def _graph_search_node(state: ResearchDigestState) -> ResearchDigestState:
    papers = await _search_papers_via_mcp(state["topic"], state["max_papers"] + 3)
    return {"papers": papers}


async def _graph_select_node(state: ResearchDigestState) -> ResearchDigestState:
    selected_papers = await _select_relevant_papers(
        state["topic"],
        state.get("papers", []),
        state["max_papers"],
    )
    return {"selected_papers": selected_papers}


def _build_research_graph():
    graph = StateGraph(ResearchDigestState)
    graph.add_node("search", _graph_search_node)
    graph.add_node("select", _graph_select_node)
    graph.add_edge(START, "search")
    graph.add_edge("search", "select")
    graph.add_edge("select", END)
    return graph.compile()


_RESEARCH_GRAPH = _build_research_graph()


def _is_live_sports_query(topic: str) -> bool:
    lowered = topic.lower()
    return any(keyword in lowered for keyword in _LIVE_SPORTS_KEYWORDS)


def _fetch_today_ipl_fixture() -> dict[str, str] | None:
    """Fetch today's IPL fixture from Cricbuzz live scores page."""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    response = requests.get(_IPL_FIXTURES_URL, headers=headers, timeout=20)
    response.raise_for_status()
    html = response.text

    matches = re.findall(
        r'<a\s+title="([^"]+)"\s+href="([^"]*indian-premier-league-2026[^"]*)"',
        html,
        re.IGNORECASE,
    )
    if not matches:
        return None

    # Prefer upcoming/live entry over completed result.
    selected_title = None
    selected_href = None
    for title, href in matches:
        lower_title = title.lower()
        if "preview" in lower_title or "live" in lower_title:
            selected_title, selected_href = title, href
            break

    if not selected_title:
        selected_title, selected_href = matches[0]

    title_clean = re.sub(r"\s+", " ", selected_title).strip()
    # Example: "Lucknow Super Giants vs Chennai Super Kings, 59th Match - Preview"
    teams_part, _, details_part = title_clean.partition(",")
    if " vs " not in teams_part:
        return None
    team_a, team_b = [t.strip() for t in teams_part.split(" vs ", 1)]

    match_number_match = re.search(r"(\d+)(?:st|nd|rd|th)\s+Match", details_part, re.IGNORECASE)
    match_number = match_number_match.group(1) if match_number_match else "TBD"

    status = ""
    if "-" in details_part:
        status = details_part.split("-", 1)[1].strip()

    return {
        "match_number": match_number,
        "team_a": team_a,
        "team_b": team_b,
        "time": "See source",
        "venue": "See source",
        "source": f"https://www.cricbuzz.com{selected_href}" if selected_href.startswith("/") else _IPL_FIXTURES_URL,
        "status": status or "Scheduled",
    }


async def _stream_live_ipl_digest(topic: str) -> AsyncIterator[str]:
    """Stream live IPL info for sports-centric questions."""
    yield _sse("status", {"message": "Fetching live IPL fixtures...", "step": 1})

    try:
        fixture = await asyncio.to_thread(_fetch_today_ipl_fixture)
    except Exception as exc:
        logger.exception("Failed to fetch IPL fixtures")
        yield _sse("error", {"message": f"Unable to fetch live IPL data: {exc}"})
        return

    if not fixture:
        yield _sse(
            "error",
            {
                "message": (
                    "Live IPL fixture was not found for today on the official fixtures page. "
                    "Please check again closer to match time."
                )
            },
        )
        return

    digest = (
        "## Overview\n"
        f"For today, the IPL fixture is **{fixture['team_a']} vs {fixture['team_b']}**.\n\n"
        "## Key Findings\n"
        f"- Match: {fixture['team_a']} vs {fixture['team_b']}\n"
        f"- Match number: {fixture['match_number']}\n"
        f"- Status: {fixture.get('status', 'Scheduled')}\n"
        f"- Time: {fixture['time']}\n"
        f"- Venue: {fixture['venue']}\n"
        f"- Source: {fixture['source']}\n\n"
        "## Research Gaps\n"
        "- Playing XI and toss updates are usually announced closer to match start.\n"
        "- Last-minute team changes may not appear immediately in fixtures.\n\n"
        "## Recommendation\n"
        "Use this fixture as baseline, and verify toss/playing XI from live score pages at match time."
    )

    yield _sse("status", {"message": "Formatting live fixture digest...", "step": 2})
    yield _sse("digest_chunk", {"token": digest})
    yield _sse(
        "done",
        {
            "topic": topic,
            "papers_found": 0,
            "digest": digest,
            "key_papers": [],
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "step": 3,
        },
    )


# ── main streaming generator ─────────────────────────────────────────────────

async def stream_research_digest(topic: str, max_papers: int = 5, use_mcp: bool = True) -> AsyncIterator[str]:
    """
    Streaming generator that:
      1. Searches arXiv for relevant papers
      2. Decides (via LLM) whether it has enough evidence
      3. Streams a structured research digest as SSE events
            4. Uses MCP search when enabled, otherwise falls back to direct arXiv search
    """
    if _is_live_sports_query(topic):
        async for event in _stream_live_ipl_digest(topic):
            yield event
        return

    search_topic = _normalize_research_topic(topic)

    yield _sse("status", {"message": f"Searching arXiv for: {search_topic}…", "step": 1})

    # ── Step 1-2: LangGraph orchestrates MCP search + relevance selection ───
    graph_state: dict[str, Any] = {}

    if use_mcp:
        try:
            graph_state = await _RESEARCH_GRAPH.ainvoke({"topic": search_topic, "max_papers": max_papers})
        except Exception as exc:
            logger.exception("arXiv MCP search failed")
            yield _sse("status", {"message": "MCP search failed. Falling back to direct arXiv search...", "step": 2})
            try:
                papers = await _search_papers_via_arxiv(search_topic, max_papers + 3)
            except Exception as fallback_exc:
                logger.exception("Direct arXiv fallback search failed")
                yield _sse("error", {"message": f"Research search failed (MCP and fallback): {fallback_exc}"})
                return

            selected_papers = await _select_relevant_papers(search_topic, papers, max_papers)
            graph_state = {
                "topic": search_topic,
                "max_papers": max_papers,
                "papers": papers,
                "selected_papers": selected_papers,
            }
    else:
        try:
            papers = await _search_papers_via_arxiv(search_topic, max_papers + 3)
        except Exception as exc:
            logger.exception("Direct arXiv search failed")
            yield _sse("error", {"message": f"Direct arXiv search failed: {exc}"})
            return

        selected_papers = await _select_relevant_papers(search_topic, papers, max_papers)
        graph_state = {
            "topic": search_topic,
            "max_papers": max_papers,
            "papers": papers,
            "selected_papers": selected_papers,
        }

    papers = graph_state.get("papers", [])

    if not papers:
        if use_mcp:
            # Handle no-results or rate-limited MCP responses by retrying direct arXiv once.
            yield _sse("status", {"message": "No MCP papers returned. Retrying with direct arXiv search...", "step": 2})
            try:
                papers = await _search_papers_via_arxiv(search_topic, max_papers + 3)
            except Exception as fallback_exc:
                logger.exception("Direct arXiv retry failed")
                yield _sse("error", {"message": f"No papers found via MCP and direct arXiv retry failed: {fallback_exc}"})
                return
            graph_state["papers"] = papers
            graph_state["selected_papers"] = await _select_relevant_papers(search_topic, papers, max_papers)

    if not papers:
        yield _sse("error", {"message": f"No papers found on arXiv for topic: {search_topic!r}"})
        return

    yield _sse("papers_found", {
        "count": len(papers),
        "message": f"Found {len(papers)} papers. Evaluating relevance…",
        "step": 2,
    })

    yield _sse("status", {"message": "Agent evaluating paper relevance…", "step": 3})

    selected_papers = graph_state.get("selected_papers", [])

    yield _sse("selected_papers", {
        "papers": [p.model_dump() for p in selected_papers],
        "message": f"Selected {len(selected_papers)} relevant papers. Generating digest…",
        "step": 4,
    })

    # ── Step 3: LLM generates structured digest ──────────────────────────────
    selected_text = "\n\n".join(
        f"### {p.title}\n- Authors: {', '.join(p.authors)}\n- Published: {p.published}\n- URL: {p.url}\n- Summary: {p.summary}"
        for p in selected_papers
    )

    digest_messages = [
        SystemMessage(content=(
            "You are a research digest writer. Write a clear, structured digest for researchers. "
            "Format your response with these sections:\n"
            "## Overview\n(2-3 sentence summary of the research landscape)\n\n"
            "## Key Findings\n(bullet list of the most important findings across papers)\n\n"
            "## Research Gaps\n(what areas need more investigation)\n\n"
            "## Recommendation\n(which paper to read first and why)\n\n"
            "Be concise. Use markdown formatting."
        )),
        HumanMessage(content=(
            f"Topic: {topic}\n\nSelected Papers:\n{selected_text}\n\n"
            "Write the research digest."
        )),
    ]

    yield _sse("status", {"message": "Writing research digest…", "step": 5})

    try:
        # Stream the digest text token by token
        digest_chunks: list[str] = []
        async for chunk in chat_llm.astream(digest_messages):
            token = chunk.content
            if token:
                digest_chunks.append(token)
                yield _sse("digest_chunk", {"token": token})

        full_digest = "".join(digest_chunks)
    except Exception as exc:
        logger.exception("Digest generation failed")
        yield _sse("error", {"message": f"Digest generation failed: {exc}"})
        return

    # ── Step 4: Final summary event ──────────────────────────────────────────
    yield _sse("done", {
        "topic": topic,
        "papers_found": len(selected_papers),
        "digest": full_digest,
        "key_papers": [p.model_dump() for p in selected_papers],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "step": 6,
    })
