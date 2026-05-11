from __future__ import annotations

import os


# Provide minimum required settings env before importing app modules.
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/test_db")
os.environ.setdefault("LITELLM_PROXY_URL", "http://localhost:4000")
os.environ.setdefault("LITELLM_API_KEY", "test-key")
os.environ.setdefault("LLM_MODEL", "gpt-4o-mini")
os.environ.setdefault("LITELLM_EMBEDDING_MODEL", "text-embedding-3-small")
os.environ.setdefault("IMAGE_GEN_MODEL", "gpt-image-1")
os.environ.setdefault("ENVIRONMENT", "development")
