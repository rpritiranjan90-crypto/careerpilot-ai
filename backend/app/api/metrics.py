"""Prometheus metrics endpoint."""

from fastapi import APIRouter, Response

from app.core.metrics import render_prometheus_metrics

router = APIRouter(tags=["observability"])


@router.get("/metrics", include_in_schema=False)
async def metrics() -> Response:
    """Prometheus-format metrics endpoint.

    Exposed for scraping by Prometheus, Grafana Cloud Agent, VictoriaMetrics, …
    No auth required for /metrics – make sure this route is not exposed to
    the public internet (use a private network, ingress allowlist, or basic auth).
    """
    return Response(
        content=render_prometheus_metrics(),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )
