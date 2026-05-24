import os
from pydantic_settings import BaseSettings
from pydantic import model_validator
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "码医 MediCode"
    app_version: str = "1.0.0"
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"

    # Database — supports SQLite (dev) and PostgreSQL (prod)
    database_url: str = os.getenv(
        "DATABASE_URL",
        "sqlite+aiosqlite:///./medicode.db",
    )
    database_sync_url: str = os.getenv(
        "DATABASE_SYNC_URL",
        "sqlite:///./medicode.db",
    )

    # LLM
    llm_model_name: str = os.getenv("LLM_MODEL", "qwen2.5:3b")
    llm_base_url: str = os.getenv("LLM_BASE_URL", "http://localhost:11434")

    # Security — must be set via env in production
    secret_key: str = os.getenv("SECRET_KEY", "")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

    # Demo credentials (must be set via env — no defaults in production)
    demo_admin_password: str = os.getenv("DEMO_ADMIN_PASSWORD", "")
    demo_coder_password: str = os.getenv("DEMO_CODER_PASSWORD", "")
    demo_doctor_password: str = os.getenv("DEMO_DOCTOR_PASSWORD", "")

    # DRG
    drg_base_rate: float = float(os.getenv("DRG_BASE_RATE", "12000.0"))

    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    @property
    def use_sqlite(self) -> bool:
        return "sqlite" in self.database_url

    @model_validator(mode="after")
    def _apply_defaults(self):
        if not self.secret_key:
            if self.debug:
                import secrets
                self.secret_key = secrets.token_urlsafe(32)
            else:
                raise ValueError("SECRET_KEY must be set in production (non-debug mode)")
        if not self.demo_admin_password and self.debug:
            self.demo_admin_password = "medicode2024"
            self.demo_coder_password = "code123"
            self.demo_doctor_password = "doc123"
        return self

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
