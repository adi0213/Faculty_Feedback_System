# EduPulse AI — Backend Dockerfile (root level for Render deployment)
# Build context is the repo root; backend source is in edupulse-backend-v2/

FROM python:3.12-slim AS builder

# System dependencies for C extensions (psycopg2, scipy, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY edupulse-backend-v2/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ── Production image ──────────────────────────────────────────────────────────
FROM python:3.12-slim AS production

# Non-root user for security
RUN useradd --create-home --shell /bin/bash edupulse

# Runtime system libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy backend application code
COPY --chown=edupulse:edupulse edupulse-backend-v2/ .

# Pre-create writable directories as edupulse user
RUN mkdir -p uploads/certificates /tmp/edupulse/uploads/certificates \
    && chown -R edupulse:edupulse /app /tmp/edupulse

USER edupulse

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Startup — $PORT is set by Render automatically
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
