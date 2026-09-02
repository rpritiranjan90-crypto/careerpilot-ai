"""Structured application logging configuration.

In production, logs are emitted as structured key=value lines so they can be
indexed by any log aggregator (Datadog, CloudWatch, Loki, …).
"""

import logging
import os
import sys
import uuid
from contextvars import ContextVar

# Per-request request ID (set by middleware, available anywhere in the call stack).
request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)


class StructuredFormatter(logging.Formatter):
    """Formats log records as: timestamp level=LEVEL name=name request_id=… message=MSG [extra_kv …]"""

    def format(self, record: logging.LogRecord) -> str:
        parts = [
            f"timestamp={self.formatTime(record, self.datefmt or '%Y-%m-%dT%H:%M:%S')}",
            f"level={record.levelname}",
            f"name={record.name}",
        ]

        # Request ID (may be absent for startup / background logs)
        req_id = request_id_ctx.get()
        if req_id:
            parts.append(f"request_id={req_id}")

        # Structured extra fields (anything passed as extra= in logger calls)
        for key, value in record.__dict__.items():
            if key not in {"name", "msg", "args", "created", "filename", "funcName",
                           "levelname", "levelno", "lineno", "module", "msecs",
                           "pathname", "process", "processName", "thread",
                           "threadName", "exc_info", "exc_text", "stack_info",
                           "message", "request_id"}:
                parts.append(f"{key}={value!r}")

        parts.append(f"message={record.getMessage()}")

        # Include exception info if present
        if record.exc_info:
            parts.append(f"exception={self.formatException(record.exc_info)}")

        return " ".join(parts)


def setup_logging() -> None:
    """Configure application logging based on the ENVIRONMENT variable."""
    is_production = os.getenv("ENVIRONMENT", "development") == "production"

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if not is_production else logging.INFO)

    # Remove any pre-existing handlers
    for h in root_logger.handlers[:]:
        root_logger.removeHandler(h)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)

    if is_production:
        # Structured machine-readable format
        handler.setFormatter(StructuredFormatter())
        # Only emit DEBUG in production when explicitly enabled
        if os.getenv("LOG_LEVEL", "").upper() != "DEBUG":
            handler.setLevel(logging.INFO)
    else:
        # Human-readable dev format
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )

    root_logger.addHandler(handler)

    # Silence noisy third-party loggers
    for noisy in ["uvicorn", "uvicorn.access", "uvicorn.error",
                   "httpx", "httpcore", "sqlalchemy.engine"]:
        logging.getLogger(noisy).setLevel(
            logging.WARNING if is_production else logging.INFO
        )
        # Suppress uvicorn access logs entirely in production
        if is_production and noisy == "uvicorn.access":
            logging.getLogger(noisy).setLevel(logging.CRITICAL)

    logging.getLogger("app").info(
        "Logging initialized (production=%s, log_level=%s)",
        is_production,
        os.getenv("LOG_LEVEL", "INFO"),
    )


def generate_request_id() -> str:
    """Return a new UUID4 request ID string."""
    return str(uuid.uuid4())


def get_request_id() -> str | None:
    """Return the current request ID from context, or None."""
    return request_id_ctx.get()


class RequestIdFilter(logging.Filter):
    """Inject request_id from context vars into every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx.get() or ""
        return True
