# Architecture

System design and architectural decisions for CareerPilot AI.

## Goals

1. **Free-first** — all core features work without paid API keys
2. **Privacy-preserving** — user data processed locally when possible
3. **Production-ready** — observable, secure, scalable
4. **Contributor-friendly** — clear structure, easy local dev

## High-level components

```
┌───────────────────────────────────────────────────────────────┐
│  CLIENT  (React 18 + TypeScript SPA)                          │
│  ──────────────────────────────────────────────────────────   │
│  • Pages: Home, Resume, JobMatch, Interview, Dashboard, …     │
│  • Services: API client (src/services/api.ts)                 │
│  • State: local component state (useState/useRef)             │
│  • Build: Vite → static assets served by Nginx                │
└────────────────────┬──────────────────────────────────────────┘
                     │ HTTPS (CORS, JWT)
                     ▼
┌───────────────────────────────────────────────────────────────┐
│  NGINX  (production reverse proxy)                            │
│  ──────────────────────────────────────────────────────────   │
│  • Serves React SPA from /usr/share/nginx/html                │
│  • Proxies /api/* → backend:8000                              │
│  • Adds security headers (CSP, HSTS, X-Frame-Options, …)      │
│  • Gzip + long-cache for /assets/, no-cache for index.html    │
└────────────────────┬──────────────────────────────────────────┘
                     │ HTTP (internal network)
                     ▼
┌───────────────────────────────────────────────────────────────┐
│  BACKEND  (FastAPI on Uvicorn, Python 3.11)                   │
│  ──────────────────────────────────────────────────────────   │
│  • Middleware stack:                                           │
│     1. RequestIdMiddleware (UUID per request, propagates)      │
│     2. SecurityHeadersMiddleware (CSP, HSTS, X-Frame-Options) │
│     3. RequestLoggingMiddleware (structured logs, metrics)     │
│     4. CORSMiddleware (origin allowlist)                      │
│  • API layer: upload, analysis, job_match, interview          │
│  • Service layer: deterministic business logic                │
│  • AI abstraction: OllamaProvider → FallbackAIProvider         │
│  • Rate limiting: in-memory per-user per-action                │
│  • Auth: Supabase JWT (mock for now, see Auth section)         │
└────────────────────┬──────────────────────────────────────────┘
                     │ SQL (port 5432)
                     ▼
┌───────────────────────────────────────────────────────────────┐
│  DATABASE  (PostgreSQL 16 via Supabase OR self-hosted)        │
│  ──────────────────────────────────────────────────────────   │
│  Tables: users, resumes, resume_analyses,                     │
│          job_descriptions, job_matches,                       │
│          interviews, interview_questions                      │
└───────────────────────────────────────────────────────────────┘
```

## Layered design (backend)

```
┌─────────────────────────────────────────────────────────────┐
│  API layer (app/api/)                                       │
│  ────────────────────────────────────────────────────────── │
│  • FastAPI route handlers                                    │
│  • Request/response validation via Pydantic schemas          │
│  • Authentication dependency injection                       │
│  • Rate limiting + input validation                          │
│  • Thin: delegates to services                               │
└────────────────────┬────────────────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Service layer (app/services/)                              │
│  ────────────────────────────────────────────────────────── │
│  • Business logic (resume parsing, scoring, matching)         │
│  • Pure functions where possible (no side effects)           │
│  • Easily unit-testable                                      │
│  • Returns plain dicts / Pydantic models                     │
└────────────────────┬────────────────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Data layer (app/models/, app/core/database.py)             │
│  ────────────────────────────────────────────────────────── │
│  • SQLAlchemy 2.0 ORM models + Alembic migrations            │
│  • Session management via FastAPI Depends(get_db)           │
│  • Foreign-key cascade deletions & GDPR Article 17 erasure   │
└─────────────────────────────────────────────────────────────┘
```

## Data model

```
User ─┬─ Resume ─── ResumeAnalysis
      │     │
      │     └─ JobDescription ─── JobMatch
      │
      └─ Interview ─── InterviewQuestion
```

All entities use UUID string primary keys. Timestamps are UTC.

## AI provider abstraction

The AI layer is intentionally pluggable:

```python
class AIProvider(ABC):
    async def analyze_resume(self, text: str) -> dict: ...
    async def match_job(self, resume: str, jd: str) -> dict: ...
    async def generate_question(self, interview_type: str) -> str: ...
    async def evaluate_answer(self, q: str, a: str) -> dict: ...
```

Two implementations:

- **`OllamaProvider`** — talks to a local Ollama instance. Privacy-preserving, free, no API keys.
- **`FallbackAIProvider`** — deterministic rule-based analyzer. Always works, zero dependencies.

The backend picks `OllamaProvider` when `OLLAMA_BASE_URL` is reachable, otherwise falls through to `FallbackAIProvider` transparently with cached probing. **The user never sees an error** when AI is unavailable.

## Authentication & Authorization

Authentication is enforced via cryptographic JWT verification with development-mode fallback:

1. **Production mode (`ENVIRONMENT=production`)**:
   - Requires valid `SUPABASE_JWT_SECRET`.
   - Validates cryptographic signature via `PyJWT` (HS256).
   - Validates `exp` expiration, `sub` subject claim, `aud="authenticated"` audience, and optional `iss` issuer claim.
   - Rejects unverified or expired tokens with `401 Unauthorized`.
   - Rejects IDOR cross-tenant access attempts with `403 Forbidden` / `404 Not Found`.

2. **Development mode (`DEV_TOKEN_AUTH=true`)**:
   - Allows local developer tokens for friction-free testing while preserving full authorization checks and user separation.

## Rate Limiting & Deployment Architecture

1. **Single-Instance Deployment (Current & Default)**:
   - Utilizes `InMemoryRateLimiter` with `threading.Lock` thread-safety.
   - Employs `time.monotonic()` to guarantee immunity from system clock adjustments and NTP skews.
   - Sliding-window timestamp pruning with automatic inline GC sweeps to prevent memory leaks.
   - Configurable per-user per-action limits (e.g., upload, analyze, interview) returning `429 Too Many Requests` and `Retry-After` headers.

2. **Multi-Node Horizontal Scaling (Optional / Future)**:
   - For deployments spanning multiple container instances behind a round-robin load balancer, the in-memory backend can be seamlessly swapped for Redis via `redis-py` using the exact same `RateLimitConfig` interface.

## Security layers

1. **Transport** — TLS termination at the load balancer; HSTS header in responses
2. **Headers** — CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy
3. **CORS** — explicit origin allowlist (no wildcards in production)
4. **Input validation** — Pydantic schemas for every request body
5. **File uploads** — extension allowlist, MIME type check, 5MB size cap, filename sanitization, null byte detection
6. **Auth** — bearer token required on all `/api/*` routes (except `/health`, `/metrics`)
7. **Rate limiting** — per-user, per-action limits with `Retry-After` headers
8. **GDPR Erasure** — Article 17 endpoint permanently deleting DB records and unlinking disk storage
9. **Secrets** — environment variables only; production validation guards prevent unsafe configs
10. **Container** — non-root user, minimal base image, multi-stage build

## Observability

### Logs

- **Development** — human-readable, colored
- **Production** — structured `key=value` lines, one per log event
- Every line includes a `request_id` for end-to-end tracing

### Metrics

Built-in Prometheus-compatible `/metrics` endpoint with:

- `http_requests_total{method,path,status}` — counter
- `http_request_duration_seconds{method,path}` — histogram
- `http_request_errors_total{method,path,status}` — counter
- `process_uptime_seconds` — gauge

No external dependencies (no `prometheus_client` library required).

### Health checks

- `/health` — liveness (process is up)
- `/health/ready` — readiness (DB, Ollama are reachable)

## Deployment topology

See [DEPLOYMENT.md](DEPLOYMENT.md) for the full deployment guide. In summary:

- **Single VPS** — Docker Compose, simplest setup
- **Managed runtime** — push images to GHCR, deploy to ECS/Cloud Run/etc.
- **Kubernetes** — full HA setup with HPA, PDB, etc.

## Free-tier philosophy

Every architectural decision prioritizes:

1. **No paid APIs** — Ollama instead of OpenAI/Anthropic
2. **No vendor lock-in** — works with any Postgres, any LLM that speaks Ollama API
3. **Minimal cloud deps** — Supabase is optional, can be replaced with local Postgres
4. **Self-hostable** — the entire stack runs on a $5/month VPS

When a feature requires a trade-off (e.g., a hosted email service), the team prefers the option that keeps the free tier usable.
