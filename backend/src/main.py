import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, func
from src.config.settings import get_settings
from src.models import init_db  # registers all models on Base.metadata
from src.models.database import async_session
from src.models.patient import Patient
from src.api.router import api_router

logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()

    # Auto-seed demo data if database is empty (competition demo safety)
    try:
        async with async_session() as db:
            count = (await db.execute(select(func.count()).select_from(Patient))).scalar() or 0
        if count == 0:
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


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/docs" if settings.debug else None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "ok", "app": settings.app_name, "version": settings.app_version}


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
