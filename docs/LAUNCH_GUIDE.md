# CareerPilot AI — Launch Guide

## Pre-Launch (T-1 hour)

### Final checks

- [ ] **Both services are "Live" on Render**
  - `careerpilot-api` → Live
  - `careerpilot-frontend` → Live

- [ ] **Health checks pass**
  - `curl https://careerpilot-api-q5ur.onrender.com/health` → 200 OK
  - `curl https://careerpilot-frontend-si1b.onrender.com/` → 200 OK

- [ ] **Sentry is receiving test events** (if DSN configured)
  - Trigger a test error
  - Verify it shows up in Sentry dashboard

- [ ] **UptimeRobot monitors are armed**
  - Both URLs should show "Up"

- [ ] **Manual backup taken**
  - `pg_dump` completed and stored securely
  - Verified backup can be restored

- [ ] **Supabase RLS policies enabled** on all tables

- [ ] **All sync:false env vars set in Render**
  - `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`, `DATABASE_URL`
  - `VITE_SUPABASE_ANON_KEY` (frontend)
  - `SENTRY_DSN` (if using Sentry)

### Smoke test

Run through the full user flow:

1. Open `https://careerpilot-frontend-si1b.onrender.com/`
2. Sign up with a new email
3. Verify email (if email confirmation is enabled in Supabase)
4. Sign in
5. Upload a test resume
6. Get an analysis (will use fallback if Ollama unavailable — that's expected)
7. Start an interview
8. Sign out
9. Sign in again — session should persist

### Monitor dashboards open

Have these tabs ready:
- Render Dashboard: https://dashboard.render.com/
- Supabase Dashboard: https://supabase.com/dashboard/project/eothvqvygmldgygjkfke
- Sentry Issues: https://sentry.io/ (if configured)
- UptimeRobot: https://uptimerobot.com/dashboard

---

## Launch (T-0)

### Announcement templates

#### Twitter / X

```
🚀 CareerPilot AI is live!

AI-powered career prep that helps you:
✅ Analyze your resume
✅ Match against job descriptions
✅ Practice mock interviews

Try it free: https://careerpilot-frontend-si1b.onrender.com

Built with @FastAPI, @supabase, and a lot of coffee ☕
```

#### LinkedIn

```
I'm excited to share that CareerPilot AI is now live! 🚀

After weeks of building, I shipped an AI-powered career preparation platform that helps job seekers:
• Get instant feedback on their resumes
• Match their skills against job descriptions
• Practice mock interviews with AI feedback

Tech stack: FastAPI + React + Supabase + Docker, deployed on Render.

Try it out: https://careerpilot-frontend-si1b.onrender.com

Would love your feedback!
```

#### Reddit (r/sideproject, r/learnprogramming)

```
Title: I built an AI-powered career prep tool — CareerPilot AI

Hi r/sideproject! I've been working on CareerPilot AI, a free tool to help job seekers prep smarter.

Features:
- AI resume analysis (with offline fallback for privacy)
- Job description matching
- Mock interview practice

Stack: FastAPI backend, React frontend, Supabase auth + DB, Docker on Render.

Free to use, no signup required for browsing.

Live: https://careerpilot-frontend-si1b.onrender.com
GitHub: https://github.com/rpritiranjan90-crypto/careerpilot-ai

Feedback welcome!
```

#### Hacker News (Show HN)

```
Title: Show HN: CareerPilot AI – Free AI career prep tool

Hi HN,

I built CareerPilot AI to help job seekers prep smarter. It analyzes resumes, matches them against job descriptions, and provides AI feedback on mock interviews.

Key design decisions:
- Privacy-first: uses local Ollama for AI inference when available, with a deterministic fallback when not
- Supabase for auth + DB (free tier)
- Docker + Render for hosting
- Open source: https://github.com/rpritiranjan90-crypto/careerpilot-ai

The whole thing is free to use. Would love feedback on the AI analysis quality and UX.

Live: https://careerpilot-frontend-si1b.onrender.com
```

#### Product Hunt (if you want to launch there)

**Tagline**: "AI-powered career prep that helps you land your next role"

**Description**:
CareerPilot AI is a free tool that helps job seekers:
1. Analyze their resume for impact, clarity, and ATS-friendliness
2. Match their skills against specific job descriptions
3. Practice mock interviews with instant AI feedback

Built with privacy in mind — AI runs locally when possible.

---

## Post-Launch (T+1 hour, T+1 day, T+1 week)

### T+1 hour: First stability check

- [ ] Both services still Live on Render
- [ ] No error spikes in Sentry
- [ ] UptimeRobot shows both monitors "Up"
- [ ] No user-reported issues

### T+1 day: Engagement check

- [ ] Sign-ups: How many users signed up?
- [ ] Active users: How many actually used the app?
- [ ] Most-used feature: Resume analysis? Interview? Job match?
- [ ] Error rate: Any patterns in Sentry?
- [ ] Performance: Any slow endpoints? (Check Render metrics)

### T+1 week: Iterate

- [ ] User feedback collected
- [ ] Top 3 issues prioritized
- [ ] Roadmap updated

---

## Rollback plan

If something goes catastrophically wrong:

1. **Render → careerpilot-api → Manual Deploy → previous commit**
2. Or: **Render → careerpilot-api → Suspend Service** (stops the service)
3. Same for frontend

Database rollback (if schema is the issue):
1. `psql ... < backup_20260101.sql` (restore from manual backup)
2. Or: Supabase Dashboard → Database → Backups → Restore

---

## Support

During the first week, monitor these channels:
- Email (if you set one up)
- GitHub Issues
- Sentry alerts
- Render alerts

Respond to issues within 24 hours.

---

## Next Steps

After launch, proceed to:
- **Step 14**: Post-launch (metrics review, iterate)