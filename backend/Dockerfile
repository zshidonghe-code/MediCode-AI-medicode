FROM python:3.12-slim

WORKDIR /app

# Install only what's needed for Python packages with C extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && apt-get purge -y gcc \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# Copy source code
COPY . .

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
