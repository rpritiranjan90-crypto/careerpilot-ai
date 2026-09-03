# CareerPilot AI — Pre-Launch Security Checklist

Run through this checklist before going public.

---

## 1. Secrets & Environment Variables

- [x] **No .env files committed to Git**
  - Verified: `git ls-files | grep .env` returns nothing
  - `.gitignore` includes `.env`, `backend/.env`, `frontend/.env`

- [x] **No secrets in render.yaml values** (only sync:false placeholders)
  - `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`, `DATABASE_URL` are all `sync: false`
  - Only public values are inlined (ENVIRONMENT, DEBUG, RATE_LIMIT_*, etc.)

- [x] **No SUPABASE_JWT_SECRET in frontend**
  - `grep -r "SUPABASE_JWT_SECRET" frontend/src` returns no matches
  - Frontend only uses VITE_SUPABASE_ANON_KEY (public-facing, designed to be shared)

- [x] **Frontend never imports backend-only env vars**
  - No VITE_ versions of: SUPABASE_SERVICE_ROLE_KEY, SUPABASE_JWT_SECRET, DATABASE_URL

---

## 2. Authentication & Authorization

- [x] **DEV_TOKEN_AUTH=false in production**
  - Set in `render.yaml` line 34-35
  - Backend has a production-safety validator that refuses to start if `ENV=production DEV_TOKEN_AUTH=true`

- [x] **SUPABASE_JWT_SECRET is set in Render**
  - Required for JWT signature verification
  - Backend refuses to start in production without it

- [x] **JWT validation enforced**
  - Signature verified using `SUPABASE_JWT_SECRET`
  - `aud`, `iss`, `exp` claims checked
  - See `backend/app/security/auth.py`

- [x] **CORS configured for production frontend only**
  - `CORS_ORIGINS=https://careerpilot-frontend-si1b.onrender.com` in render.yaml
  - No wildcard `*` in CORS

---

## 3. HTTP Security Headers

- [x] **Content-Security-Policy set**
  - Default-src, script-src, style-src, img-src, font-src, connect-src all restricted
  - Supabase domain whitelisted in connect-src
  - Wildcard `https://*` removed

- [x] **HSTS enabled** (max-age=31536000, includeSubDomains, preload)

- [x] **X-Content-Type-Options: nosniff**

- [x] **X-Frame-Options: DENY**

- [x] **X-XSS-Protection: 1; mode=block**

- [x] **Referrer-Policy: strict-origin-when-cross-origin**

- [x] **Permissions-Policy** blocks camera, microphone, geolocation

- [x] **Server header removed** (hides "uvicorn" from response)

---

## 4. Database Security

- [x] **Using Supabase connection pooler** (not direct connection)
  - Reduces attack surface
  - Free tier only allows pooler

- [x] **DB_SCHEMA=careerpilot** (isolated from public schema)
  - Prevents accidental writes to wrong schema

- [x] **psycopg2-binary with parameterized queries** (SQLAlchemy ORM)
  - No raw SQL string concatenation in app code

- [ ] **Supabase Row Level Security (RLS) policies**
  - Go to Supabase Dashboard → Authentication → Policies
  - Verify RLS is enabled on all `careerpilot.*` tables
  - If not, enable: `ALTER TABLE careerpilot.users ENABLE ROW LEVEL SECURITY;`

---

## 5. File Upload Security

- [x] **File size limit** (MAX_UPLOAD_SIZE_MB=5)

- [x] **Extension whitelist** (ALLOWED_EXTENSIONS=pdf,docx,txt)

- [x] **Files stored outside web root** (`/app/uploads`)

- [ ] **Optional: File content validation**
  - Currently only checks file extension
  - Could add magic byte validation (e.g., PDF starts with `%PDF`)

---

## 6. Rate Limiting

- [x] **RATE_LIMIT_ANALYZE=20** (requests per hour per user)

- [x] **RATE_LIMIT_INTERVIEW=30** (requests per hour per user)

- [ ] **Optional: Global rate limit**
  - Currently per-endpoint
  - Could add a global IP-based rate limit for unauthenticated routes

---

## 7. Docker Security

- [x] **Non-root user** in both Dockerfiles
  - Backend: `appuser` (UID 1000)
  - Frontend: `nginxuser` (UID 1001)

- [x] **Slim base images** (python:3.11-slim, nginx:1.27-alpine)
  - Minimal attack surface
  - No unnecessary OS packages

- [x] **Multi-stage builds** (no build tools in runtime image)

- [x] **No secrets baked into image**
  - All sensitive env vars passed at runtime (sync:false)
  - `ENV` instructions in Dockerfiles only contain non-sensitive defaults

---

## 8. CI/CD Security

- [x] **GitHub Actions enabled** (CodeQL running on every push)

- [x] **No force pushes to main** (Render auto-deploys from main)

- [x] **Secrets stored in Render, not GitHub**
  - `SUPABASE_*` keys live in Render dashboard
  - Not exposed in PRs or commit history

---

## 9. Monitoring & Logging

- [x] **Sentry integration** (set SENTRY_DSN in Render)
  - Backend: ✅ code done, DSN pending
  - Frontend: ⏳ optional

- [x] **Structured logging** with request IDs
  - All requests get a unique X-Request-ID
  - Errors logged with full context

- [x] **Health check endpoint** (`/health`)
  - Used by Render for liveness probes
  - UptimeRobot will monitor this

- [x] **Readiness check** (`/health/ready`)
  - Checks database connectivity
  - Checks Ollama availability (best-effort)

---

## 10. Third-Party Services

- [x] **Supabase** (auth + DB)
  - Free tier, but production-ready
  - Project is private (not exposed via public schema)

- [x] **Render** (hosting)
  - HTTPS enforced
  - Free tier with cold starts (acceptable for MVP)

- [ ] **Ollama** (AI inference)
  - Currently set to `http://localhost:11434`
  - **This won't work in production** — Render containers don't have Ollama
  - Action: either remove AI features for MVP, or use an external API (OpenAI, Anthropic)

---

## 11. Legal & Compliance

- [ ] **Privacy policy** (if collecting user data)
  - You collect: email, password (hashed by Supabase), uploaded files, interview responses
  - Required for GDPR, CCPA, etc.

- [ ] **Terms of service**

- [ ] **Cookie consent banner** (if using any cookies beyond auth)

- [ ] **Data deletion endpoint** (GDPR right to be forgotten)
  - Add endpoint: `DELETE /api/users/me` that removes user data

---

## 12. Final Pre-Launch Tests

Run these checks **immediately before** announcing the launch:

```bash
# 1. Health check
curl -I https://careerpilot-api-q5ur.onrender.com/health

# 2. Frontend loads
curl -I https://careerpilot-frontend-si1b.onrender.com/

# 3. Auth flow works
# - Sign up new user
# - Log in
# - Log out
# - Sign in again

# 4. CORS check
curl -H "Origin: https://careerpilot-frontend-si1b.onrender.com" \
     -H "Access-Control-Request-Method: POST" \
     -X OPTIONS \
     https://careerpilot-api-q5ur.onrender.com/api/auth/login \
     -I

# 5. Security headers
curl -I https://careerpilot-frontend-si1b.onrender.com/

# 6. No secrets leaked in frontend bundle
curl -s https://careerpilot-frontend-si1b.onrender.com/assets/ -o /tmp/frontend_bundle.html
grep -E "SUPABASE_SERVICE_ROLE_KEY|SUPABASE_JWT_SECRET|DATABASE_URL" /tmp/frontend_bundle.html
# (should return no matches)
```

---

## 13. Summary Status

| Category | Status | Notes |
|----------|--------|-------|
| Secrets | ✅ Complete | All env vars properly scoped |
| Auth | ✅ Complete | DEV_TOKEN_AUTH=false, JWT validated |
| HTTP Headers | ✅ Complete | All recommended headers set |
| Database | ⚠️ Verify RLS | Check Supabase policies |
| File Uploads | ✅ Complete | Size + extension limits |
| Rate Limiting | ✅ Complete | Per-endpoint limits |
| Docker | ✅ Complete | Non-root, slim images |
| CI/CD | ✅ Complete | CodeQL running |
| Monitoring | ⏳ Pending | Need to add Sentry DSN + UptimeRobot |
| AI/Ollama | ❌ Broken in prod | Set to localhost:11434 (won't work) |
| Legal | ⏳ Optional | Privacy policy, ToS |

---

## Critical Action Items Before Launch

1. **Decide on AI in production**
   - Option A: Remove AI features from production UI
   - Option B: Switch to OpenAI/Anthropic API (requires API key in Render)
   - Option C: Skip for now, add later

2. **Add Sentry DSN to Render** (for error tracking)

3. **Set up UptimeRobot** (for uptime alerts)

4. **Verify Supabase RLS policies** are enabled

5. **Take a manual pg_dump backup** before launch

---

## Next Steps

After completing this checklist, proceed to:
- **Step 13**: Launch (announce, monitor, support)
- **Step 14**: Post-launch (metrics review, iterate)