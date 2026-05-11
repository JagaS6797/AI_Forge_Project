from __future__ import annotations

import logging
from dataclasses import dataclass

from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.chains.rag_chain import build_rag_chain
from app.ai.rag.chroma_client import get_user_vector_store, user_collection_name
from app.ai.rag.pdf_loader import load_pdf_text
from app.ai.rag.text_splitter import split_text
from app.core.config import settings
from app.models.chat_thread import ChatThread
from app.models.file_attachment import FileAttachment
from app.models.rag_document import RagDocument
from app.schemas.attachment import AttachmentMetadata
from app.schemas.rag import PdfUploadResponse
from app.services.attachment_service import save_uploaded_file, validate_file
from app.services.user_service import get_or_create_user_id

logger = logging.getLogger(__name__)


@dataclass
class IngestResult:
    chunks_indexed: int


async def upload_and_index_pdf(
    *,
    db: AsyncSession,
    user_email: str,
    thread_id: str,
    file_name: str,
    content_type: str,
    content: bytes,
) -> PdfUploadResponse:
    is_valid, validation_error = validate_file(file_name=file_name, file_size=len(content), mime_type=content_type)
    if not is_valid:
        raise ValueError(validation_error)

    if len(content) > settings.max_upload_mb * 1024 * 1024:
        raise ValueError(f"PDF exceeds max upload size ({settings.max_upload_mb}MB)")

    if content_type != "application/pdf":
        raise ValueError("Only PDF files are allowed in this endpoint")

    user_id = await get_or_create_user_id(db, user_email)

    thread = await db.scalar(
        select(ChatThread).where(ChatThread.id == thread_id, ChatThread.user_id == user_id)
    )
    if not thread:
        raise ValueError("Thread not found or access denied")

    saved_path = save_uploaded_file(file_content=content, file_name=file_name, mime_type=content_type)

    attachment = FileAttachment(
        user_id=user_id,
        message_id=None,
        file_name=file_name,
        file_type=content_type,
        attachment_type="pdf",
        file_size=len(content),
        file_path=saved_path,
    )
    db.add(attachment)
    await db.flush()

    ingest_result = await ingest_pdf_attachment(
        db=db,
        user_email=user_email,
        thread_id=thread_id,
        attachment=attachment,
    )

    return PdfUploadResponse(
        attachment=AttachmentMetadata.model_validate(attachment),
        chunks_indexed=ingest_result.chunks_indexed,
        status="ready",
    )


async def ingest_pdf_attachment(
    *,
    db: AsyncSession,
    user_email: str,
    thread_id: str,
    attachment: FileAttachment,
) -> IngestResult:
    user_id = await get_or_create_user_id(db, user_email)

    raw_text = load_pdf_text(attachment.file_path)
    if not raw_text:
        raise ValueError("Uploaded PDF has no readable text")

    chunks = split_text(raw_text)
    if not chunks:
        raise ValueError("No chunks generated from PDF")

    vector_store = get_user_vector_store(user_id)
    metadatas = [
        {
            "user_id": user_id,
            "thread_id": thread_id,
            "attachment_id": attachment.id,
            "file_name": attachment.file_name,
            "chunk_index": idx,
            "source": "pdf",
        }
        for idx, _ in enumerate(chunks)
    ]
    ids = [f"{attachment.id}:{idx}" for idx, _ in enumerate(chunks)]
    vector_store.add_texts(chunks, metadatas=metadatas, ids=ids)

    rag_doc = RagDocument(
        user_id=user_id,
        thread_id=thread_id,
        attachment_id=attachment.id,
        file_name=attachment.file_name,
        collection_name=user_collection_name(user_id),
        chunks_count=len(chunks),
    )
    db.add(rag_doc)
    await db.commit()

    return IngestResult(chunks_indexed=len(chunks))


async def thread_has_rag_documents(*, db: AsyncSession, user_email: str, thread_id: str) -> bool:
    user_id = await get_or_create_user_id(db, user_email)
    query = select(exists().where(RagDocument.user_id == user_id).where(RagDocument.thread_id == thread_id))
    return bool(await db.scalar(query))


async def answer_with_rag(
    *,
    db: AsyncSession,
    user_email: str,
    thread_id: str,
    history: str,
    question: str,
    k: int = 4,
    relevance_threshold: float = 0.5,
) -> tuple[str, bool]:
    """Answer using RAG if relevant docs found, otherwise signal fallback to normal chat.
    
    Returns:
        (answer, should_use_rag) where should_use_rag=False means fall back to normal LLM.
    """
    user_id = await get_or_create_user_id(db, user_email)
    vector_store = get_user_vector_store(user_id)
    docs_with_scores = vector_store.similarity_search_with_score(question, k=k, filter={"thread_id": thread_id})

    if not docs_with_scores:
        return "", False

    docs = [doc for doc, score in docs_with_scores]
    max_score = max((score for doc, score in docs_with_scores), default=0.0)

    if max_score < relevance_threshold:
        return "", False

    context = "\n\n".join(doc.page_content for doc in docs)
    chain = build_rag_chain()
    response = await chain.ainvoke(
        {
            "context": context,
            "history": history,
            "human_input": question,
        }
    )
    return str(response).strip(), True
