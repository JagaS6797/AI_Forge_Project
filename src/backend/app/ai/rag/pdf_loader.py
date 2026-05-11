from __future__ import annotations

from langchain_community.document_loaders import PyPDFLoader


def load_pdf_text(file_path: str) -> str:
    loader = PyPDFLoader(file_path)
    pages = loader.load()
    text = "\n\n".join((page.page_content or "").strip() for page in pages if page.page_content)
    return text.strip()
