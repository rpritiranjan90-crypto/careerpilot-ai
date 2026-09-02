#!/usr/bin/env bash
# scripts/restore.sh
# Usage: restore.sh <dump-file> [--yes]
#
# Restores a pg_dump logical backup into the running db container.
# --yes skips the confirmation prompt (safe for automation/cron).
set -euo pipefail

YES=false
DUMP_FILE=""

for arg in "$@"; do
  case "$arg" in
    --yes) YES=true ;;
    *)     DUMP_FILE="$arg" ;;
  esac
done

if [[ -z "$DUMP_FILE" ]]; then
  echo "Usage: $0 <dump-file> [--yes]" >&2
  echo "Example: $0 /var/backups/careerpilot/db-20250912T031700Z.dump" >&2
  exit 1
fi

if [[ ! -f "$DUMP_FILE" ]]; then
  echo "ERROR: dump file not found: $DUMP_FILE" >&2
  exit 1
fi

if [[ "$YES" != "true" ]]; then
  echo "WARNING: this will drop and recreate the 'careerpilot' database."
  echo "Dump file: $DUMP_FILE"
  echo "Press Enter to continue, Ctrl-C to abort..."
  read -r
fi

echo "[$(date -u +%H:%M:%S)] Stopping backend"
docker compose stop backend 2>/dev/null || true

echo "[$(date -u +%H:%M:%S)] Dropping and recreating database"
docker compose exec -T db dropdb -U postgres careerpilot --if-exists || true
docker compose exec -T db createdb -U postgres careerpilot

echo "[$(date -u +%H:%M:%S)] Restoring dump"
cat "$DUMP_FILE" | docker compose exec -T db pg_restore \
  -U postgres -d careerpilot --no-owner --role=postgres

echo "[$(date -u +%H:%M:%S)] Restarting backend"
docker compose up -d backend

echo "[$(date -u +%H:%M:%S)] Verifying row counts"
sleep 3
docker compose exec db psql -U postgres -d careerpilot -c \
  "SELECT count(*) AS users FROM users; SELECT count(*) AS resumes FROM resumes;"

echo "[$(date -u +%H:%M:%S)] Restore complete."
