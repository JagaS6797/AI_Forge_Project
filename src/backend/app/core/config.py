from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    secret_key: str
    jwt_expire_minutes: int = 480
    app_name: str = "amzur-ai-chat"
    environment: str = "development"
    frontend_url: Optional[str] = None

    # Database
    database_url: str

    # Amzur LiteLLM Proxy
    litellm_proxy_url: str
    litellm_api_key: str
    litellm_user_id: Optional[str] = None
    llm_model: str
    litellm_embedding_model: str
    image_gen_model: str

    # Google OAuth
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    google_redirect_uri: Optional[str] = None

    # ChromaDB
    chroma_persist_dir: str = "./chroma_db"

    # Google Sheets
    google_service_account_json: Optional[str] = None

    # File uploads
    max_upload_mb: int = 20
    upload_dir: str = "./uploads"


settings = Settings()
