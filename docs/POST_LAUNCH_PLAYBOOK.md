# CareerPilot AI — Post-Launch Playbook

This document covers what to do after launch: monitoring, iterating, and growing.

---

## 1. First 24 Hours

### Active monitoring

Keep these tabs open and check every 2-4 hours:

| Dashboard | URL | What to watch |
|-----------|-----|---------------|
| Render | https://dashboard.render.com/ | Service status, CPU/memory, logs |
| Sentry | https://sentry.io/ | New errors, error spikes |
| UptimeRobot | https://uptimerobot.com/ | Uptime status, response time |
| Supabase | https://supabase.com/dashboard/project/eothvqvygmldgygjkfke | DB connections, auth events |

### What to look for

- **Error rate spike**: New error type in Sentry → check logs → fix or rollback
- **High CPU/memory**: Likely a memory leak or runaway request → check logs
- **Slow responses**: Check Render metrics for `p95 latency` → may need to scale up
- **Auth failures**: If sign-in suddenly fails, check `SUPABASE_URL` is still set

### Quick response actions

If you see an issue:
1. **Check Sentry first** — gives you the full stack trace
2. **Check Render logs** — `careerpilot-api → Logs → Filter: ERROR`
3. **Decide**: hotfix or rollback?
4. **Hotfix**: commit fix, push to main, Render auto-deploys (~2-3 min)
5. **Rollback**: Render → Manual Deploy → select previous commit

---

## 2. First Week: Collect Feedback

### Metrics to track

| Metric | Where to find it | Target (MVP) |
|--------|------------------|--------------|
| Sign-ups | Supabase → Authentication → Users | 10+ users |
| Active users (DAU) | Custom: count distinct user_ids in DB | 5+ DAU |
| Resume analyses | Custom: count rows in `careerpilot.analyses` | 20+ analyses |
| Interview sessions | Custom: count rows in `careerpilot.interviews` | 10+ sessions |
| Error rate | Sentry → Issues | < 5% of requests |
| Uptime | UptimeRobot | > 95% (free tier allows cold starts) |

### How to query the database

Use Supabase SQL Editor:
https://supabase.com/dashboard/project/eothvqvygmldgygjkfke/sql

```sql
-- Total sign-ups
SELECT COUNT(*) FROM careerpilot.users;

-- Active users (last 7 days)
SELECT COUNT(DISTINCT user_id)
FROM careerpilot.analyses
WHERE created_at > NOW() - INTERVAL '7 days';

-- Most-used features
SELECT
  'analyses' AS feature, COUNT(*) AS usage
FROM careerpilot.analyses
UNION ALL
SELECT
  'interviews', COUNT(*)
FROM careerpilot.interviews;

-- Error log (from Sentry — export if needed)
```

### User feedback channels

- **Email**: if you set one up
- **GitHub Issues**: https://github.com/rpritiranjan90-crypto/careerpilot-ai/issues
- **In-app feedback**: Add a "Send Feedback" button (nice-to-have)

### Common feedback themes to expect

1. **AI quality**: "The analysis was generic" → Improve prompts or fine-tune
2. **Speed**: "It took too long" → Add caching, optimize AI calls
3. **UX**: "I couldn't find X" → Improve navigation
4. **Pricing**: "Will this stay free?" → Decide on monetization

---

## 3. First Month: Iterate

### Priority matrix

Use this to decide what to work on next:

| Impact \\ Effort | Low effort | High effort |
|------------------|------------|-------------|
| **High impact** | Do first | Plan carefully |
| **Low impact** | Do if time | Skip |

### Common post-launch priorities

1. **Add Sentry to frontend** (catch client-side errors)
2. **Improve AI prompts** based on user feedback
3. **Add caching** for repeated analyses (Redis, or in-memory)
4. **Optimize cold start** (Render free tier has 50s delay on first request)
5. **Add more file formats** (currently only pdf, docx, txt)
6. **Email notifications** (send results via email)
7. **Mobile responsiveness** (test on phones)

### Performance optimization

If Render metrics show high latency:

```python
# Add response caching in backend/app/api/*.py
from functools import lru_cache
import time

# Cache expensive AI results for 1 hour
@lru_cache(maxsize=100)
def get_cached_analysis(resume_hash: str, ttl: int = 3600):
    # ...
```

Or use Redis (free tier on Upstash: https://upstash.com/).

---

## 4. Growth (Month 2+)

### SEO basics

- Add meta tags to `frontend/index.html`
- Submit sitemap to Google Search Console
- Add OpenGraph tags for social sharing

### Content marketing

- Write blog posts: "How to optimize your resume for ATS"
- Create YouTube tutorials
- Share on LinkedIn, Twitter regularly

### Monetization (if desired)

Options:
- **Freemium**: Free tier with limits, paid for unlimited
- **One-time purchase**: $19 for "Pro" features
- **Subscription**: $9/mo for ongoing access
- **B2B**: Charge companies for bulk licenses

For MVP, **free is fine** — focus on usage and feedback.

### Scaling considerations

When you outgrow the free tier:
- **Render**: Upgrade to Standard ($7/mo per service) for no cold starts
- **Supabase**: Upgrade to Pro ($25/mo) for 7-day point-in-time recovery
- **Ollama**: Move to a dedicated server or use OpenAI/Anthropic API

---

## 5. Maintenance Schedule

| Frequency | Task |
|-----------|------|
| Daily | Check Sentry for new errors, respond to user feedback |
| Weekly | Take manual pg_dump backup, review Render metrics |
| Monthly | Review Sentry trends, update dependencies, security patches |
| Quarterly | Major feature releases, user research, roadmap planning |

### Dependency updates

```bash
# Backend
cd backend
pip list --outdated
# Update pyproject.toml, then rebuild Docker image

# Frontend
cd frontend
npm outdated
npm update
# Then rebuild
```

### Security patches

- Subscribe to: https://github.com/rpritiranjan90-crypto/careerpilot-ai/security/advisories
- Watch for: Supabase, FastAPI, React security advisories
- Update immediately for HIGH/CRITICAL severity

---

## 6. Success Metrics (3-month review)

At the 3-month mark, evaluate:

| Goal | Metric | Target |
|------|--------|--------|
| Product-market fit | Weekly active users (WAU) | 50+ |
| Engagement | Avg sessions per user | 3+ |
| Quality | Error-free session rate | > 95% |
| Performance | p95 page load time | < 3 seconds |
| Reliability | Uptime | > 99% |

If you're hitting these targets, you're ready to invest more (paid hosting, marketing, etc.).
If not, iterate on the most common user complaints first.

---

## 7. When to Ask for Help

You don't have to do this alone. Consider:

- **Technical co-founder**: If you want to scale faster
- **Designer**: To improve UX based on feedback
- **Marketing help**: To grow the user base
- **Open source contributors**: Add `CONTRIBUTING.md` to the repo

---

## 8. Celebrate! 🎉

You shipped a full-stack AI application to production. That's a huge accomplishment.

Take a moment to appreciate what you built:
- ✅ FastAPI backend with auth, DB, file uploads, AI integration
- ✅ React frontend with multiple pages and features
- ✅ Supabase integration for auth and data
- ✅ Docker containerization
- ✅ Production deployment on Render
- ✅ Security hardening
- ✅ Monitoring and alerting
- ✅ Documentation

That's a complete production-grade system. Well done!

---

## Next Steps

This is the end of the 14-step deployment roadmap. Future work is up to you:
- Iterate based on user feedback
- Add new features
- Scale as needed
- Or take what you learned and build something new!

Good luck! 🚀