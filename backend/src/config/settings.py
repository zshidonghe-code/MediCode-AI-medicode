import os
import secrets
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "码医 MediCode"
    app_version: str = "1.0.0"
    debug: bool = True

    # Database — supports SQLite (dev) and PostgreSQL (prod)
    database_url: str = os.getenv(
        "DATABASE_URL",
        "sqlite+aiosqlite:///./medicode.db",
    )
    database_sync_url: str = os.getenv(
        "DATABASE_SYNC_URL",
        "sqlite:///./medicode.db",
    )

    # Redis (optional in dev)
    redis_url: str = os.getenv("REDIS_URL", "")

    # ChromaDB
    chroma_persist_dir: str = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma")

    # LLM
    llm_model_name: str = os.getenv("LLM_MODEL", "qwen2.5:3b")
    llm_base_url: str = os.getenv("LLM_BASE_URL", "http://localhost:11434")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "shibing624/text2vec-base-chinese")

    # Security — autogenerate random key in dev, must be set in prod
    secret_key: str = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
    access_token_expire_minutes: int = 480

    # Demo credentials (override via env for production)
    demo_admin_password: str = os.getenv("DEMO_ADMIN_PASSWORD", "medicode2024")
    demo_coder_password: str = os.getenv("DEMO_CODER_PASSWORD", "code123")
    demo_doctor_password: str = os.getenv("DEMO_DOCTOR_PASSWORD", "doc123")

    # DRG
    drg_base_rate: float = float(os.getenv("DRG_BASE_RATE", "12000.0"))

    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    @property
    def use_sqlite(self) -> bool:
        return "sqlite" in self.database_url

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
