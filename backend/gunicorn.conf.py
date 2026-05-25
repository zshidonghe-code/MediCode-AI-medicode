"""
Gunicorn configuration for MediCode backend production deployment.
Usage: gunicorn -c gunicorn.conf.py src.main:app
"""

import multiprocessing
import os

# ---- Server Socket ----
bind = "0.0.0.0:8000"
backlog = 2048

# ---- Worker Processes ----
workers = int(os.getenv("GUNICORN_WORKERS", min(4, multiprocessing.cpu_count() * 2 + 1)))
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 10000
max_requests_jitter = 1000
timeout = int(os.getenv("GUNICORN_TIMEOUT", "120"))
graceful_timeout = 30
keepalive = 5

# ---- Process Naming ----
proc_name = "medicode-backend"

# ---- Logging ----
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info")
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# ---- Server Mechanics ----
daemon = False
pidfile = None
user = None
group = None
umask = 0
tmp_upload_dir = None

# ---- SSL (disabled by default, use a reverse proxy for TLS) ----
keyfile = None
certfile = None
