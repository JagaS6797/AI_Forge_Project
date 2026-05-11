from __future__ import annotations

from langchain_openai import OpenAIEmbeddings

from app.core.config import settings


def get_embeddings_client() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(
        model=settings.litellm_embedding_model,
        openai_api_base=settings.litellm_proxy_url,
        openai_api_key=settings.litellm_api_key,
    )
