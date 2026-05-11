from __future__ import annotations

from pathlib import Path

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.ai.llm import chat_llm


def _prompt_text() -> str:
    prompt_path = Path(__file__).resolve().parents[1] / "prompts" / "rag_prompt.txt"
    return prompt_path.read_text(encoding="utf-8")


def build_rag_chain():
    prompt = ChatPromptTemplate.from_messages([
        ("system", _prompt_text()),
        (
            "human",
            "Document context:\n{context}\n\nPrevious conversation:\n{history}\n\nCurrent question:\n{human_input}",
        ),
    ])
    return prompt | chat_llm | StrOutputParser()
