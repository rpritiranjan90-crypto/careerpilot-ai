"""Sentry error tracking initialization for the FastAPI app."""

import os

from sentry_sdk import init as sentry_init
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration


def init_sentry() -> None:
    """Initialize Sentry error tracking.

    Reads DSN from the SENTRY_DSN env var (sync:false in Render).
    If no DSN is set, Sentry is silently skipped (dev/local mode).
    """
    dsn = os.environ.get("SENTRY_DSN")
    if not dsn:
        return  # no DSN → skip initialization

    sentry_init(
        dsn=dsn,
        integrations=[
            FastApiIntegration(),
            SqlalchemyIntegration(),
        ],
        environment=os.environ.get("ENVIRONMENT", "development"),
        # Performance monitoring
        enable_tracing=True,
        traces_sample_rate=0.2,
    )