#!/usr/bin/env bash
# scripts/cleanup-stale-data.sh
#
# Daily data-retention sweep. Intended to be run from cron at 03:00 UTC.
#
# - Deletes users who haven't updated in DATA_RETENTION_INACTIVE_DAYS
#   (default: 90). CASCADE FKs remove their resumes, analyses, interviews, etc.
# - Prunes application and access logs older than LOG_RETENTION_DAYS (default: 30)
# - Logs the count of rows deleted to /var/log/careerpilot/cleanup.log
#
# Required env:
#   DATABASE_URL  – PostgreSQL connection string
#
# Optional env:
#   DATA_RETENTION_INACTIVE_DAYS  (default 90)
#   LOG_RETENTION_DAYS           (default 30)
#   LOG_DIR                      (default /var/log/careerpilot)
set -euo pipefail

INACTIVE_DAYS="${DATA_RETENTION_INACTIVE_DAYS:-90}"
LOG_DAYS="${LOG_RETENTION_DAYS:-30}"
LOG_DIR="${LOG_DIR:-/var/log/careerpilot}"
LOG_FILE="${LOG_DIR}/cleanup.log"

mkdir -p "$LOG_DIR"

log() {
  echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] $*" | tee -a "$LOG_FILE"
}

log "Starting cleanup (inactive_days=$INACTIVE_DAYS, log_days=$LOG_DAYS)"

if [ -z "${DATABASE_URL:-}" ]; then
  log "ERROR: DATABASE_URL is not set; aborting."
  exit 1
fi

# Count before deletion (for the log)
INACTIVE_COUNT=$(psql "$DATABASE_URL" -tAc "
SELECT COUNT(*) FROM users
WHERE COALESCE(updated_at, created_at) < NOW() - INTERVAL '${INACTIVE_DAYS} days';
")
log "Inactive users to delete: $INACTIVE_COUNT"

if [ "$INACTIVE_COUNT" -gt 0 ]; then
  psql "$DATABASE_URL" -c "
DELETE FROM users
WHERE COALESCE(updated_at, created_at) < NOW() - INTERVAL '${INACTIVE_DAYS} days';
" >> "$LOG_FILE" 2>&1
  log "Deleted $INACTIVE_COUNT inactive user(s) and their data."
else
  log "No inactive users; skipping."
fi

# Prune old log files
DELETED_LOGS=$(find "$LOG_DIR" -type f \( -name "*.log" -o -name "*.log.*" \) -mtime +"$LOG_DAYS" -print -delete | wc -l)
log "Pruned $DELETED_LOGS log file(s) older than ${LOG_DAYS} days."

log "Cleanup complete."
