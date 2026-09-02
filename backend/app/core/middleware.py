"""Request-scoped middleware: request ID injection and security headers."""

import logging
import os
import time
import uuid
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import request_id_ctx

logger = logging.getLogger("app.middleware")


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Inject a unique X-Request-ID header into every request and store it
    in a context var so it can be accessed anywhere in the call stack."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Only accept a valid UUID4 as the incoming X-Request-ID to prevent
        # log-injection attacks (an attacker could set X-Request-ID: <script>...
        # which would appear in HTML dashboards if accepted verbatim).
        incoming = request.headers.get("X-Request-ID", "")
        try:
            uuid.UUID(incoming)  # raises ValueError if not a valid UUID
            req_id = incoming
        except ValueError:
            req_id = str(uuid.uuid4())

        # Propagate into context vars so all downstream logging is tagged
        token = request_id_ctx.set(req_id)

        # Attach to request state for use in endpoints
        request.state.request_id = req_id

        try:
            response = await call_next(request)
        finally:
            request_id_ctx.reset(token)

        # Always return the request ID so clients can correlate logs
        response.headers["X-Request-ID"] = req_id
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add standard security headers to every response.

    Content-Security-Policy is intentionally lenient here (the app is a SPA
    that makes API calls and renders user-supplied content). Tighten it before
    a public-facing deployment.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Core security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), interest-cohort=()"
        )
        # Remove the "Server: uvicorn" header
        response.headers["Server"] = ""

        # Content-Security-Policy
        # connect-src: allow backend host from VITE_API_URL at runtime (passed via env),
        # plus localhost for dev. Wildcard https://* removed — it bypasses CSP intent
        # by allowing exfiltration to ANY HTTPS domain. In production the backend
        # hostname (backend:8000 in Docker, or the actual deployed URL) must be listed.
        backend_host = os.environ.get("VITE_API_URL", "").rstrip("/")
        connect_src_parts = ["'self'"]
        if backend_host:
            connect_src_parts.append(backend_host)
        # Supabase domain — required for auth API calls from the browser
        connect_src_parts.append("https://eothvqvygmldgygjkfke.supabase.co")
        # Allow localhost for local development (dev server, Ollama on loopback)
        connect_src_parts.append("http://localhost:*")
        connect_src = " ".join(connect_src_parts)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self' data:; "
            f"connect-src {connect_src}; "
            "frame-ancestors 'none';"
        )

        # HSTS (only on HTTPS — check the Forwarded or X-Forwarded-Proto header)
        proto = request.headers.get("X-Forwarded-Proto", "").lower()
        if proto == "https" or request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Structured request/response logging with timing and request ID."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        method = request.method
        path = request.url.path
        start = time.perf_counter()

        logger.info(
            "request_start method=%s path=%s client=%s",
            method, path, request.client.host if request.client else "unknown",
        )

        try:
            response = await call_next(request)
        except Exception as exc:
            duration_s = time.perf_counter() - start
            duration_ms = duration_s * 1000
            logger.exception(
                "request_error method=%s path=%s duration_ms=%.2f error=%s",
                method, path, duration_ms, exc,
            )
            # Record metrics for failed requests
            try:
                from app.core import metrics
                metrics.http_requests_total.inc(method=method, path=path, status="500")
                metrics.http_request_errors_total.inc(method=method, path=path)
                metrics.http_request_duration_seconds.observe(duration_s, method=method, path=path)
            except Exception:
                pass
            raise

        duration_s = time.perf_counter() - start
        duration_ms = duration_s * 1000
        status = response.status_code
        logger.info(
            "request_end method=%s path=%s status=%d duration_ms=%.2f",
            method, path, status, duration_ms,
        )

        # Record metrics (best-effort; never let metrics break a response)
        try:
            from app.core import metrics
            metrics.http_requests_total.inc(method=method, path=path, status=str(status))
            metrics.http_request_duration_seconds.observe(duration_s, method=method, path=path)
            if status >= 400:
                metrics.http_request_errors_total.inc(method=method, path=path, status=str(status))
        except Exception:
            pass

        # Add timing header so clients can observe server-side latency
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"

        return response
