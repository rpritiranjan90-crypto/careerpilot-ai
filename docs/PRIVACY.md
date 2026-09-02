# Privacy & Data Retention

This document covers what personal data CareerPilot AI collects, how it is used,
how long it is retained, and how users can exercise their rights.

---

## 1. What Data We Collect

### 1.1 Data You Provide Directly

| Data | Where Stored | Purpose |
|------|--------------|---------|
| Email address | `users.email` | Account identification |
| Display name (optional) | `users.name` | Personalization |
| Resume files (PDF/DOCX/TXT) | `/app/uploads/` + `resumes.extracted_text` | Resume analysis |
| Job descriptions | `job_descriptions.description` | Job matching |
| Interview answers | `interview_questions.answer` | Interview feedback |
| AI-generated results | `resume_analyses.result_json`, `job_matches.result_json`, `interview_questions.evaluation_json` | History / dashboard |

### 1.2 Data Collected Automatically

| Data | Where | Purpose |
|------|-------|---------|
| Authenticated user ID (from JWT `sub` claim) | Logs, audit | Authorization |
| Request ID (UUID) | Logs | Correlation |
| IP address | Access logs (Nginx) | Rate limiting, security |
| User-Agent header | Access logs | Browser-quirk debugging |
| Timestamp | Logs | Audit trail |

We do **not** use third-party analytics, tracking pixels, or cookies for
advertising.

---

## 2. How Data Is Used

- **Resume & job data** is sent to the local Ollama model (or your configured AI
  provider) to generate analyses. By default Ollama runs on the same host as
  the API; in production this should be either a local model or a contractually
  vetted cloud provider.
- **Auth tokens** are validated locally using a shared secret (HS256). We do
  not call out to a third-party identity provider on every request.
- **Logs** are retained for 30 days for security and incident response.

---

## 3. Data Retention

| Data Type | Retention | Justification |
|-----------|-----------|---------------|
| Account / email | Until account deleted | Service operation |
| Resumes + extracted text | Until account deleted OR 90 days of inactivity, whichever comes first | Stale data minimization |
| AI analyses / matches | Until account deleted | User value |
| Interview sessions | Until account deleted | User value |
| Server access logs | 30 days | Security incident response |
| Database backups | 30 days (configurable) | Disaster recovery |
| Error logs (application) | 90 days | Debugging |
| Aggregated metrics (no PII) | 1 year | Capacity planning |

### Automated Cleanup

Set the following environment variables to enable scheduled cleanup:

```bash
# In production .env
DATA_RETENTION_INACTIVE_DAYS=90
LOG_RETENTION_DAYS=30
BACKUP_RETENTION_DAYS=30
```

A nightly cron should run:

```sql
-- Delete users inactive for >90 days and their data
DELETE FROM users WHERE updated_at < NOW() - INTERVAL '90 days';
```

Cascading foreign keys will remove all child rows.

---

## 4. Your Rights (GDPR / CCPA / LGPD)

| Right | How to Exercise |
|-------|-----------------|
| Right to access | `GET /api/users/me` (TBD) returns all stored data |
| Right to rectification | Update via Supabase Auth UI |
| Right to erasure | `DELETE /api/users/me` — see below |
| Right to data portability | `GET /api/users/me/export` (TBD) returns JSON dump |
| Right to restriction | Contact privacy@careerpilot.example |
| Right to object | Contact privacy@careerpilot.example |

### Account Deletion

To permanently delete your account and all associated data:

```bash
curl -X DELETE https://api.careerpilot.example/api/users/me \
  -H "Authorization: Bearer $TOKEN"
```

This is **irreversible** and removes:
- The user record
- All uploaded resumes (both the file on disk and the database row)
- All resume analyses
- All job descriptions and matches
- All interview sessions and questions

### Data Export

To download all your data in a portable JSON format:

```bash
curl https://api.careerpilot.example/api/users/me/export \
  -H "Authorization: Bearer $TOKEN" \
  -o my-data.json
```

---

## 5. Where Data Is Stored

- **Database**: PostgreSQL 16 (configurable)
- **Resume files**: Local filesystem (`UPLOAD_DIR=/app/uploads`) — encrypted at
  rest in production via LUKS / cloud-provider block-device encryption
- **Logs**: stdout (collected by Docker, then forwarded by your log shipper)
- **Backups**: PostgreSQL `pg_dump`, copied off-site to S3-compatible storage

In production, ensure:
- Database disks are encrypted at rest
- Backups are encrypted before upload (the backup script supports
  `BACKUP_ENCRYPTION_KEY`)
- TLS 1.2+ is enforced on all connections
- Database access is restricted to the application subnet (security group / VPC)

---

## 6. Subprocessors

| Provider | Purpose | Data Shared | Region |
|----------|---------|-------------|--------|
| Supabase | Authentication | Email, password hash | EU / US (configurable) |
| Ollama (self-hosted) | AI inference | Resume text, job description, interview answers | Same host |
| Your cloud provider | Hosting, DB, blob storage | All data | Per deployment |

If you swap any of these (e.g., to a hosted LLM), update this list and notify
users per your DPA obligations.

---

## 7. Security Measures

See [SECURITY.md](SECURITY.md) for the full security architecture. In summary:

- TLS 1.2+ enforced
- JWT authentication on all `/api/*` routes
- Per-user authorization (IDOR tests in CI)
- Per-user rate limiting
- File upload validation (extension, MIME, magic bytes, size)
- Parameterized SQL queries (SQLAlchemy ORM)
- Structured logging with no PII in URLs
- Encrypted backups with off-site storage

---

## 8. Contact

For privacy questions or to exercise your rights:
**privacy@careerpilot.example**

We respond to verified requests within 30 days.
