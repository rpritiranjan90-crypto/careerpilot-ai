# CareerPilot AI — Monitoring Setup Guide

This document walks through setting up production monitoring for CareerPilot AI.

---

## 1. Sentry Error Tracking (Backend)

### What's already done:
- Added `sentry-sdk[fastapi]` to `backend/pyproject.toml`
- Created `backend/app/core/sentry.py` with initialization
- Integrated Sentry in `backend/app/main.py`
- Added `SENTRY_DSN` environment variable to `render.yaml` (sync:false)

### Your actions:
1. **Create a Sentry account** (if you don't have one):
   - Go to https://sentry.io/signup/
   - Choose "Developer" (free tier: 5,000 errors/month, 1 team member)

2. **Create a Sentry project**:
   - Organization → Projects → New Project
   - Platform: **FastAPI** (or Python)
   - Name: `careerpilot-api`
   - Copy the **DSN** (looks like `https://<key>@o<org>.ingest.sentry.io/<project>`)

3. **Add DSN to Render**:
   - Go to Render Dashboard → `careerpilot-api` → Environment
   - Add `SENTRY_DSN` with the DSN value
   - Click **Save Changes** (triggers redeploy)

4. **Verify**:
   - Trigger a test error: `curl https://careerpilot-api-q5ur.onrender.com/api/debug/error`
   - Check Sentry Issues page — should see the error within seconds

---

## 2. Sentry Error Tracking (Frontend)

### What's needed:
- Add `@sentry/react` to frontend dependencies
- Initialize Sentry in `frontend/src/main.tsx`

### Your actions:
1. **Add dependency**:
```bash
cd frontend
npm install @sentry/react
```

2. **Create Sentry init file** (`frontend/src/lib/sentry.ts`):
```typescript
import * as Sentry from "@sentry/react";

export function initSentry() {
  const dsn = import.meta.env.VITE_SENTRY_DSN;
  if (!dsn) return;

  Sentry.init({
    dsn,
    environment: import.meta.env.VITE_APP_ENV || "development",
    integrations: [Sentry.browserTracingIntegration()],
    tracesSampleRate: 0.2,
    replaysSessionSampleRate: 0.1,
    replaysOnErrorSampleRate: 1.0,
  });
}
```

3. **Initialize in `main.tsx`**:
```typescript
import { initSentry } from "./lib/sentry";
initSentry();
```

4. **Add to `render.yaml`**:
```yaml
      - key: VITE_SENTRY_DSN
        sync: false
```

5. **Add DSN to Render dashboard** for `careerpilot-frontend`

---

## 3. Uptime Monitoring (UptimeRobot)

### What's needed:
- Create monitors for both production URLs
- Configure alerts (email, Slack, etc.)

### Your actions:
1. **Create UptimeRobot account**:
   - Go to https://uptimerobot.com/
   - Free tier: 50 monitors, 5-minute checks

2. **Add monitors**:

   **Backend API**:
   - Friendly Name: `CareerPilot API`
   - URL: `https://careerpilot-api-q5ur.onrender.com/health`
   - Type: HTTP(s)
   - Interval: 5 minutes
   - Alert contacts: Add your email/Slack

   **Frontend**:
   - Friendly Name: `CareerPilot Frontend`
   - URL: `https://careerpilot-frontend-si1b.onrender.com/`
   - Type: HTTP(s)
   - Interval: 5 minutes
   - Alert contacts: Add your email/Slack

3. **Verify**:
   - Wait 5 minutes for first check
   - Both should show "Up" status

---

## 4. Render Native Monitoring

### What's available (no setup needed):
- **Metrics tab** in Render dashboard: CPU, Memory, Request count, Latency
- **Logs tab**: Real-time logs with filtering
- **Events**: Deploy history, auto-deploy status
- **Alerts**: Configure in Render → Settings → Alerts
  - Deploy failures
  - Service down
  - High memory/CPU

### Recommended Render alerts:
1. Go to Render Dashboard → Settings → Alerts
2. Add alerts for:
   - `careerpilot-api`: "Service is down" → email
   - `careerpilot-api`: "Deploy failed" → email
   - `careerpilot-frontend`: "Service is down" → email
   - `careerpilot-frontend`: "Deploy failed" → email

---

## 5. Prometheus/Grafana (Optional - for advanced metrics)

If you want custom dashboards beyond Render's built-in metrics:

### Option A: Grafana Cloud (Free tier)
1. Sign up at https://grafana.com/auth/sign-up/create-user
2. Create a **Prometheus** datasource
3. Configure remote write from your app (requires `/metrics` endpoint accessible)
4. Build dashboards for:
   - Request rate (http_requests_total)
   - Latency (http_request_duration_seconds)
   - Error rate (http_request_errors_total)
   - In-flight requests

### Option B: Self-hosted (not recommended for free tier)

---

## 6. Log Aggregation (Optional)

For structured log search:

### Option A: Grafana Loki (Free tier on Grafana Cloud)
- Ship logs via Promtail or Docker logging driver
- Query logs alongside metrics

### Option B: Better Stack / Logtail
- Free tier available
- Easy integration with Render via log drain

---

## 7. Summary Checklist

| Component | Status | Action Required |
|-----------|--------|-----------------|
| Backend Sentry | ✅ Code done | Add DSN to Render |
| Frontend Sentry | ❌ Not started | Add dependency + init |
| UptimeRobot | ❌ Not started | Create account + 2 monitors |
| Render Alerts | ❌ Not started | Configure in dashboard |
| Grafana Cloud | ⏳ Optional | If needed |

---

## 8. Next Steps After Monitoring

Once monitoring is live, proceed to:
- **Step 11**: Backup and Recovery (verify Supabase backups, document restore)
- **Step 12**: Pre-launch Security Checklist
- **Step 13**: Launch
- **Step 14**: Post-launch