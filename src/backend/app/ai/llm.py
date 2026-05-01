from typing import Any

from app.core.config import settings
from langchain_openai import ChatOpenAI

# AI clients should be initialized here and imported elsewhere.
# Keep this file as the single gateway for LLM and embedding clients.

_model_kwargs: dict[str, Any] = {}
_extra_body: dict[str, Any] | None = None

if settings.litellm_user_id:
    # user goes in model_kwargs (forwarded as an OpenAI API parameter)
    _model_kwargs["user"] = settings.litellm_user_id
    # extra_body is a langchain-openai top-level parameter
    _extra_body = {
        "metadata": {
            "litellm_user_id": settings.litellm_user_id,
        }
    }

chat_llm = ChatOpenAI(
    model=settings.llm_model,
    base_url=settings.litellm_proxy_url,
    api_key=settings.litellm_api_key,
    timeout=30,
    max_retries=2,
    model_kwargs=_model_kwargs,
    extra_body=_extra_body,
)

__all__ = ["chat_llm"]
