import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy import select, func, text
from src.config.settings import get_settings
from src.models import init_db  # registers all models on Base.metadata
from src.models.database import async_session, engine
from src.models.patient import Patient
from src.models.icd import ICDCode
from src.api.router import api_router

logger = logging.getLogger(__name__)
settings = get_settings()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self'"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()

    # Auto-seed ICD codes + demo data if database is empty (competition demo safety)
    try:
        async with async_session() as db:
            icd_count = (await db.execute(select(func.count()).select_from(ICDCode))).scalar() or 0
            patient_count = (await db.execute(select(func.count()).select_from(Patient))).scalar() or 0

        if icd_count == 0:
            logger.info("ICD codes empty, auto-seeding reference data...")
            from src.scripts.seed_data import seed_icd_codes, seed_drg_groups, seed_qc_rules
            await seed_icd_codes()
            await seed_drg_groups()
            await seed_qc_rules()
            async with async_session() as db:
                await db.execute(text("ANALYZE"))
                await db.commit()
            logger.info("Reference data seeded")

        if patient_count == 0:
            logger.info("Database is empty, auto-seeding demo data...")
            from src.scripts.seed_pipeline_demo import seed_pipeline_demo
            await seed_pipeline_demo()
            logger.info("Demo data seeded successfully")
    except Exception as e:
        logger.warning(f"Auto-seed skipped: {e}")

    # Prewarm LLM engine (non-blocking detection)
    try:
        from src.services.llm_engine import llm_engine
        backend = await llm_engine.prewarm()
        logger.info(f"LLM backend: {backend}")
    except Exception as e:
        logger.warning(f"LLM prewarm skipped: {e}")
    yield
    # Shutdown
    await engine.dispose()
    logger.info("Database engine disposed")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/docs" if settings.debug else None,
    lifespan=lifespan,
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/health/llm")
async def health_llm():
    """检查 LLM (Ollama) 是否在线"""
    try:
        from src.services.llm_engine import llm_engine
        if llm_engine._ollama is None:
            from src.services.llm_engine.engine import OllamaBackend
            llm_engine._ollama = OllamaBackend()
        available = await llm_engine._ollama.is_available()
        llm_engine._available = available
        return {"llm_available": available, "llm_backend": "ollama" if available else "rule-based"}
    except Exception:
        return {"llm_available": False, "llm_backend": "rule-based"}
