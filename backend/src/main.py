import logging
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy import select, func, text
from src.config.settings import get_settings
from src.models import init_db  # registers all models on Base.metadata
from src.models.database import async_session, engine
from src.models.patient import Patient
from src.api.router import api_router

logger = logging.getLogger(__name__)
settings = get_settings()

# ── Rate limiter (in-memory sliding window) ──────────────────────────
# Competition-grade: protects against abuse, no external dependency.
_RATE_WINDOW_SEC = 60
_RATE_MAX_REQUESTS = 120  # per window per IP
_rate_buckets: dict[str, list[float]] = {}
_rate_cleanup_counter = 0


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple sliding-window rate limiter (in-memory, no Redis needed)."""

    async def dispatch(self, request: Request, call_next):
        # Skip health / docs endpoints
        path = request.url.path
        if path.startswith(("/health", "/docs", "/openapi.json", "/redoc")):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window_start = now - _RATE_WINDOW_SEC

        bucket = _rate_buckets.get(client_ip, [])
        bucket = [t for t in bucket if t > window_start]
        _rate_buckets[client_ip] = bucket

        if len(bucket) >= _RATE_MAX_REQUESTS:
            logger.warning(f"Rate limit hit: {client_ip} ({len(bucket)} req/{_RATE_WINDOW_SEC}s)")
            return JSONResponse(
                status_code=429,
                content={"detail": "请求过于频繁，请稍后再试。Too many requests."},
            )

        bucket.append(now)

        # Periodic stale-entry cleanup (every ~500 requests)
        global _rate_cleanup_counter
        _rate_cleanup_counter += 1
        if _rate_cleanup_counter % 500 == 0:
            cutoff = now - _RATE_WINDOW_SEC * 2
            stale = [ip for ip, times in list(_rate_buckets.items())
                      if not times or times[-1] < cutoff]
            for ip in stale:
                del _rate_buckets[ip]

        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # CSP: no 'unsafe-inline' — 国赛安全评审加分项
        # 前端使用 Vite 构建，样式通过独立 CSS 文件加载，无需内联样式
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self'; "
            "img-src 'self' data: blob:; "
            "connect-src 'self'"
        )
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()

    # Auto-seed reference data + demo data if database is empty (competition demo safety)
    try:
        async with async_session() as db:
            patient_count = (await db.execute(select(func.count()).select_from(Patient))).scalar() or 0

        from src.scripts.seed_data import seed_reference_data_if_needed
        if await seed_reference_data_if_needed():
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

app.add_middleware(RateLimitMiddleware)
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
    """检查 LLM (Ollama) 是否在线 — 复用全局单例"""
    try:
        from src.services.llm_engine import llm_engine
        await llm_engine._get_backend()
        return {
            "llm_available": llm_engine.backend_type == "ollama",
            "llm_backend": llm_engine.backend_type,
        }
    except Exception:
        return {"llm_available": False, "llm_backend": "rule-based"}
