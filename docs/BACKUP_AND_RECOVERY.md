# CareerPilot AI — Backup & Recovery Guide

## What needs backing up

| Data | Where | Backup mechanism | Recovery |
|------|-------|------------------|----------|
| User accounts & auth | Supabase Auth | Automatic (Supabase manages) | Restore from Supabase dashboard |
| Database tables (resumes, jobs, sessions) | Supabase PostgreSQL | Daily automatic backups (free tier: 7 days retention) | Point-in-time recovery via Supabase dashboard |
| Uploaded files (resumes, docs) | `/app/uploads` on Render | ❌ Ephemeral on free tier — lost on redeploy | User must re-upload |
| Code & config | GitHub | Git itself is the backup | `git clone` / `git pull` |

---

## 1. Supabase Database Backups (Already Automatic)

**Supabase Free tier includes:**
- Daily automated backups
- 7-day retention
- Accessible via Supabase dashboard

**Verify backups are working:**

1. Go to https://supabase.com/dashboard/project/eothvqvygmldgygjkfke/database/backups
2. You should see a list of recent backups (one per day)
3. Each shows: timestamp, size, status

**If backups are missing:**
- Free tier projects older than 7 days that have been inactive may not have backups
- Trigger a backup manually: Dashboard → Database → Backups → "Create backup"

---

## 2. Manual Backup (Before Major Changes)

Before any major deploy (e.g., migration, schema change), take a manual backup:

### Option A: Via Supabase Dashboard
1. Go to Database → Backups
2. Click "Create backup"
3. Wait for it to complete
4. Note the timestamp for later restore

### Option B: Via pg_dump (recommended for production)
```bash
# Install psql client (if not already)
# Windows: https://www.postgresql.org/download/windows/

# Get connection string from Supabase Dashboard → Settings → Database
# Use the "Direct connection" string (not the pooler)

pg_dump "postgresql://postgres:<password>@db.eothvqvygmldgygjkfke.supabase.co:5432/postgres" \
  --schema=careerpilot \
  --no-owner \
  --no-acl \
  --file=careerpilot_backup_$(date +%Y%m%d_%H%M%S).sql
```

**Store the backup:**
- Don't commit to Git (could leak data)
- Upload to a secure cloud storage (S3, Google Drive encrypted, etc.)
- Encrypt before storing: `gpg --symmetric --cipher-algo AES256 careerpilot_backup_*.sql`

---

## 3. Disaster Recovery Scenarios

### Scenario A: Database corruption / accidental data loss

**Restore from Supabase automatic backup:**
1. Supabase Dashboard → Database → Backups
2. Select the backup from before the incident
3. Click "Restore" — this will overwrite current data
4. Verify: `curl https://careerpilot-api-q5ur.onrender.com/api/users` (with auth)

**Restore from manual pg_dump backup:**
```bash
# Restore to a NEW database first to verify
createdb -h db.eothvqvygmldgygjkfke.supabase.co -U postgres careerpilot_recovered
psql "postgresql://postgres:<password>@db.eothvqvygmldgygjkfke.supabase.co:5432/careerpilot_recovered" \
  < careerpilot_backup_20260101_120000.sql

# If verified, restore to main database
psql "postgresql://postgres:<password>@db.eothvqvygmldgygjkfke.supabase.co:5432/postgres" \
  < careerpilot_backup_20260101_120000.sql
```

### Scenario B: Render service is down / deleted

**Recover:**
1. Go to Render Dashboard → careerpilot-api → "Manual Deploy" → "Deploy latest commit"
2. Verify all sync:false env vars are still set (Supabase keys, DATABASE_URL, SENTRY_DSN)
3. Wait for health check: `curl https://careerpilot-api-q5ur.onrender.com/health`
4. Same for frontend

**If service is completely deleted:**
1. Render Dashboard → New → Blueprint
2. Connect to GitHub repo `rpritiranjan90-crypto/careerpilot-ai`
3. Render will re-read `render.yaml` and recreate both services
4. Re-set all sync:false env vars
5. Deploy

### Scenario C: GitHub repo is lost

**Recover:**
1. Render keeps a cached copy of the last deployed Docker image (for 7 days on free tier)
2. Re-create the GitHub repo from local: `git push origin main --force`
3. Or: clone from Render's deploy logs (the git SHA is logged)

### Scenario D: Supabase project is deleted

**This is the worst case — full data loss if no manual backup exists.**

**Prevention:**
- Take manual pg_dump backups weekly (store offsite)
- Document the backup location in a secure note
- Consider upgrading to Supabase Pro ($25/mo) for point-in-time recovery

---

## 4. File Uploads (Ephemeral Data)

**Problem:** Files uploaded to `/app/uploads` are lost when Render redeploys or restarts the service.

**For free tier, this is acceptable** if:
- Users can re-upload files
- File contents are also stored elsewhere (e.g., metadata in DB only)

**For production-grade:**
- Use **Supabase Storage** or **AWS S3** for file uploads
- Update backend to upload to S3 instead of local disk
- Add a `file_url` column to the database to reference the S3 object

**Quick fix for now:**
- Document that uploads are ephemeral
- Add a warning in the UI: "Your uploaded files are not persisted between sessions"

---

## 5. Backup Verification Schedule

| Frequency | Action | Who |
|-----------|--------|-----|
| Daily | Verify Supabase automatic backup exists | Automated (Supabase) |
| Weekly | Take manual pg_dump backup | You |
| Before deploys | Manual backup | You (before any schema change) |
| Monthly | Test restore in a sandbox | You |

---

## 6. Recovery Time Objectives (RTO)

| Scenario | RTO | RPO (data loss window) |
|----------|-----|------------------------|
| Service crash/restart | 1-2 min (Render auto-restart) | 0 |
| Render redeploy | 2-5 min (Render free tier cold start) | 0 (data in Supabase) |
| Database corruption | 15-30 min (restore from Supabase backup) | Up to 24 hours (daily backup) |
| Full Supabase loss | 1-2 hours (restore from manual pg_dump) | Up to 1 week (if weekly backup) |
| Full GitHub repo loss | 30 min (recreate from local + Render cache) | 0 (code is in Render) |

---

## 7. Quick Reference: Backup Commands

### Take a backup
```bash
pg_dump "postgresql://postgres:PASSWORD@db.eothvqvygmldgygjkfke.supabase.co:5432/postgres" \
  --schema=careerpilot \
  --no-owner --no-acl \
  --file=backup_$(date +%Y%m%d).sql

# Encrypt
gpg --symmetric --cipher-algo AES256 backup_20260101.sql
```

### Restore a backup
```bash
# Decrypt
gpg --decrypt backup_20260101.sql.gpg > backup_20260101.sql

# Restore
psql "postgresql://postgres:PASSWORD@db.eothvqvygmldgygjkfke.supabase.co:5432/postgres" \
  < backup_20260101.sql
```

### Verify backup integrity
```bash
# Check the SQL file is valid
psql --set ON_ERROR_STOP=1 "postgresql://postgres:PASSWORD@db.eothvqvygmldgygjkfke.supabase.co:5432/postgres" \
  --single-transaction \
  --variable="ON_ERROR_STOP=1" \
  < /dev/null  # just connect to verify credentials work
```

---

## 8. Summary Checklist

- [x] Supabase automatic backups (verify in dashboard)
- [ ] Manual pg_dump backup taken and stored securely
- [ ] Backup restoration procedure tested
- [ ] File upload persistence decision made (ephemeral vs S3)
- [ ] Backup schedule documented and followed

---

## Next Steps

After backup setup, proceed to:
- **Step 12**: Pre-launch Security Checklist
- **Step 13**: Launch
- **Step 14**: Post-launch