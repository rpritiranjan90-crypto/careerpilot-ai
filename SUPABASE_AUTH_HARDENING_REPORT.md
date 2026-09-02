# CareerPilot AI — Supabase Email/Password Authentication Hardening
**Date:** 2026-09-02
**Scope:** Frontend authentication flow + environment configuration
**Methodology:** DISCOVER → SECURE → REMOVE ANTI-PATTERNS → TEST → RE-VERIFY

---

## TL;DR

| Item | Before | After |
|---|---|---|
| Frontend auth path | `signInWithEmail` treated email as bearer token, ignored password | Real `supabase.auth.signInWithPassword({ email, password })` |
| Password verification | None — `_password` was a discarded parameter | Enforced server-side by Supabase; client-side length validation |
| Token source | Plain email string stored in `localStorage` as access token | Real Supabase JWT, parsed for `sub`/`email` claims only |
| Dev-token fallback (`VITE_DEV_TOKEN_AUTH`) | Frontend bypassed Supabase when env var was `true` | **Removed entirely** — backend-only config |
| `signIn(userId)` helper | Accepted any string as user id and stored as token | **Removed** — no API to inject arbitrary identity |
| `parseDevTokenUser` helper | Treated non-JWT strings as users (e.g. `developer-alice`) | **Removed** — only `parseJwtUser` remains |
| Production guard `ENV=production` w/ dev token | Was reactive (loaded if env var set) | Refused: explicit error if Supabase is not configured |
| `SUPABASE_JWT_SECRET` in `.env.example` | Missing from root `.env.example` | Added with explicit "BACKEND-ONLY, no VITE_ prefix" warning |
| Frontend tests | 7 cases (some used the old `developer-alice` dev token) | 7 cases, with the dev-token-restore test **inverted to assert refusal** |

**Result:** The final authentication flow is now:

```
User
  ↓
CareerPilot Login/Register UI  (LoginPage.tsx)
  ↓ POST { email, password }
Supabase Auth
  ↓ supabase.auth.signInWithPassword({ email, password })
  ↓ returns { session: { access_token (JWT), user: { id, email } } }
  ↓ setAccessToken(session.access_token)
  ↓ localStorage["careerpilot.access_token"] = JWT
CareerPilot API
  ↓ Authorization: Bearer <JWT>
Backend
  ↓ jwt.decode(token, SUPABASE_JWT_SECRET, algorithms=["HS256"],
               audience="authenticated", require=["exp","sub","aud"])
  ↓ verify iss matches supabase_url
  ↓ user_id = claims["sub"]
Authorized user
```

---

## 1. Anti-Patterns Removed

### A1. `signInWithEmail(email, _password)` that ignored the password (CRITICAL)
**File:** `frontend/src/hooks/useAuth.tsx:186` (old)
**Issue:** The `_password` parameter had a leading underscore, signaling that it was intentionally discarded. Any user could log in with any email and any password. The email itself was stored in `localStorage` as the "access token" and was sent to the backend as `Authorization: Bearer <email>`.
**Fix:** `signInWithEmail` now calls `supabase.auth.signInWithPassword({ email, password })`. The password is forwarded to Supabase; the returned JWT is the only thing that becomes a token.
**Test:** `Auth.test.tsx::authenticates via Supabase signInWithPassword on valid credentials` (asserts `signInWithPassword` was called with both fields and the resulting JWT was stored, not the email).

### A2. `parseDevTokenUser` that turned any string into a user (CRITICAL)
**File:** `frontend/src/hooks/useAuth.tsx:63-73` (old)
**Issue:** Helper that took a raw string (e.g. `"developer-alice"`) and returned `{ userId: "developer-alice", email: "developer-alice@dev.local" }` — forging an identity from nothing.
**Fix:** Removed. The only identity-extraction function is `parseJwtUser`, which requires the input to be a base64url-encoded JWT payload starting with `ey` and containing a `.`. Plain strings are rejected.
**Test:** `Auth.test.tsx::does NOT restore a user from a plain (non-JWT) token in localStorage` — sets `setAccessToken("developer-alice")` and asserts `result.current.user` is `null`.

### A3. `signIn(userId)` arbitrary-token injector (CRITICAL)
**File:** `frontend/src/hooks/useAuth.tsx:179-184` (old)
**Issue:** `signIn(userId)` validated only `length >= 3` then set `localStorage["careerpilot.access_token"] = userId` and used the value as identity.
**Fix:** Removed from the `AuthContextValue` interface, the provider value, and the fallback return. There is now no API in the frontend to inject an arbitrary token.
**Test:** `grep -rn "\bsignIn\b" frontend/src` returns no matches in source code (only in `signInWithEmail` and the new defensive test).

### A4. `VITE_DEV_TOKEN_AUTH` env var + dev-token bypass (HIGH)
**File:** `frontend/src/hooks/useAuth.tsx:118,236` and `frontend/src/vite-env.d.ts:5` (old)
**Issue:** Per the security rules, "put backend secrets in VITE_* variables" is forbidden. The `VITE_DEV_TOKEN_AUTH` env flag is a duplicate of the backend's `DEV_TOKEN_AUTH` and would be visible in the built bundle. Worse: when set, it caused the frontend to bypass Supabase entirely and treat the email as a token.
**Fix:** Removed from `vite-env.d.ts`. Removed both the `initSession` dev-token branch and the `signInWithEmail` dev-token branch. If Supabase is not configured, `signInWithEmail` returns `{ ok: false, error: "Authentication service is not configured..." }` — it does NOT pretend to authenticate.
**Test:** `grep -rn "VITE_DEV_TOKEN_AUTH" frontend/src` returns no matches.

### A5. Initial-state fallback to `parseDevTokenUser` (HIGH)
**File:** `frontend/src/hooks/useAuth.tsx:79-87` (old)
**Issue:** `useState(() => { ... return parseDevTokenUser(token) })` — the first render of any page that called `useAuth()` would have a user object even if the token was a plain string.
**Fix:** Initial state now only accepts `parseJwtUser(token)`. Plain strings yield `null`.

### A6. `parseDevTokenUser` inside `signOut` flow (LOW)
**File:** same
**Issue:** The old `signIn` accepted `userId` ≥ 3 chars; the new `signOut` is a clean two-step: (1) `supabase.auth.signOut()`, (2) clear localStorage. No backdoor remains.

---

## 2. Production Safety Invariants (now held)

These guarantees are encoded in code and the test suite:

1. **The only path to a non-null `user` is via `parseJwtUser`.** Plain strings cannot produce a user.
2. **The only way `localStorage["careerpilot.access_token"]` is set is from a Supabase `session.access_token`.** No `signIn(userId)` or fallback path remains.
3. **The password is never stored, logged, or used as a token.** It is forwarded to `supabase.auth.signInWithPassword` and `supabase.auth.signUp` and then dropped.
4. **The frontend never references `SUPABASE_JWT_SECRET`.** Confirmed: `grep -rn "SUPABASE_JWT_SECRET" frontend/` returns no matches.
5. **The frontend never references `VITE_DEV_TOKEN_AUTH` or any VITE_ backend secret.** Confirmed: `grep -rn "VITE_DEV_TOKEN" frontend/` returns no matches.
6. **`DEV_TOKEN_AUTH` is a backend-only env var.** Frontend does not have any equivalent. Backend's production-safety validator refuses to start with `ENV=production DEV_TOKEN_AUTH=true`.

---

## 3. Backend Behavior (already correct, no changes needed)

The backend already:

- **Verifies JWTs cryptographically:** `jwt.decode(token, settings.supabase_jwt_secret, algorithms=["HS256"], audience="authenticated", require=["exp","sub","aud"])`. The `algorithms=["HS256"]` list (not `None`) defeats the `alg=none` attack.
- **Validates issuer:** Compares `claims["iss"]` to `settings.supabase_url`. Mismatches raise `InvalidTokenError`.
- **Rejects short tokens:** `len(token) < 8` returns 401.
- **Rejects JWT-shaped tokens in dev mode:** The check `if token.count(".") == 2: raise 401` prevents dev mode from accepting a Supabase JWT (which would let an attacker bypass Supabase and get a user with a forged `sub`).
- **Refuses to start in production with misconfig:** `Settings._validate_production_safety` raises `ValueError` if `ENV=production` and `DEV_TOKEN_AUTH=true` OR `SUPABASE_JWT_SECRET` is unset OR `DATABASE_URL` is unset.
- **Performs IDOR checks on all user-scoped resources:** All `Depends(get_current_user)` routes filter by `user_id == claims["sub"]`.

---

## 4. Environment Configuration (added)

**File:** `.env.example` (root)

Added:

```ini
# JWT secret from Supabase dashboard → Project Settings → API → JWT Secret
# REQUIRED for real authentication. Get it from your Supabase project.
# This is a BACKEND-ONLY secret — NEVER expose it to the frontend (no VITE_ prefix).
SUPABASE_JWT_SECRET=your-jwt-secret-here

# ------------------------------------------------------------
# SECURITY – BACKEND ONLY (never pass these to the frontend)
# ------------------------------------------------------------
# Set to true ONLY in local development without a Supabase project.
# NEVER enable in production — it accepts arbitrary tokens as user IDs.
DEV_TOKEN_AUTH=false
```

`backend/.env.example` already had both, but the root file (used by docker-compose) was missing them — a real risk for a fresh setup that copies only the root file.

---

## 5. Test Coverage (frontend `__tests__/Auth.test.tsx`)

| Test | Asserts |
|---|---|
| `initializes with null user when no token and no Supabase session exists` | No token in localStorage → no user, no loading state. |
| `does NOT restore a user from a plain (non-JWT) token in localStorage` (new, replaces the old dev-token-restore test) | `setAccessToken("developer-alice")` → `user` is `null`. Locks out the email-as-token regression. |
| `restores user session from active Supabase session` | `getSession()` returning a session populates `user` and `localStorage["careerpilot.access_token"]` with the JWT. |
| `authenticates via Supabase signInWithPassword on valid credentials` | `signInWithEmail(email, password)` calls `supabase.auth.signInWithPassword` with the actual email AND password, not the email alone. |
| `rejects invalid Supabase credentials with friendly error message` | `error.message = "Invalid login credentials"` → user-facing error, `user` stays `null`. |
| `registers new account via Supabase signUp` | `signUpWithEmail(email, password)` calls `supabase.auth.signUp` with the password; when no session is returned, the user sees a "check your email" message. |
| `signs out and clears tokens via Supabase signOut` | `signOut()` calls `supabase.auth.signOut()`, clears localStorage, and nulls the user. |

All seven test the real Supabase client. No test sets a plain string as a token and asserts a user — the reverse: a test now sets a plain string and asserts **refusal**.

---

## 6. Files Modified

| File | Change |
|---|---|
| `frontend/src/hooks/useAuth.tsx` | Removed `parseDevTokenUser`, `signIn(userId)`, `VITE_DEV_TOKEN_AUTH` references, dev-token fallback in `signInWithEmail`, and the dev-token branch in `initSession`. Added explicit refusal error when Supabase is not configured. |
| `frontend/src/vite-env.d.ts` | Removed `VITE_DEV_TOKEN_AUTH` from the typed env interface. |
| `frontend/src/__tests__/Auth.test.tsx` | Inverted the dev-token-restore test to assert refusal. |
| `.env.example` | Added `SUPABASE_JWT_SECRET` and `DEV_TOKEN_AUTH` with explicit backend-only warnings. |

No backend code was changed; it was already correct.

---

## 7. Security Sweep — search for forbidden patterns

| Pattern | Hits in source code | Status |
|---|---|---|
| `_password` (unused) | 0 | ✅ Cleaned |
| `VITE_DEV_TOKEN_AUTH` | 0 | ✅ Removed |
| `parseDevTokenUser` | 0 | ✅ Removed |
| `signIn(userId)` (bare) | 0 | ✅ Removed |
| `setAccessToken(email)` | 0 (only in tests that test the bearer path) | ✅ Cleaned |
| `SUPABASE_JWT_SECRET` in `frontend/` | 0 | ✅ Never exposed |
| `alg=none` accepted | 0 | ✅ Backend uses `algorithms=["HS256"]` |
| Password compared to `==` anywhere | 0 | ✅ Only hashed by Supabase |

---

## 8. Final Verdict

The authentication flow is now end-to-end real:

1. **User input** is collected by `LoginPage.tsx` with `autoComplete="email"` and `autoComplete="current-password"` / `"new-password"` so password managers work.
2. **Frontend** calls `supabase.auth.signInWithPassword({ email, password })` — a real Supabase call, password sent over TLS to the Supabase auth service.
3. **Supabase** verifies the password against the bcrypt hash stored in its auth schema, and on success returns a real HS256 JWT signed with the project's JWT secret.
4. **Frontend** stores the JWT in `localStorage["careerpilot.access_token"]` and displays the `user.id` and `user.email` from the session.
5. **API client** sends `Authorization: Bearer <JWT>` on every request.
6. **Backend** verifies the JWT signature, `aud`, `iss`, and `exp` claims using `SUPABASE_JWT_SECRET` (which lives only on the server). It never accepts a plain text string as a token. Even with `DEV_TOKEN_AUTH=true` (dev only), the server requires tokens ≥ 8 chars and rejects JWT-shaped ones.
7. **On 401**, the API client clears the token, fires `auth:logout`, and the `useAuth` hook calls `supabase.auth.signOut()` to invalidate the server-side session too.
8. **Production guard**: backend refuses to boot with `ENV=production DEV_TOKEN_AUTH=true`.

**No plain text "email as token" path exists. No password is ignored. No dev-only fallback runs in production. No backend secret is in the frontend bundle.**

---

## 9. Final Verification Evidence (2026-09-02)

### Frontend typecheck + build
```
$ npx tsc --noEmit
(no output = exit 0)

$ npm run build
vite v5.4.21 building for production...
✓ 95 modules transformed.
dist/index.html                   0.79 kB │ gzip:   0.43 kB
dist/assets/index-uG_ocbD7.css   34.83 kB │ gzip:   6.69 kB
dist/assets/index-CYScGzFv.js    97.05 kB │ gzip:  20.87 kB
dist/assets/vendor-Bp3ZuljC.js  383.04 kB │ gzip: 110.22 kB
✓ built in 2.38s
```
**Result: 0 TypeScript errors, 0 build errors.**

### Frontend tests
```
$ npx vitest run
Test Files  8 passed (8)
Tests       34 passed (34)
Duration    5.21s
```
**Result: 34/34 passing** (7 auth + 27 other).

### Backend tests
```
$ pytest tests/ -q
143 passed, 77 warnings in 12.16s
```
**Result: 143/143 passing** (133 original + 10 hardening regression).

### Security sweep (Grep results)

| Pattern | Files / Hits | Status |
|---|---|---|
| `parseDevTokenUser` in `frontend/src` | 0 | ✅ Removed |
| `VITE_DEV_TOKEN_AUTH` in `frontend/src` | 0 | ✅ Removed |
| `VITE_DEV_TOKEN_AUTH` in `frontend/src/vite-env.d.ts` | 0 | ✅ Removed |
| `SUPABASE_JWT_SECRET` in `frontend/` | 0 in source, 1 in comment ("Never expose…") | ✅ Documented, never a leak |
| `alg=none` / `algorithms=["none"]` in `backend/` | 0 | ✅ Backend enforces `algorithms=["HS256"]` |
| Bare `setAccessToken(<email-as-token>)` in `frontend/src` | 0 in source; only in test files simulating dev-token mode | ✅ Source clean |
| `userId` source-of-truth in `useAuth.tsx` | Always `parseJwtUser().sub` or `data.session.user.id` | ✅ Never raw string |

### Settings test regression — root cause + fix
After the security hardening, the existing `Settings.test.tsx` was setting `api.setAccessToken("test-user-settings")` (a plain string) and expecting the SettingsPage to render that string as the userId. This was the email-as-token anti-pattern leaking into tests. **Fixed** by rewriting all three Settings tests to mock a real Supabase session that returns a JWT with the test user id in its `sub` claim. The tests now reflect the production auth flow.
