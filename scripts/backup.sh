#!/usr/bin/env bash
# CareerPilot AI - automated backup script
# Usage: backup.sh [BACKUP_DIR]
#
# Backs up the PostgreSQL database (logical pg_dump) and the uploads volume
# to a local directory. Configure BACKUP_DIR or pass as first argument.
# S3 off-site copy is optional and requires the AWS CLI to be installed.

set -euo pipefail

BACKUP_DIR="${1:-${BACKUP_DIR:-/var/backups/careerpilot}}"
DATE="$(date -u +%Y%m%dT%H%M%SZ)"
RETENTION_DAYS="${RETENTION_DAYS:-14}"

mkdir -p "$BACKUP_DIR"

# ---------------------------------------------------------------------------
# Database (logical dump)
# ---------------------------------------------------------------------------
DB_DUMP="$BACKUP_DIR/db-$DATE.dump"
echo "[$(date -u +%H:%M:%S)] Backing up database -> $DB_DUMP"
if ! docker compose exec -T db pg_dump -U postgres -Fc careerpilot > "$DB_DUMP"; then
    echo "ERROR: database backup failed" >&2
    rm -f "$DB_DUMP"
    exit 1
fi
echo "[$(date -u +%H:%M:%S)] Database backup complete ($(du -h "$DB_DUMP" | cut -f1))"

# ---------------------------------------------------------------------------
# Uploads (named volume)
# ---------------------------------------------------------------------------
UPLOADS_TAR="$BACKUP_DIR/uploads-$DATE.tar.gz"
echo "[$(date -u +%H:%M:%S)] Backing up uploads volume -> $UPLOADS_TAR"
if ! docker run --rm \
    -v careerpilot-uploads:/uploads:ro \
    -v "$BACKUP_DIR":/backup \
    alpine:3.19 \
    tar czf "/backup/uploads-$DATE.tar.gz" /uploads 2>/dev/null; then
    echo "WARN: uploads backup failed (volume may not exist yet)" >&2
    rm -f "$UPLOADS_TAR"
fi
if [[ -f "$UPLOADS_TAR" ]]; then
    echo "[$(date -u +%H:%M:%S)] Uploads backup complete ($(du -h "$UPLOADS_TAR" | cut -f1))"
fi

# ---------------------------------------------------------------------------
# Optional S3 off-site copy
# ---------------------------------------------------------------------------
if [[ -n "${S3_BUCKET:-}" ]] && command -v aws >/dev/null 2>&1; then
    echo "[$(date -u +%H:%M:%S)] Copying backups to S3 s3://$S3_BUCKET"
    aws s3 cp "$DB_DUMP" "s3://$S3_BUCKET/db/" || echo "WARN: S3 db copy failed" >&2
    if [[ -f "$UPLOADS_TAR" ]]; then
        aws s3 cp "$UPLOADS_TAR" "s3://$S3_BUCKET/uploads/" || echo "WARN: S3 uploads copy failed" >&2
    fi
fi

# ---------------------------------------------------------------------------
# Retention
# ---------------------------------------------------------------------------
echo "[$(date -u +%H:%M:%S)] Pruning backups older than $RETENTION_DAYS days"
find "$BACKUP_DIR" -type f -mtime +"$RETENTION_DAYS" -name "*.dump" -delete
find "$BACKUP_DIR" -type f -mtime +"$RETENTION_DAYS" -name "*.tar.gz" -delete

echo "[$(date -u +%H:%M:%S)] Backup complete"
