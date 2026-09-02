# CareerPilot AI

> **Prepare smarter. Get career-ready.**

[![CI](https://github.com/your-org/career-pilot-ai/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/your-org/career-pilot-ai/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![React 18](https://img.shields.io/badge/React-18-61dafb.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.5-blue.svg)](https://www.typescriptlang.org/)

CareerPilot AI is a free-first, privacy-preserving AI-powered career preparation platform that helps you:

- 📄 **Analyze your resume** — upload or paste and get actionable feedback
- 🔍 **Match against job descriptions** — see how your skills stack up
- 📚 **Identify skill gaps** — know exactly what to develop
- 🎙️ **Practice mock interviews** — get instant AI feedback
- 📊 **Track career readiness** — see your overall progress

All core features work **without any paid API keys** using local rule-based analysis. Optional AI enhancement via [Ollama](https://ollama.ai) (completely free and runs on your own machine).

---

## Table of Contents

- [Quick Start](#quick-start)
  - [Prerequisites](#prerequisites)
  - [Local Development](#local-development)
  - [Docker (one command)](#docker-one-command)
- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [API Reference](#api-reference)
- [Development](#development)
  - [Running Tests](#running-tests)
  - [Type Checking](#type-checking)
  - [Linting](#linting)
  - [Pre-commit Hooks](#pre-commit-hooks)
- [Deployment](#deployment)
  - [Docker Compose (staging)](#docker-compose-staging)
  - [Docker Compose (production)](#docker-compose-production)
  - [CI/CD](#cicd)
- [Backups](#backups)
- [Free Tier Limitations](#free-tier-limitations)
- [Optional: Enable Local AI](#optional-enable-local-ai)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [Security](#security)
- [License](#license)

---

## Quick Start

### Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Node.js | 18+ | [nodejs.org](https://nodejs.org) |
| Python | 3.10+ | [python.org](https://www.python.org) |
| pip | latest | `pip install -U pip` |
| Docker | 24+ | [docker.com](https://docs.docker.com/get-docker/) |
| Docker Compose | 2+ | included with Docker Desktop |

### Local Development

**1. Clone & install dependencies**

```bash
git clone https://github.com/your-org/career-pilot-ai.git
cd career-pilot-ai

# Frontend
cd frontend
npm install

# Backend
cd ../backend
pip install -e ".[dev]"
```

**2. Configure environment**

```bash
# Backend
cp backend/.env.example backend/.env
# Edit backend/.env with your settings (Supabase, Ollama, etc.)

# Frontend
cp frontend/.env.example frontend/.env
```

**3. Run**

```bash
# Terminal 1 – Backend (FastAPI, http://localhost:8000)
cd backend
uvicorn app.main:app --reload --port 8000

# Terminal 2 – Frontend (Vite, http://localhost:3000)
cd frontend
npm run dev
```

**4. Open** [http://localhost:3000](http://localhost:3000)

### Docker (one command)

```bash
cp .env.example .env
docker compose up --build
```

App is live at **http://localhost:3000** (frontend) and **http://localhost:8000** (backend API).

---

## Features

| Feature | Description | Free Tier |
|---------|-------------|-----------|
| Resume Analysis | Upload PDF/DOCX/TXT or paste text → skill extraction + scoring | ✅ Unlimited |
| Job Match | Compare your skills against any job description | ✅ Unlimited |
| Skill Gap | Identify missing skills and get recommendations | ✅ Unlimited |
| Mock Interview | Practice 4 interview types with instant feedback | ✅ Unlimited |
| Career Readiness | Dashboard showing overall career readiness score | ✅ Unlimited |
| AI Insights | Enhanced analysis via local Ollama (no API costs) | ✅ Free (local) |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CareerPilot AI                            │
│                                                                 │
│  ┌──────────────┐      ┌─────────────────┐      ┌──────────┐  │
│  │   Browser    │ ──── │  Nginx (prod)   │ ──── │ FastAPI  │  │
│  │  React SPA   │      │  reverse proxy  │      │ Backend  │  │
│  │ :3000 / :80  │      │                 │      │ :8000    │  │
│  └──────────────┘      └─────────────────┘      └────┬─────┘  │
│                                                        │         │
│                               ┌────────────────────────┼─────┐   │
│                               │                        │     │   │
│                         ┌─────▼──────┐          ┌─────▼────┐ │   │
│                         │ PostgreSQL │          │ Ollama   │ │   │
│                         │ (Supabase) │          │ (local)  │ │   │
│                         │            │          │  :11434  │ │   │
│                         └────────────┘          └──────────┘ │   │
│                                                          ↑     │
│                              ┌──────────────────────────┘     │
│                              │                                 │
│                     ┌────────▼────────┐                        │
│                     │  File Storage  │                        │
│                     │   (uploads/)    │                        │
│                     └─────────────────┘                        │
└─────────────────────────────────────────────────────────────────┘
```

- **Frontend** – React 18 + TypeScript + Vite + Tailwind CSS SPA
- **Backend** – FastAPI (Python 3.10+) REST API with Pydantic validation
- **Database** – PostgreSQL 16 (Supabase or self-hosted) with Alembic migrations
- **Auth** – Supabase JWT (HS256); development fallback `DEV_TOKEN_AUTH=true`
- **AI** – Ollama (local, free) with deterministic fallback when Ollama is unavailable
- **Containerization** – Docker + Docker Compose with multi-stage builds
- **Observability** – Structured JSON logs, request_id correlation, `/metrics` endpoint
- **Security** – Ownership-based authorization, magic-byte file validation, security headers, no service-role keys in the frontend

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | React 18, TypeScript 5, Vite 5, Tailwind CSS 3, React Router 6, Vitest |
| **Backend** | Python 3.10+, FastAPI 0.110, Pydantic 2, Uvicorn, SQLAlchemy 2 |
| **Database** | PostgreSQL 16 (Supabase or self-hosted) |
| **Auth** | Supabase Auth (JWT) |
| **AI** | Ollama (local LLM) with rule-based fallback |
| **Containerization** | Docker, Docker Compose, multi-stage builds |
| **CI/CD** | GitHub Actions |
| **Tooling** | ruff, black, mypy, ESLint, Pre-commit |

---

## API Reference

Interactive docs available at [http://localhost:8000/docs](http://localhost:8000/docs) (Swagger UI) or [http://localhost:8000/redoc](http://localhost:8000/redoc) (ReDoc).

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Liveness check |
| `GET` | `/health/ready` | Readiness check with dependency status |
| `GET` | `/metrics` | Prometheus-format metrics |
| `POST` | `/api/resumes/upload` | Upload a resume file (PDF, DOCX, TXT, max 5 MB) |
| `GET` | `/api/resumes/{id}` | Get resume metadata |
| `DELETE` | `/api/resumes/{id}` | Delete a resume |
| `POST` | `/api/resumes/analyze` | Analyze resume text and return structured feedback |
| `GET` | `/api/resumes/{id}/analysis` | Retrieve a prior resume analysis |
| `POST` | `/api/job-matches` | Calculate match score between resume skills and job description |
| `GET` | `/api/job-matches/{id}` | Retrieve a prior job match result |
| `POST` | `/api/interviews` | Start a new mock interview session |
| `POST` | `/api/interviews/{id}/answers` | Submit an interview answer for evaluation |
| `GET` | `/api/interviews/{id}` | Retrieve an interview session |

---

## Development

### Running Tests

```bash
# Backend
cd backend
pytest -v

# Frontend
cd frontend
npm run test        # run once
npm run test:watch  # watch mode
```

### Type Checking

```bash
# Backend
cd backend
mypy app

# Frontend
cd frontend
npm run typecheck
```

### Linting

```bash
# Backend
cd backend
ruff check app tests
black --check app tests

# Frontend
cd frontend
npm run lint
npm run lint:fix  # auto-fix where possible
```

### Pre-commit Hooks

Install once, run automatically on every `git commit`:

```bash
pip install pre-commit
pre-commit install

# Run manually
pre-commit run --all-files

# Update hook versions
pre-commit autoupdate
```

Hooks included: trailing whitespace, merge conflict markers, Python linting (ruff), secrets scanning (detect-secrets), Docker linting (hadolint), Markdown linting.

---

## Deployment

### Docker Compose (staging)

```bash
# Edit .env with your Supabase / Ollama settings
cp .env.example .env

docker compose up --build
```

### Docker Compose (production)

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env up --build -d
```

> **Important:** Before deploying to production:
> 1. Set `ENVIRONMENT=production` and `DEBUG=false` in `.env`
> 2. Set your actual domain(s) in `CORS_ORIGINS`
> 3. Fill in real Supabase keys and Ollama endpoint
> 4. Set a strong `POSTGRES_PASSWORD`

### CI/CD

Every push to `main` automatically:
1. Runs all tests (backend + frontend)
2. Runs linting and type checks
3. Builds Docker images
4. Runs security audits (dependency vulnerabilities)
5. Deploys to **staging** automatically

To deploy to **production**: go to the GitHub Actions tab and manually trigger the **CD** workflow, or push a version tag (`v1.2.3`).

Required GitHub repository **secrets** / **variables** for CD:

| Secret / Variable | Description |
|---|---|
| `STAGING_HOST` | SSH host for staging server |
| `STAGING_USER` | SSH user for staging server |
| `STAGING_SSH_KEY` | SSH private key for staging |
| `PRODUCTION_HOST` | SSH host for production server |
| `PRODUCTION_USER` | SSH user for production server |
| `PRODUCTION_SSH_KEY` | SSH private key for production |
| `VITE_API_URL` | Production API URL |
| `VITE_SUPABASE_URL` | Production Supabase URL |
| `VITE_SUPABASE_ANON_KEY` | Production Supabase anon key |
| `STAGING_URL` | Staging deployment URL |
| `PRODUCTION_URL` | Production deployment URL |

---

## Backups

The platform has two stateful components that must be backed up:
**PostgreSQL** and the **uploads volume**. See
[docs/BACKUP_AND_RESTORE.md](docs/BACKUP_AND_RESTORE.md) for the daily
`pg_dump` script, restore procedure, off-site copies to S3, and how to
verify a backup by restoring into a test instance.

Quick example (database):

```bash
docker compose exec -T db pg_dump -U postgres -Fc careerpilot \
    > backups/db-$(date -u +%Y%m%dT%H%M%SZ).dump
```

---

## Free Tier Limitations

| Feature | Free Tier Limit |
|---------|----------------|
| Resume analysis | ✅ Unlimited (client-side rule-based) |
| Job matching | ✅ Unlimited (client-side rule-based) |
| Mock interviews | ✅ Unlimited (client-side rule-based) |
| AI insights | Local Ollama (no API costs, privacy-preserving) |
| Data storage | Supabase free tier (500 MB) or local PostgreSQL |
| Users | Unlimited (no per-seat pricing) |

---

## Optional: Enable Local AI

CareerPilot works fully without AI. For enhanced (but still free) insights:

**1. Install Ollama**

```bash
# macOS / Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Windows: download from https://ollama.ai/download
```

**2. Pull the model**

```bash
ollama pull llama3.2:3b
```

**3. Start Ollama**

```bash
ollama serve
```

The backend will automatically detect Ollama and use it. If Ollama is unavailable, it falls back to the deterministic rule-based analyzer transparently.

---

## Project Structure

```
career-pilot-ai/
├── .github/
│   ├── workflows/         # CI (ci.yml), CD (cd.yml), Release (release.yml)
│   ├── dependabot.yml     # Auto-dependency updates
│   ├── ISSUE_TEMPLATE/   # Bug report & feature request templates
│   └── PULL_REQUEST_TEMPLATE.md
│
├── backend/              # FastAPI Python application
│   ├── app/
│   │   ├── api/          # Route handlers (upload, analysis, job_match, interview)
│   │   ├── core/         # Config, logging, middleware, metrics, database
│   │   ├── schemas/      # Pydantic request/response models
│   │   ├── services/     # Business logic layer
│   │   ├── ai/           # AI provider abstraction (Ollama + fallback)
│   │   ├── security/     # Auth, rate limiting, upload validation
│   │   ├── models/       # SQLAlchemy ORM models (User, Resume, Analysis, …)
│   │   └── utils/        # Document parsing (PDF, DOCX, TXT)
│   ├── alembic/          # Database migrations
│   │   ├── env.py
│   │   └── versions/     # Migration scripts
│   ├── tests/            # pytest unit + integration tests
│   ├── Dockerfile        # Multi-stage production image
│   └── pyproject.toml    # Dependencies & tooling config
│
├── frontend/             # React TypeScript application
│   ├── src/
│   │   ├── components/   # Button, Card, NavBar, ScoreCard, States
│   │   ├── pages/        # Home, Resume, JobMatch, Interview, Dashboard, Settings
│   │   ├── services/     # API client (backend communication)
│   │   ├── types/        # TypeScript domain types
│   │   └── layouts/      # MainLayout (NavBar + footer shell)
│   ├── public/           # Static assets
│   ├── Dockerfile        # Multi-stage build + Nginx serve
│   ├── nginx.conf        # Production Nginx config
│   └── package.json
│
├── docs/                # Additional documentation
│   ├── DEPLOYMENT.md    # Detailed deployment guide
│   ├── ARCHITECTURE.md  # System design details
│   ├── BACKUP_AND_RESTORE.md  # Backup and restore procedures
│   ├── SECURITY.md      # Security model and disclosure
│   ├── CONTRIBUTING.md   # Development workflow
│   └── CHANGELOG.md     # Release history
│
├── docker-compose.yml    # Local development orchestration
├── docker-compose.prod.yml  # Production overrides
├── .env.example         # Root-level environment variables template
├── .gitignore
├── .editorconfig
├── .pre-commit-config.yaml
├── .secrets.baseline
├── .hadolint.yaml
├── .markdownlint-cli2.jsonc
├── LICENSE
└── README.md
```

---

## Contributing

1. **Fork** the repository
2. **Create a feature branch**: `git checkout -b feat/your-feature`
3. **Install pre-commit hooks**: `pre-commit install`
4. **Make your changes** – write tests, update docs
5. **Run the full check suite**:
   ```bash
   # Backend
   ruff check app tests && black --check app tests && mypy app && pytest

   # Frontend
   npm run lint && npm run typecheck && npm run test
   ```
6. **Commit** using conventional commits: `git commit -m "feat: add dark mode toggle"`
7. **Open a Pull Request** with a clear description

See [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) for the full workflow.

---

## Security

- ✅ All uploads validated for file type and size (PDF, DOCX, TXT only, max 5 MB)
- ✅ CORS configured for explicit origin allowlist
- ✅ Security headers on every response (X-Frame-Options, X-Content-Type-Options, CSP, HSTS, Referrer-Policy, Permissions-Policy)
- ✅ API authentication via Supabase JWT
- ✅ Per-user rate limiting (20 analyses/hr, 30 interviews/hr)
- ✅ No secrets committed to version control (detect-secrets pre-commit hook)
- ✅ In-memory rate limiter; Redis-compatible interface for scaling
- ✅ Prompt injection defense when using LLM features
- ✅ Runs as non-root user in Docker containers

**Found a security issue?** Please see [SECURITY.md](docs/SECURITY.md) (or open a private security advisory on GitHub).

---

## License

MIT – see [LICENSE](LICENSE). Built with ❤️ by the CareerPilot AI contributors.
