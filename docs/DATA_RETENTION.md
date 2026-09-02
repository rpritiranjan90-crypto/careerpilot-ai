# Data Retention Policy

This document defines how long different categories of data are retained in
CareerPilot AI and the operational procedures for enforcing retention.

## Categories

| Category | Default Retention | Configurable | Justification |
|----------|-------------------|--------------|---------------|
| User account data | Until deletion | No | Service operation |
| Resumes + extracted text | Until deletion OR 90d inactive | `DATA_RETENTION_INACTIVE_DAYS` | Storage minimization |
| AI analyses | Until deletion | No | User value |
| Job descriptions | Until deletion | No | User value |
| Interview sessions | Until deletion | No | User value |
| Application logs | 30 days | `LOG_RETENTION_DAYS` | Incident response |
| Database backups | 30 days | `BACKUP_RETENTION_DAYS` | Disaster recovery |
| Access logs (Nginx) | 30 days | N/A | Security |
| Aggregated metrics | 1 year | N/A | Capacity planning |

## Implementation

### Nightly Cleanup Job (cron)

Add the following to your production crontab:

```cron
# Run cleanup at 03:00 UTC daily
0 3 * * * cd /opt/careerpilot && ./scripts/cleanup-stale-data.sh >> /var/log/careerpilot/cleanup.log 2>&1
```

### `scripts/cleanup-stale-data.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

INACTIVE_DAYS="${DATA_RETENTION_INACTIVE_DAYS:-90}"
LOG_DAYS="${LOG_RETENTION_DAYS:-30}"

# Delete users who haven't been active in INACTIVE_DAYS.
# CASCADE on FKs will remove resumes, analyses, interviews, etc.
psql "$DATABASE_URL" -c "
DELETE FROM users
WHERE updated_at < NOW() - INTERVAL '${INACTIVE_DAYS} days';
" | tee -a /var/log/careerpilot/cleanup.log

# Prune old log files
find /var/log/careerpilot -type f -name "*.log" -mtime +"$LOG_DAYS" -delete
find /var/log/careerpilot -type f -name "*.log.*" -mtime +"$LOG_DAYS" -delete

# Prune old backups (the backup script does this too, but a belt-and-suspenders
# pass is cheap and protects against missed rotations)
find /var/backups/careerpilot -type f -mtime +30 -delete

echo "Cleanup completed at $(date -u +'%Y-%m-%dT%H:%M:%SZ')"
```

### Backup Retention

The `scripts/backup.sh` script rotates daily/weekly/monthly tiers:

- Daily: kept 7 days
- Weekly: kept 4 weeks
- Monthly: kept 12 months

All backups older than `BACKUP_RETENTION_DAYS` are garbage-collected after each
backup run.

## Manual Verification

To check what would be deleted without actually deleting:

```sql
-- Find inactive users
SELECT id, email, updated_at
FROM users
WHERE updated_at < NOW() - INTERVAL '90 days';

-- Counts by table
SELECT 'users' AS table_name, COUNT(*) FROM users WHERE updated_at < NOW() - INTERVAL '90 days'
UNION ALL
SELECT 'resumes', COUNT(*) FROM resumes WHERE created_at < NOW() - INTERVAL '90 days';
```

## Exceptions

Some data may be retained longer for legal/regulatory reasons:

- **Tax / accounting records** — 7 years (if applicable)
- **Security incident logs** — 1 year or per legal requirement
- **Backups containing user data** — retention governed by `BACKUP_RETENTION_DAYS`

When retention must exceed the standard period for legal reasons, document the
exception in the `LEGAL_HOLD` table:

```sql
CREATE TABLE legal_hold (
    id UUID PRIMARY KEY,
    user_id VARCHAR NOT NULL REFERENCES users(id),
    reason TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL
);
```

The cleanup job must skip users with an active legal hold.
