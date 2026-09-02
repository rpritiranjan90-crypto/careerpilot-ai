# Changelog

All notable changes to CareerPilot AI are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Production-ready Docker images (multi-stage builds) for backend and frontend
- Docker Compose for local development and production overrides
- GitHub Actions CI pipeline (lint, type-check, test, build, security audit)
- GitHub Actions CD pipeline (auto-deploy to staging, manual deploy to production)
- Dependabot for automatic dependency updates (Python, npm, Docker, GitHub Actions)
- Pre-commit hooks (ruff, detect-secrets, hadolint, markdownlint)
- Structured JSON logging with request ID propagation
- Prometheus-format `/metrics` endpoint
- Security headers middleware (CSP, HSTS, X-Frame-Options, etc.)
- Health endpoints: `/health` (liveness) and `/health/ready` (readiness)
- Comprehensive documentation: README, DEPLOYMENT, ARCHITECTURE, CONTRIBUTING, SECURITY
- EditorConfig, License (MIT)
- PR and issue templates

### Changed
- Migrated `pyproject.toml` from non-standard JSON to PEP 621
- Frontend `package.json`: added `type: "module"`, ESLint 8 config
- Backend CORS: explicit method list (no wildcards)
- Backend logging: now structured in production

### Security
- Non-root user in Docker containers
- HSTS, CSP, X-Frame-Options, X-Content-Type-Options, Permissions-Policy headers
- detect-secrets pre-commit hook to prevent credential leaks
- pip-audit, npm audit, Trivy scanning in CI

## [1.0.0] - Initial release

### Added
- Resume analysis endpoint with skill extraction and scoring
- Job match endpoint with skill overlap and word frequency scoring
- Mock interview endpoint with 4 question categories and 5-dimension answer evaluation
- File upload endpoint (PDF, DOCX, TXT) with validation and sanitization
- AI provider abstraction (Ollama + deterministic fallback)
- In-memory rate limiting per user per action
- React 18 frontend with 6 pages (Home, Resume, JobMatch, Interview, Dashboard, Settings)
- Client-side deterministic analyzers (work without backend)
- Tailwind CSS design system with custom color palette
- FastAPI auto-generated OpenAPI docs at `/docs` and `/redoc`
- Unit tests for service layer (pytest + Vitest)
