# Observability Guide

This document covers metrics, logging, and alerting for CareerPilot AI.

---

## Metrics

The backend exposes Prometheus-compatible metrics at `GET /metrics`.

Metrics are implemented without external dependencies (pure Python) so the image
remains lean. Any Prometheus-compatible scraper can ingest them.

### Available Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `http_requests_total` | Counter | `method`, `path`, `status` | Total HTTP requests |
| `http_request_duration_seconds` | Histogram | `method`, `path` | Request latency distribution |
| `http_request_errors_total` | Counter | `method`, `path`, `status` | Requests with 4xx/5xx status |
| `process_uptime_seconds` | Gauge | — | Process uptime |

### Prometheus Scrape Config

```yaml
# prometheus.yml
scrape_configs:
  - job_name: "careerpilot-backend"
    static_configs:
      - targets: ["careerpilot-backend:8000"]
    metrics_path: "/metrics"
    scrape_interval: 15s
```

---

## Logging

Production logs are emitted as structured key=value lines:

```
timestamp=2026-09-01T12:00:00 level=INFO name=app.middleware request_id=abc-123 message="request_end method=POST path=/api/resumes/analyze status=200 duration_ms=45.32"
```

Dev logs are human-readable:

```
2026-09-01 12:00:00 | INFO     | app.middleware | request_end method=POST path=/api/resumes/analyze status=200
```

### Log Levels

| Environment | Default Level | Notes |
|-------------|--------------|-------|
| Development | DEBUG | Verbose, all requests |
| Production | INFO | Normal operation |
| Production + LOG_LEVEL=DEBUG | DEBUG | Temporary troubleshooting only |

### Correlating Logs with Traces

Every log line includes `request_id=<uuid>`. Pass `X-Request-ID: <uuid>` in a
request header to set it; otherwise a UUID4 is generated automatically.

---

## Alerting

Prometheus alerting rules for this service:

```yaml
# alerts.yml
groups:
  - name: careerpilot
    rules:
      # High error rate
      - alert: HighErrorRate
        expr: |
          (
            sum(rate(http_request_errors_total[5m]))
            /
            sum(rate(http_requests_total[5m]))
          ) > 0.05
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High error rate on CareerPilot API (>5%)"

      # Backend down
      - alert: BackendDown
        expr: up{job="careerpilot-backend"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "CareerPilot backend is unreachable"

      # High latency
      - alert: HighLatency
        expr: |
          histogram_quantile(0.95,
            sum(rate(http_request_duration_seconds_bucket[5m])) by (le)
          ) > 2.0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "P95 latency > 2s on CareerPilot API"

      # Rate limit pressure
      - alert: RateLimitPressure
        expr: |
          sum(rate(http_request_errors_total{status="429"}[15m])) > 5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Significant rate-limit pressure on CareerPilot"
```

---

## Grafana Dashboard Panels

Suggested panels for a CareerPilot dashboard:

1. **Request Rate** – `sum(rate(http_requests_total[1m])) by (method)`
2. **Error Rate** – `sum(rate(http_request_errors_total[5m])) by (status)`
3. **P50/P95/P99 Latency** – `histogram_quantile(0.5/0.95/0.99, rate(http_request_duration_seconds_bucket[5m]))`
4. **Uptime** – `process_uptime_seconds`
5. **HTTP Status Breakdown** – `sum(rate(http_requests_total[5m])) by (status)`

---

## Health Endpoints

| Endpoint | Auth | Description |
|----------|------|-------------|
| `GET /health` | None | Returns `{"status": "ok", "request_id": "…"}` |
| `GET /health/ready` | None | Returns `{"checks": {"api": "ok", ...}}` — check DB connectivity |
| `GET /metrics` | None | Prometheus metrics (intentionally public) |

For production, consider adding basic auth or IP allowlisting to `/metrics` if
it contains sensitive volume data.
