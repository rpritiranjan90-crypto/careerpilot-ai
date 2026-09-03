# CareerPilot AI - Backend Dockerfile
# Multi-stage build: builder compiles wheels, runtime is ultra-slim, non-root, and zero-OS-dep.

# ---------- Builder ----------
FROM python:3.11-slim AS builder

WORKDIR /app

# Install deps first (better layer caching)
COPY backend/pyproject.toml ./pyproject.toml

# Extract dependency list from PEP 621 pyproject.toml using standard library tomllib
RUN python -c "import tomllib; reqs = tomllib.load(open('pyproject.toml', 'rb'))['project']['dependencies']; open('/tmp/reqs.txt', 'w').write('\n'.join(reqs))"

RUN pip install --no-cache-dir --upgrade pip \
    && pip wheel --no-cache-dir --wheel-dir /wheels -r /tmp/reqs.txt


# ---------- Runtime ----------
FROM python:3.11-slim AS runtime

# Non-root user for security
RUN groupadd --system --gid 1000 appgroup \
    && useradd --system --uid 1000 --gid appgroup --create-home --shell /bin/false appuser

WORKDIR /app

# Install Python packages from cached wheels (psycopg2-binary provides self-contained wheels)
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir --no-index --find-links=/wheels /wheels/*.whl \
    && rm -rf /wheels

# Copy application source and configuration (build context is repo root)
COPY --chown=appuser:appgroup backend/app ./app
COPY --chown=appuser:appgroup backend/alembic ./alembic
COPY --chown=appuser:appgroup backend/alembic.ini ./alembic.ini
COPY --chown=appuser:appgroup backend/.env.example ./.env.example

# Create upload directory and set ownership
RUN mkdir -p /app/uploads && chown -R appuser:appgroup /app

USER appuser

# Backend URL injected at build time (production)
ARG VITE_API_URL
ENV VITE_API_URL=${VITE_API_URL:-}

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    ENVIRONMENT=production \
    PORT=8000

EXPOSE 8000

# Healthcheck uses Python standard library urllib (zero external OS binary dependencies)
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')" || exit 1

# uvicorn with proxy headers so X-Forwarded-* from Nginx works
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips=*"]
