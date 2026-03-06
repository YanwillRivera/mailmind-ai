from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Anthropic
    anthropic_api_key: str

    # Google OAuth (from Google Cloud Console)
    google_client_id: str
    google_client_secret: str
    google_redirect_uri: str = "http://localhost:8000/auth/callback"

    # Notion (optional — skip if not using Notion)
    notion_api_key: str = ""
    notion_database_id: str = ""

    # App
    secret_key: str = "change-this-in-production"
    poll_interval_seconds: int = 60   # How often to check for new emails

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
