# ---------------------------------------------------------------------------
# Facilities Request Triage – Multi-stage Dockerfile
# Pinned base image; runs as unprivileged user; SQLite writes under /data
# ---------------------------------------------------------------------------
FROM python:3.11.9-slim AS base

# ---------------------------------------------------------------------------
# System deps (minimal)
# ---------------------------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
    && rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------------------------
# Non-root user
# ---------------------------------------------------------------------------
RUN useradd --create-home --shell /bin/bash app

# ---------------------------------------------------------------------------
# Working directory
# ---------------------------------------------------------------------------
WORKDIR /app

# ---------------------------------------------------------------------------
# Copy and install pinned Python dependencies first (layer caching)
# ---------------------------------------------------------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---------------------------------------------------------------------------
# Copy application source (no tests, no .env, no local DB)
# ---------------------------------------------------------------------------
COPY facilities/ ./facilities/
COPY streamlit_app.py .
COPY scenarios/ ./scenarios/

# ---------------------------------------------------------------------------
# Data volume – SQLite is written here
# ---------------------------------------------------------------------------
RUN mkdir -p /data && chown app:app /data
VOLUME ["/data"]

# ---------------------------------------------------------------------------
# Switch to non-root
# ---------------------------------------------------------------------------
USER app

# ---------------------------------------------------------------------------
# Default environment (overridden by Terraform / docker run)
# ---------------------------------------------------------------------------
ENV DATABASE_PATH=/data/facilities.db \
    PROVIDER_MODE=lmstudio

# ---------------------------------------------------------------------------
# Expose API port (Streamlit has its own port, controlled by startup cmd)
# ---------------------------------------------------------------------------
EXPOSE 8000

# ---------------------------------------------------------------------------
# Default: run FastAPI API
# Override with: docker run ... streamlit run streamlit_app.py --server.port 8502 --server.address 0.0.0.0
# ---------------------------------------------------------------------------
CMD ["uvicorn", "facilities.api:app", "--host", "0.0.0.0", "--port", "8000"]
