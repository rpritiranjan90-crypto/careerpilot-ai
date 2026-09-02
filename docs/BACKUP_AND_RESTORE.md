# Backup and Restore

This document covers the operational procedures for backing up and restoring
a CareerPilot AI deployment. The system has two stateful components:

1. **PostgreSQL database** — application data
2. **Uploads volume** — user-uploaded resume files

## Automated backups (cron)

The simplest approach is a daily `pg_dump` of the database, plus a tarball of
the uploads volume. The example below assumes a Docker Compose deployment on
a single host.

### 1. Create a backup script

Save as `scripts/backup.sh` and `chmod +x`:

```bash
#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR=/var/backups/careerpilot
DATE=$(date -u +%Y%m%dT%H%M%SZ)
mkdir -p "$BACKUP_DIR"

# Database
docker compose exec -T db pg_dump -U postgres -Fc careerpilot \
    > "$BACKUP_DIR/db-$DATE.dump"

# Uploads (named volume)
docker run --rm \
    -v careerpilot-uploads:/uploads:ro \
    -v "$BACKUP_DIR":/backup \
    alpine:3.19 \
    tar czf "/backup/uploads-$DATE.tar.gz" /uploads

# Retention: keep 14 days
find "$BACKUP_DIR" -type f -mtime +14 -delete
```

### 2. Schedule it

```bash
# Daily at 03:17 UTC
echo "17 3 * * * /opt/careerpilot/scripts/backup.sh >> /var/log/careerpilot-backup.log 2>&1" \
    | sudo crontab -
```

## Restoring

### Restore the database

```bash
# Stop the backend (so it doesn't try to connect mid-restore)
docker compose stop backend

# Drop and recreate the DB
docker compose exec db dropdb -U postgres careerpilot --if-exists
docker compose exec db createdb -U postgres careerpilot

# Restore
cat db-20250912T031700Z.dump | docker compose exec -T db pg_restore -U postgres -d careerpilot

# Start everything
docker compose up -d
```

### Restore uploads

```bash
# Stop the backend
docker compose stop backend

# Restore files into the uploads volume
docker run --rm \
    -v careerpilot-uploads:/uploads \
    -v /var/backups/careerpilot:/backup:ro \
    alpine:3.19 \
    tar xzf /backup/uploads-20250912T031700Z.tar.gz -C /

# Restart
docker compose up -d
```

## Off-site / cloud backups

For production, copy the backup files to object storage (S3, GCS, B2) hourly
or use a managed service (e.g. Postgres logical replication to RDS, WAL-G,
or a managed PostgreSQL provider like Supabase, Neon, or RDS).

Example: copy to S3 with versioning enabled.

```bash
# Add to the backup script
aws s3 cp "$BACKUP_DIR/db-$DATE.dump" "s3://your-bucket/careerpilot/db/"
aws s3 cp "$BACKUP_DIR/uploads-$DATE.tar.gz" "s3://your-bucket/careerpilot/uploads/"
```

## Verifying a backup

**Test the restore at least once a quarter.** A backup you've never restored
is a backup you don't have.

```bash
# Spin up a test instance
docker compose -f docker-compose.yml -f docker-compose.test.yml up -d db
cat db-latest.dump | docker compose -f docker-compose.yml -f docker-compose.test.yml \
    exec -T db pg_restore -U postgres -d careerpilot

# Smoke-test: connect and SELECT
docker compose -f docker-compose.yml -f docker-compose.test.yml \
    exec db psql -U postgres -d careerpilot -c "SELECT count(*) FROM users;"
```

## Rollback (release)

If a deployment introduces a regression, the rollback procedure is:

1. `git revert` the offending merge commit and push
2. The CD pipeline rebuilds and pushes the previous image tag
3. On the server: `docker compose -f docker-compose.yml -f docker-compose.prod.yml pull && docker compose ... up -d`

Database migrations: the migration system is forward-only. To "rollback" a
schema change, write a new migration that undoes it. The application never
relies on a specific migration version — only the current schema.

## What this document does NOT cover

- Disaster recovery across regions (use managed Postgres + S3 cross-region replication)
- PITR (point-in-time recovery) — enable WAL archiving on Postgres for true PITR
- Encrypted backups — encrypt at rest in your object store; do not rely on disk encryption alone
