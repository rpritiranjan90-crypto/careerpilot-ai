# Deployment Guide

Detailed step-by-step instructions for deploying CareerPilot AI to a production environment.

## Table of Contents

- [Pre-flight checklist](#pre-flight-checklist)
- [Option A: Docker Compose on a single VPS](#option-a-docker-compose-on-a-single-vps)
- [Option B: Container registry + managed runtime](#option-b-container-registry--managed-runtime)
- [Option C: Kubernetes (high availability)](#option-c-kubernetes-high-availability)
- [Environment-specific notes](#environment-specific-notes)
- [Health checks & observability](#health-checks--observability)
- [Backups](#backups)
- [Rollback](#rollback)
- [Troubleshooting](#troubleshooting)

---

## Pre-flight checklist

Before deploying to production, confirm:

- [ ] Domain name is registered and DNS A records are pointed to your server
- [ ] TLS certificates are available (Let's Encrypt, AWS ACM, etc.)
- [ ] Supabase project is created, tables exist, and service role key is secured
- [ ] Ollama (if used) is reachable from your application
- [ ] `ENVIRONMENT=production` and `DEBUG=false` in your environment
- [ ] `CORS_ORIGINS` contains only your actual domain(s)
- [ ] Strong passwords for any database / secret values
- [ ] Backups are configured (see [Backups](#backups))

---

## Option A: Docker Compose on a single VPS

**Best for:** small teams, MVP deployments, cost-sensitive setups.

### 1. Provision a server

- 1 vCPU, 2 GB RAM minimum (4 GB recommended if running Ollama)
- Ubuntu 24.04 LTS or Debian 12
- Open ports: 22 (SSH), 80 (HTTP), 443 (HTTPS)
- A non-root user with `sudo` access

### 2. Initial server setup

```bash
# SSH in
ssh deploy@your-server-ip

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker deploy
newgrp docker

# Verify
docker --version
docker compose version
```

### 3. Clone and configure

```bash
git clone https://github.com/your-org/career-pilot-ai.git
cd career-pilot-ai
cp .env.example .env
nano .env   # fill in your values
```

Required `.env` values for production:

```bash
ENVIRONMENT=production
DEBUG=false

CORS_ORIGINS=https://your-domain.com

SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=<your-anon-key>
SUPABASE_SERVICE_ROLE_KEY=<your-service-role-key>

OLLAMA_BASE_URL=http://ollama-internal:11434  # or your Ollama endpoint
```

### 4. (Optional) Set up TLS with Let's Encrypt

```bash
# Add an nginx sidecar or use a host-level reverse proxy
# Simplest: install certbot
sudo apt install certbot
sudo certbot certonly --standalone -d your-domain.com
```

Then point a host-level Nginx to forward 80/443 to the docker-compose stack.

### 5. Deploy

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml pull
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
docker compose logs -f   # tail logs
```

### 6. Verify

```bash
# Health checks
curl https://your-domain.com/health
# → {"status":"ok","version":"1.0.0",...}

curl https://your-domain.com/api/resumes/analyze -X POST \
  -H "Content-Type: application/json" \
  -d '{"resume_text":"Experienced Python developer with FastAPI and React."}'
```

### 7. (Recommended) Auto-restart on reboot

```bash
sudo systemctl enable docker
# docker compose services are already configured with `restart: unless-stopped`
```

---

## Option B: Container registry + managed runtime

**Best for:** teams that want zero-server management.

### Push images

Images are automatically pushed to **GitHub Container Registry** by the `cd.yml` workflow on every successful CI run.

```bash
# Pull an image
docker pull ghcr.io/your-org/careerpilot-frontend:latest
docker pull ghcr.io/your-org/careerpilot-backend:latest
```

### Deploy to a platform

The images work with any OCI-compatible runtime:

- **AWS ECS / Fargate** – point a task definition at the images
- **Google Cloud Run** – `gcloud run deploy --image ghcr.io/...`
- **Azure Container Apps** – `az containerapp create --image ghcr.io/...`
- **Fly.io** – `flyctl deploy --image ghcr.io/...`
- **Railway / Render** – point the service at the image URL

**Required environment variables** in your platform's secrets manager:

```
APP_NAME=CareerPilot AI
ENVIRONMENT=production
DEBUG=false
CORS_ORIGINS=https://your-domain.com
SUPABASE_URL=...
SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_ROLE_KEY=...
OLLAMA_BASE_URL=...
UPLOAD_DIR=/app/uploads
MAX_UPLOAD_SIZE_MB=5
ALLOWED_EXTENSIONS=pdf,docx,txt
RATE_LIMIT_ANALYZE=20
RATE_LIMIT_INTERVIEW=30
```

**Frontend** needs the following build args at build time (the workflow already does this):

```
VITE_API_URL=https://api.your-domain.com
VITE_SUPABASE_URL=...
VITE_SUPABASE_ANON_KEY=...
VITE_APP_NAME=CareerPilot AI
VITE_APP_VERSION=1.0.0
```

---

## Option C: Kubernetes (high availability)

**Best for:** large teams, multi-region, high-traffic deployments.

Reference manifests coming soon. The Docker images work as-is; you only need:

- **Deployment** for backend (3+ replicas)
- **Deployment** for frontend (2+ replicas)
- **Service** (ClusterIP) for backend
- **Service** (ClusterIP) for backend metrics
- **Ingress** with TLS for the frontend
- **ConfigMap / Secret** for environment variables
- **HorizontalPodAutoscaler** based on CPU/memory
- **PodDisruptionBudget** for safe rollouts

---

## Environment-specific notes

### Staging

- Use staging Supabase project (separate from production)
- Higher logging verbosity (`LOG_LEVEL=DEBUG` is fine)
- Test data only – never use real user data
- Branch-deploy preview URLs supported via Docker tags

### Production

- `ENVIRONMENT=production`, `DEBUG=false`
- Structured JSON logs (automatically enabled)
- Restricted CORS (`https://your-domain.com` only)
- Secrets in a managed secrets store (AWS Secrets Manager, GCP Secret Manager, etc.)
- HTTP→HTTPS redirect at the load balancer
- Database backups automated (see below)
- Monitoring enabled (Prometheus, Datadog, etc.)

---

## Health checks & observability

### Liveness probe

```bash
GET /health
```

Returns `200 {"status":"ok",...}` if the API process is up.

### Readiness probe

```bash
GET /health/ready
```

Returns `200` only when all dependencies (DB, Ollama) are reachable. Returns `503` otherwise.

### Metrics (Prometheus)

```bash
GET /metrics
```

Returns Prometheus text format. Built-in metrics:

- `http_requests_total{method,path,status}`
- `http_request_duration_seconds{method,path}` (histogram)
- `http_request_errors_total{method,path,status}`
- `process_uptime_seconds`

Example Prometheus scrape config:

```yaml
scrape_configs:
  - job_name: careerpilot
    scrape_interval: 15s
    static_configs:
      - targets: ['api.your-domain.com']
```

### Logs

- **Development:** human-readable colored output
- **Production:** structured `key=value` lines, easy to ship to:
  - AWS CloudWatch (use the JSON log driver)
  - GCP Cloud Logging
  - Datadog
  - Grafana Loki
  - Any log aggregator

Each log line includes a `request_id` so you can trace a request end-to-end.

---

## Backups

### Database (if using local PostgreSQL)

```bash
# Daily backup script
docker exec careerpilot-db pg_dump -U postgres careerpilot | \
  gzip > /backups/careerpilot-$(date +%F).sql.gz
```

Or use [pgBackRest](https://pgbackrest.org/) for incremental backups.

### Uploaded files

The `uploads/` volume is mounted as a named Docker volume. Back it up with:

```bash
docker run --rm \
  -v careerpilot-uploads:/source:ro \
  -v /backups:/backup \
  alpine tar czf /backup/uploads-$(date +%F).tar.gz -C /source .
```

### Configuration

Keep your `.env` file in a secrets manager, **not** in git. Each environment (staging/prod) has its own.

---

## Rollback

### Docker Compose

```bash
# Pin to a previous image tag
export BACKEND_IMAGE=ghcr.io/your-org/careerpilot-backend:v1.0.0
export FRONTEND_IMAGE=ghcr.io/your-org/careerpilot-frontend:v1.0.0
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Kubernetes

```bash
kubectl rollout undo deployment/careerpilot-backend
kubectl rollout undo deployment/careerpilot-frontend
```

### Database

If a migration broke something, restore from the most recent backup:

```bash
docker exec -i careerpilot-db psql -U postgres careerpilot < backup.sql
```

---

## Troubleshooting

### "Cannot connect to backend"

1. Check `docker compose ps` – are all services healthy?
2. Check `docker compose logs backend` for errors
3. Verify `CORS_ORIGINS` matches the domain the frontend is served from
4. From the frontend container: `docker compose exec frontend wget -qO- http://backend:8000/health`

### "Resume upload returns 413"

File is too large. Increase `MAX_UPLOAD_SIZE_MB` in `.env` and restart. Also raise `client_max_body_size` in nginx.conf.

### "Health check returns degraded"

Check `/health/ready` for individual dependency status. If database is failing:
1. Verify `DATABASE_URL` is correct
2. Check that the database is reachable from the backend container
3. Check logs: `docker compose logs backend | grep -i "database\|sql"`

### "Logs are noisy"

Set `LOG_LEVEL=INFO` (or `WARNING`) in `.env` to silence debug output.

### "I need to run without Docker"

See the [Local Development](../README.md#local-development) section in the main README.
