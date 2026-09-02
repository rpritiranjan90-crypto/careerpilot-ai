# CareerPilot AI — Production Deployment Roadmap & Master Guide

**Status**: 🔒 **LOCKED & PRODUCTION CERTIFIED**  
**Version**: 1.0.0  
**Stack**: FastAPI (Python 3.11/3.13) + React/TypeScript (Vite + TailwindCSS) + PostgreSQL 16 + Supabase Auth + Docker

---

## 🏗️ Architecture Overview

```
                                 [ Cloudflare / DNS / SSL ]
                                              │
                     ┌────────────────────────┴────────────────────────┐
                     │                                                 │
          HTTPS (Port 443 / 80)                             HTTPS (Port 443 / 80)
                     │                                                 │
                     ▼                                                 ▼
        ┌─────────────────────────┐                       ┌─────────────────────────┐
        │     Frontend Host       │                       │      Backend Host       │
        │ (Vercel / Cloudflare /  │                       │  (Render / Railway /    │
        │   Nginx Docker SPA)     │                       │    AWS / VPS Docker)    │
        └────────────┬────────────┘                       └────────────┬────────────┘
                     │                                                 │
                     │  Supabase Auth Token                            │  Verifies JWT Signature
                     ▼                                                 ▼
        ┌───────────────────────────────────────────────────────────────────────────┐
        │                         Supabase Cloud Platform                           │
        │  • Managed Auth (Email/Password & JWT)                                   │
        │  • Managed PostgreSQL 16 Database (Alembic Migrations 001-003)           │
        └───────────────────────────────────────────────────────────────────────────┘
                                              ▲
                                              │ REST / Coroutines
                                              ▼
                                 ┌─────────────────────────┐
                                 │     AI Inference        │
                                 │  • Fast Deterministic   │
                                 │  • Cloud LLM / Ollama   │
                                 └─────────────────────────┘
```

---

## 📋 Complete Step-by-Step Deployment Roadmap

### Step 1: Push Code to GitHub
1. Create a new private repository on [GitHub](https://github.com/new) named `careerpilot-ai` or `minor-project`.
2. Push your local workspace:
   ```bash
   git add .
   git commit -m "feat: complete production-hardened CareerPilot AI with Supabase Auth"
   git branch -M main
   git remote add origin https://github.com/<YOUR_USERNAME>/<YOUR_REPO_NAME>.git
   git push -u origin main
   ```
3. GitHub Actions (`.github/workflows/ci.yml`) will automatically trigger and run all 143 backend tests and 34 frontend tests.

---

### Step 2: Create Supabase Cloud Project (Auth + Database)
1. Go to [supabase.com](https://supabase.com) and create a free account.
2. Click **New Project**:
   * **Name**: `careerpilot-prod`
   * **Database Password**: *Choose a strong password and save it securely*.
   * **Region**: Select the closest region to you.
3. Once provisioned (takes ~1 minute), navigate to **Project Settings → API**:
   * Copy `Project URL` (e.g. `https://xyzcompany.supabase.co`)
   * Copy `anon public` key (`eyJhbGci...`)
   * Copy `JWT Secret` (`your-jwt-secret-string`)
4. Go to **Project Settings → Database**:
   * Copy the **Connection URI (Transaction / Session)**:
     `postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-ID].supabase.co:5432/postgres`

---

### Step 3: Run Database Migrations on Supabase
Execute the Alembic migrations against your live Supabase cloud database:

```bash
# In the backend directory:
$env:DATABASE_URL="postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-ID].supabase.co:5432/postgres"
alembic upgrade head
```
*(On Linux/macOS use `export DATABASE_URL=...`)*

This creates all tables, composite indexes, and GDPR cascade delete constraints.

---

### Step 4: Deploy Frontend (Vercel — Free)
1. Go to [vercel.com](https://vercel.com) and sign in with GitHub.
2. Click **Add New Project** and import your repository.
3. Configure the build settings:
   * **Framework Preset**: `Vite`
   * **Root Directory**: `frontend`
   * **Build Command**: `npm run build`
   * **Output Directory**: `dist`
4. Add **Environment Variables**:
   * `VITE_API_URL`: URL of your deployed backend (e.g. `https://careerpilot-api.onrender.com`)
   * `VITE_SUPABASE_URL`: `https://your-project.supabase.co`
   * `VITE_SUPABASE_ANON_KEY`: `your-anon-public-key`
5. Click **Deploy**. Vercel will build and assign an HTTPS URL (e.g. `https://careerpilot.vercel.app`).

---

### Step 5: Deploy Backend (Render — Free)
1. Go to [render.com](https://render.com) and sign in with GitHub.
2. Click **New +** → **Web Service** and connect your repository.
3. Configure settings:
   * **Name**: `careerpilot-api`
   * **Root Directory**: `backend`
   * **Runtime**: `Python 3` (or `Docker` using `backend/Dockerfile`)
   * **Build Command**: `pip install -r requirements.txt`
   * **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add **Environment Variables**:
   * `ENVIRONMENT`: `production`
   * `DEBUG`: `false`
   * `DATABASE_URL`: `postgresql://postgres:[PASSWORD]@db.[PROJECT-ID].supabase.co:5432/postgres`
   * `SUPABASE_URL`: `https://your-project.supabase.co`
   * `SUPABASE_JWT_SECRET`: `your-supabase-jwt-secret`
   * `DEV_TOKEN_AUTH`: `false`
   * `CORS_ORIGINS`: `["https://careerpilot.vercel.app"]`
   * `RATE_LIMIT_ANALYZE`: `20`
   * `RATE_LIMIT_GENERAL`: `120`
   * `AI_FALLBACK_ON_ERROR`: `true`
5. Click **Create Web Service**.

---

### Step 6: Post-Deployment Smoke Test
Verify the live deployment on your production URL:
1. Open `https://careerpilot.vercel.app`.
2. Register a new user via **Create Account**.
3. Upload a sample resume and view ATS analysis.
4. Run a job match and take a mock interview.
5. Check your personalized **Career Improvement Plan** at `/improve`.
6. Test GDPR deletion in `/settings`.
