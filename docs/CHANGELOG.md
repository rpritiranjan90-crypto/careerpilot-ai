# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Real PostgreSQL persistence via SQLAlchemy 2.0 + Alembic migrations
- Supabase JWT authentication (HS256) replacing mock auth
- Ownership-based authorization on every endpoint
- Magic-byte file validation (defense-in-depth on uploads)
- Standardized error envelope: `{"error": {"code", "message", "request_id"}}`
- Real `/health/ready` probe checking DB + AI provider
- Prometheus-format `/metrics` endpoint
- Structured JSON logging in production with per-request `request_id` correlation
- Security headers middleware (CSP, HSTS, X-Frame-Options, etc.)
- Frontend wired to real backend APIs (no more hardcoded client-side scoring)
- `GET_OR_CREATE_USER` pattern ensures FK targets always exist
- Backup and restore documentation
- CI workflow with backend, frontend, Docker, and security audit jobs
- CD workflow publishing images to GHCR and deploying via SSH

### Changed
- Replaced `datetime.utcnow` with `datetime.now(timezone.utc)` throughout
- Replaced deprecated `@app.on_event("startup")` with `lifespan` context manager
- `OllamaProvider` now actually calls Ollama with JSON prompt/response (was always falling through to fallback)
- Alembic migration runs automatically on backend startup
- Backend Dockerfile now uses non-root user, multi-stage build, and includes `curl` for healthchecks
- `docker-compose.yml` now includes a PostgreSQL service and `DEV_TOKEN_AUTH` default
- Frontend `api.ts` adds Bearer-token auth header and `FormData` upload support

### Removed
- Duplicated `calculate_match` / `start_interview` / `evaluate_answer` (kept single source per service)
- Client-side `performClientAnalysis`, `calculateMatchClient`, `evaluateAnswerClient` from frontend

## [0.1.0] - Initial release

- Initial scaffolding with FastAPI backend, React/Vite frontend
- Deterministic resume analysis, job matching, and mock interview
- Optional Ollama local AI integration
- Docker Compose development environment
- Pre-commit hooks (ruff, detect-secrets, hadolint, markdownlint)
- CI workflow
