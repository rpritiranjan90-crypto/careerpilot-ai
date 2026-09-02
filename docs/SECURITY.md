# Security Policy

## Supported versions

| Version | Supported          |
|---------|--------------------|
| 1.x     | ✅ Active          |
| < 1.0   | ❌ End of life     |

## Reporting a vulnerability

**Please do NOT open a public GitHub issue for security vulnerabilities.**

Instead, please report them privately via one of these channels:

1. **GitHub Security Advisories** (preferred): https://github.com/your-org/career-pilot-ai/security/advisories/new
2. **Email**: security@careerpilot.example

You should receive a response within **48 hours**. If you don't, please follow up.

## What to include

To help us triage quickly, please include:

- Type of issue (e.g., RCE, XSS, SQL injection, auth bypass)
- Full paths of affected source files
- Location of the affected code (tag/branch/commit or URL)
- Step-by-step instructions to reproduce
- Proof-of-concept or exploit code (if available)
- Impact of the issue, including how an attacker might exploit it

## Disclosure policy

- We will acknowledge receipt of your report within 48 hours
- We will provide an initial assessment within 7 days
- We will keep you informed of our progress
- We will credit you in the fix commit (unless you prefer to remain anonymous)
- We ask that you give us a reasonable amount of time to fix the issue before public disclosure (typically 90 days)

## Security architecture

See [ARCHITECTURE.md](ARCHITECTURE.md#security-layers) for a detailed overview of the security layers in place.

### At a glance

- **Transport** — TLS everywhere; HSTS in production
- **Headers** — CSP, X-Frame-Options, X-Content-Type-Options, Permissions-Policy
- **CORS** — explicit origin allowlist
- **Input** — Pydantic validation, file extension/size/MIME checks
- **Auth** — JWT bearer tokens on all `/api/*` routes
- **Rate limit** — per-user per-action
- **Secrets** — env vars only; detect-secrets pre-commit hook
- **Container** — non-root user, minimal base image, multi-stage build

## Security checklist for contributors

Before opening a PR that touches security-sensitive code, confirm:

- [ ] No new secrets, API keys, or credentials are committed
- [ ] No `console.log` of sensitive data (tokens, passwords, PII)
- [ ] User input is validated via Pydantic (backend) or TypeScript types (frontend)
- [ ] New endpoints have an authentication dependency (`Depends(get_current_user)`)
- [ ] File uploads validate type, size, and sanitize filenames
- [ ] No `eval`, `exec`, `Function()`, or `dangerouslySetInnerHTML` without explicit review
- [ ] Database queries use parameterized statements (SQLAlchemy ORM)
- [ ] Dependencies are from trusted sources (no typosquats)

## Automated scanning

The CI pipeline runs on every push:

- **pip-audit** — Python dependency vulnerabilities
- **npm audit** — Node.js dependency vulnerabilities
- **Trivy** — filesystem + container image scanning
- **detect-secrets** (pre-commit) — secret detection

## Hall of fame

Thank you to the security researchers who have helped improve CareerPilot AI:

<!-- Add researchers here as issues are reported and fixed -->
