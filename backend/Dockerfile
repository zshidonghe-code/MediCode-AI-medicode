# =============================================================================
# MediCode Backend Dockerfile
# Python 3.12 + FastAPI + Gunicorn/Uvicorn
# Supports both SQLite (dev) and PostgreSQL (prod) via DATABASE_URL
# =============================================================================

# ---- Build Stage ----
FROM python:3.12-slim AS builder

WORKDIR /app

# Install build dependencies for packages with C extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libc-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency manifests first for layer caching
COPY requirements.txt .

# Install dependencies into a wheels directory for the final stage
RUN pip install --no-cache-dir --upgrade pip \
    && pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# ---- Production Stage ----
FROM python:3.12-slim

# Create non-root user
RUN groupadd -r medicode && useradd -r -g medicode medicode

WORKDIR /app

# Install runtime system dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /app/data \
    && chown -R medicode:medicode /app

# Copy pre-built wheels and install
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir --no-deps /wheels/*.whl && rm -rf /wheels

# Copy application source
COPY --chown=medicode:medicode . .

# Create data directory
RUN mkdir -p /app/data && chown medicode:medicode /app/data

# Switch to non-root user
USER medicode

EXPOSE 8000

# Health check: verify the /health endpoint responds
HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -sf http://localhost:8000/health || exit 1

# Default: uvicorn for direct use; override with gunicorn in production compose
CMD ["gunicorn", "src.main:app", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "1", \
     "--timeout", "120", \
     "--graceful-timeout", "30", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
