"""CareerPilot AI - FastAPI application entrypoint."""

import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api import api_router
from app.api.metrics import router as metrics_router
from app.core.config import settings
from app.core.database import get_engine
from app.core.logging import get_request_id, setup_logging
from app.core.sentry import init_sentry

setup_logging()
init_sentry()
logger = logging.getLogger("app.startup")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events via lifespan context manager.

    Note: Database migrations are intentionally NOT run here. They should
    be executed as a separate deploy step (CI/CD or init container) to
    avoid race conditions when multiple instances start concurrently.
    """
    logger.info("Application starting (environment=%s)", settings.environment)

    if settings.database_url:
        engine = get_engine()
        if engine is not None:
            try:
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                from app.core.database import Base
                import app.models  # noqa: F401
                Base.metadata.create_all(bind=engine)
                logger.info("Database connection and schema verified")
            except Exception as exc:
                logger.error("Database connection check failed: %s", exc)
    else:
        logger.info("No DATABASE_URL set - running without database (demo mode)")

    yield

    logger.info("Application shutting down")


app = FastAPI(
    title="CareerPilot AI API",
    description="AI-powered career preparation platform API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Middleware imports placed after app construction (uses # noqa: E402)
from app.core.middleware import (  # noqa: E402
    RequestIdMiddleware,
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware,
)

app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestIdMiddleware)


# ---------------------------------------------------------------------------
# Standardized error envelope
# All errors returned as { "error": { "code": ..., "message": ..., "request_id": ... } }
# ---------------------------------------------------------------------------


def _error_payload(code: str, message: str, details: Any = None) -> dict:
    body: dict[str, Any] = {
        "error": {
            "code": code,
            "message": message,
            "request_id": get_request_id(),
        }
    }
    if details is not None:
        body["error"]["details"] = details
    return body


@app.exception_handler(HTTPException)
async def _http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTPException and APIError with standard error envelope."""
    code_map = {
        status.HTTP_400_BAD_REQUEST: "bad_request",
        status.HTTP_401_UNAUTHORIZED: "unauthorized",
        status.HTTP_403_FORBIDDEN: "forbidden",
        status.HTTP_404_NOT_FOUND: "not_found",
        status.HTTP_413_REQUEST_ENTITY_TOO_LARGE: "payload_too_large",
        status.HTTP_422_UNPROCESSABLE_ENTITY: "validation_error",
        status.HTTP_429_TOO_MANY_REQUESTS: "rate_limited",
        status.HTTP_500_INTERNAL_SERVER_ERROR: "internal_error",
    }
    code = getattr(exc, "code", code_map.get(exc.status_code, "http_error"))
    message = getattr(exc, "message", exc.detail if isinstance(exc.detail, str) else str(exc.detail))
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_payload(
            code=code,
            message=message,
        ),
        headers=exc.headers,
    )


@app.exception_handler(RequestValidationError)
async def _validation_handler(request: Request, exc: RequestValidationError):
    """422 with a clean envelope (Pydantic validation errors)."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=_error_payload(
            code="validation_error",
            message="Invalid request payload",
            details=exc.errors(),
        ),
    )


@app.exception_handler(Exception)
async def _unhandled_exception_handler(request: Request, exc: Exception):
    """Last-resort handler for anything that escapes a route.

    Logs the full traceback and returns a clean 500 to the client
    (no internal details leaked).
    """
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=_error_payload(
            code="internal_error",
            message="An internal error occurred",
        ),
    )


app.include_router(api_router, prefix="/api")
app.include_router(metrics_router)


@app.get("/health", tags=["health"])
async def health_check() -> dict:
    return {
        "status": "ok",
        "version": "1.0.0",
        "request_id": get_request_id(),
    }


@app.get("/health/ready", tags=["health"])
async def readiness_check() -> dict:
    """Readiness probe — checks every external dependency."""
    checks: dict[str, str] = {"api": "ok"}

    # Database
    if settings.database_url:
        try:
            engine = get_engine()
            if engine is not None:
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                checks["database"] = "ok"
            else:
                checks["database"] = "not configured"
        except Exception as exc:
            checks["database"] = f"error: {exc}"

    # Ollama (best-effort; AI is not strictly required for readiness)
    try:
        import httpx
        with httpx.Client(timeout=2.0) as client:
            resp = client.get(f"{settings.ollama_base_url}/api/tags")
        checks["ai"] = "ok" if resp.status_code == 200 else f"http {resp.status_code}"
    except Exception as exc:
        checks["ai"] = f"unavailable: {type(exc).__name__}"

    all_ok = all(v == "ok" for v in checks.values())
    return {
        "status": "ready" if all_ok else "degraded",
        "version": "1.0.0",
        "checks": checks,
        "request_id": get_request_id(),
    }


@app.get("/", tags=["root"])
async def root() -> dict:
    return {
        "name": "CareerPilot AI API",
        "version": "1.0.0",
        "docs": "/docs",
        "environment": settings.environment,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
