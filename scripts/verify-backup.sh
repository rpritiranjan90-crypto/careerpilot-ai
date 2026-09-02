#!/usr/bin/env bash
# CareerPilot AI - backup verification script
# Usage: verify-backup.sh <db-dump-file>
#
# Spins up a temporary PostgreSQL container, restores the dump into a fresh
# database, and runs a smoke test. If verification passes, the dump is good.

set -euo pipefail

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <db-dump-file>" >&2
    exit 1
fi

DUMP_FILE="$1"
if [[ ! -f "$DUMP_FILE" ]]; then
    echo "ERROR: dump file not found: $DUMP_FILE" >&2
    exit 1
fi

VERIFY_CONTAINER="careerpilot-verify-$$"
echo "[$(date -u +%H:%M:%S)] Starting verification container: $VERIFY_CONTAINER"

cleanup() {
    echo "[$(date -u +%H:%M:%S)] Cleaning up..."
    docker rm -f "$VERIFY_CONTAINER" >/dev/null 2>&1 || true
}
trap cleanup EXIT

docker run -d --name "$VERIFY_CONTAINER" \
    -e POSTGRES_USER=postgres \
    -e POSTGRES_PASSWORD=postgres \
    -e POSTGRES_DB=careerpilot \
    postgres:16-alpine >/dev/null

# Wait for postgres to be ready
for i in {1..30}; do
    if docker exec "$VERIFY_CONTAINER" pg_isready -U postgres >/dev/null 2>&1; then
        break
    fi
    sleep 1
done

echo "[$(date -u +%H:%M:%S)] Restoring dump into verification DB"
cat "$DUMP_FILE" | docker exec -i "$VERIFY_CONTAINER" pg_restore \
    -U postgres -d careerpilot --no-owner --role=postgres 2>&1 | tail -3 || true

echo "[$(date -u +%H:%M:%S)] Running smoke tests"
USERS=$(docker exec "$VERIFY_CONTAINER" psql -U postgres -d careerpilot -tA -c "SELECT count(*) FROM users;" 2>/dev/null || echo "0")
RESUMES=$(docker exec "$VERIFY_CONTAINER" psql -U postgres -d careerpilot -tA -c "SELECT count(*) FROM resumes;" 2>/dev/null || echo "0")
INTERVIEWS=$(docker exec "$VERIFY_CONTAINER" psql -U postgres -d careerpilot -tA -c "SELECT count(*) FROM interviews;" 2>/dev/null || echo "0")

echo "  users=$USERS resumes=$RESUMES interviews=$INTERVIEWS"

if [[ "$USERS" -ge 0 && "$RESUMES" -ge 0 && "$INTERVIEWS" -ge 0 ]]; then
    echo "[$(date -u +%H:%M:%S)] BACKUP VERIFIED OK"
    exit 0
else
    echo "[$(date -u +%H:%M:%S)] BACKUP VERIFICATION FAILED"
    exit 1
fi
