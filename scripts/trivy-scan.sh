#!/usr/bin/env bash
# scripts/trivy-scan.sh
# Run a Trivy scan against the local Docker images and print a summary.
# Fails the build on CRITICAL findings.
#
# Usage:
#   ./scripts/trivy-scan.sh                    # scan both images
#   ./scripts/trivy-scan.sh backend            # scan only backend
#   ./scripts/trivy-scan.sh frontend           # scan only frontend
#   SEVERITY=HIGH ./scripts/trivy-scan.sh      # also fail on HIGH
set -euo pipefail

if ! command -v trivy >/dev/null 2>&1; then
  echo "Trivy is not installed."
  echo "Install: https://aquasecurity.github.io/trivy/latest/getting-started/installation/"
  exit 2
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is not installed or not on PATH."
  exit 2
fi

SEVERITY="${SEVERITY:-CRITICAL}"
TARGETS=("${@:-backend frontend}")

# Build the images if they don't exist.
for svc in "${TARGETS[@]}"; do
  case "$svc" in
    backend)  image="careerpilot-backend:scan"  ;;
    frontend) image="careerpilot-frontend:scan" ;;
    *) echo "Unknown service: $svc" >&2; exit 1 ;;
  esac

  if ! docker image inspect "$image" >/dev/null 2>&1; then
    echo "Building $image ..."
    docker build -t "$image" "./$svc"
  fi
done

exit_code=0
for svc in "${TARGETS[@]}"; do
  case "$svc" in
    backend)  image="careerpilot-backend:scan"  ;;
    frontend) image="careerpilot-frontend:scan" ;;
  esac

  echo ""
  echo "================================================================"
  echo " Trivy scan: $image"
  echo " Severity:  $SEVERITY"
  echo "================================================================"
  if ! trivy image \
        --severity "$SEVERITY" \
        --no-progress \
        --exit-code 1 \
        "$image"; then
    echo "❌ $image has $SEVERITY vulnerabilities" >&2
    exit_code=1
  else
    echo "✅ $image: no $SEVERITY vulnerabilities"
  fi
done

exit $exit_code
