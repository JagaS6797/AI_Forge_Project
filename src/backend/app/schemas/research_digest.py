from __future__ import annotations

from pydantic import BaseModel


class ResearchDigestRequest(BaseModel):
    topic: str
    max_papers: int = 5
    use_mcp: bool = True


class ResearchPaper(BaseModel):
    title: str
    authors: list[str]
    published: str
    summary: str
    url: str


class ResearchDigestResponse(BaseModel):
    topic: str
    papers_found: int
    digest: str
    key_papers: list[ResearchPaper]
    generated_at: str
