from __future__ import annotations

from langchain_chroma import Chroma

from app.ai.rag.embeddings import get_embeddings_client
from app.core.config import settings


def user_collection_name(user_id: str) -> str:
    return f"user_{user_id}"


def get_user_vector_store(user_id: str) -> Chroma:
    return Chroma(
        collection_name=user_collection_name(user_id),
        embedding_function=get_embeddings_client(),
        persist_directory=settings.chroma_persist_dir,
    )
