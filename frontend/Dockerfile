# CareerPilot AI - Frontend Dockerfile
# Stage 1: build the static bundle with Vite.
# Stage 2: serve it with a hardened nginx config.

# ---------- Build stage ----------
FROM node:26-alpine AS build

WORKDIR /app

# Install deps first (better layer caching)
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci --no-audit --no-fund || npm install --no-audit --no-fund

# Copy source and build
COPY frontend/tsconfig.json frontend/vite.config.ts frontend/vitest.config.ts frontend/tailwind.config.js frontend/postcss.config.js frontend/index.html ./
COPY frontend/public ./public
COPY frontend/src ./src

# Build args for env vars baked at build time
ARG VITE_API_URL=http://backend:8000
ARG VITE_SUPABASE_URL
ARG VITE_SUPABASE_ANON_KEY
ARG VITE_DEV_TOKEN_AUTH=true
ARG VITE_APP_NAME=CareerPilot AI
ARG VITE_APP_VERSION=1.0.0

ENV VITE_API_URL=$VITE_API_URL \
    VITE_SUPABASE_URL=$VITE_SUPABASE_URL \
    VITE_SUPABASE_ANON_KEY=$VITE_SUPABASE_ANON_KEY \
    VITE_DEV_TOKEN_AUTH=$VITE_DEV_TOKEN_AUTH \
    VITE_APP_NAME=$VITE_APP_NAME \
    VITE_APP_VERSION=$VITE_APP_VERSION

RUN npm run build


# ---------- Runtime stage ----------
FROM nginx:1.27-alpine AS runtime

# Copy hardened root nginx config
COPY frontend/nginx.conf /etc/nginx/nginx.conf

# Copy the built bundle from the build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Create a non-root user for the nginx worker process.
# nginx master still runs as root (needed to bind port 80), but worker
# processes drop privileges. This limits the blast radius of any nginx bug.
RUN addgroup -g 1001 -S nginxgroup && \
    adduser -S nginxuser -u 1001 -G nginxgroup && \
    chown -R nginxuser:nginxgroup /usr/share/nginx/html && \
    chown -R nginxuser:nginxgroup /var/cache/nginx && \
    chown -R nginxuser:nginxgroup /var/log/nginx && \
    touch /var/run/nginx.pid && \
    chown nginxuser:nginxgroup /var/run/nginx.pid

# Run the nginx master as root (required for port 80), but workers as nginxuser.
# The master is trusted; the worker is sandboxed.
USER root

# Healthcheck (uses wget which is in the alpine base image)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -qO- http://localhost/ >/dev/null 2>&1 || exit 1

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
