from __future__ import annotations

import asyncio
import json
import logging
import re
from datetime import datetime, timezone
from typing import TYPE_CHECKING, AsyncIterator, Any

import requests
from langchain_core.messages import HumanMessage, SystemMessage

from app.ai.llm import chat_llm
from app.schemas.research_digest import ResearchPaper

if TYPE_CHECKING:
    import arxiv

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


def _import_arxiv() -> Any:
    """Import arxiv lazily so missing package does not crash app startup."""
    try:
        import arxiv  # type: ignore[import]
    except Exception as exc:
        raise RuntimeError(
            "The arxiv package is not installed. Install backend dependencies from requirements.txt."
        ) from exc
    return arxiv


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

async def stream_research_digest(topic: str, max_papers: int = 5) -> AsyncIterator[str]:
    """
    Streaming generator that:
      1. Searches arXiv for relevant papers
      2. Decides (via LLM) whether it has enough evidence
      3. Streams a structured research digest as SSE events
    """
    if _is_live_sports_query(topic):
        async for event in _stream_live_ipl_digest(topic):
            yield event
        return

    yield _sse("status", {"message": f"Searching arXiv for: {topic}…", "step": 1})

    # ── Step 1: Search arXiv ─────────────────────────────────────────────────
    try:
        arxiv = _import_arxiv()
        client = arxiv.Client(num_retries=3, delay_seconds=3)
        search = arxiv.Search(
            query=topic,
            max_results=max_papers + 3,   # fetch a few extra for agent to choose from
            sort_by=arxiv.SortCriterion.Relevance,
        )
        # results() is blocking I/O — run in thread to avoid blocking event loop
        results = await asyncio.to_thread(lambda: list(client.results(search)))
    except Exception as exc:
        logger.exception("arXiv search failed")
        yield _sse("error", {"message": f"arXiv search failed: {exc}"})
        return

    if not results:
        yield _sse("error", {"message": f"No papers found on arXiv for topic: {topic!r}"})
        return

    papers = [_paper_to_schema(r) for r in results]
    yield _sse("papers_found", {
        "count": len(papers),
        "message": f"Found {len(papers)} papers. Evaluating relevance…",
        "step": 2,
    })

    # ── Step 2: LLM decides which papers are relevant ────────────────────────
    paper_list_text = "\n\n".join(
        f"[{i+1}] {p.title}\nAuthors: {', '.join(p.authors)}\nPublished: {p.published}\nSummary: {p.summary}"
        for i, p in enumerate(papers)
    )

    # Calculate selection range based on max_papers
    min_papers = min(3, max_papers)  # Minimum 3 papers, or max_papers if less
    max_selection = min(max_papers, len(papers))  # Don't exceed available papers

    selection_messages = [
        SystemMessage(content=(
            "You are a research evaluation agent. Given a topic and a list of arXiv papers, "
            "decide which papers are most relevant. Return ONLY a JSON array of 1-based indices "
            f"of the selected papers (e.g. [1, 2, 4]). Select between {min_papers} and {max_selection} papers. "
            "Aim to select as many as possible (closer to {max_selection}) if they are relevant. "
            "No explanation — just the JSON array."
        )),
        HumanMessage(content=(
            f"Topic: {topic}\n\nPapers:\n{paper_list_text}\n\n"
            "Which papers (by number) best cover this topic? Return a JSON array of indices."
        )),
    ]

    yield _sse("status", {"message": "Agent evaluating paper relevance…", "step": 3})

    try:
        selection_response = await chat_llm.ainvoke(selection_messages)
        raw = selection_response.content.strip()
        # Extract JSON array robustly
        start, end = raw.find("["), raw.rfind("]")
        indices: list[int] = json.loads(raw[start:end + 1]) if start != -1 else list(range(1, min(4, len(papers)) + 1))
        selected_papers = [papers[i - 1] for i in indices if 1 <= i <= len(papers)][:max_papers]
    except Exception:
        logger.warning("LLM selection failed, falling back to top papers")
        selected_papers = papers[:max_papers]

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
