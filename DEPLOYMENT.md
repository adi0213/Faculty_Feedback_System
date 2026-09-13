# EduPulse AI — Deployment Guide

This document covers deployment to Render (free tier), Railway, and manual VPS.

---

## Option 1: Render (Recommended — Free Tier)

### Backend (Web Service)

1. Go to [render.com](https://render.com) → **New Web Service**
2. Connect your GitHub repo: `adi0213/Faculty_Feedback_System`
3. **Root Directory:** `edupulse-backend-v2`
4. **Build Command:** `pip install -r requirements.txt`
5. **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6. **Environment Variables** — Add these in Render dashboard:

```
APP_ENV=production
APP_SECRET_KEY=<generate-strong-32char-secret>
DATABASE_URL=<your-postgresql-url>          # Render free PostgreSQL
HMAC_SECRET=<generate-16char-secret>
OPENAI_API_KEY=<your-openai-key>
LLM_ENABLED=true
K_ANONYMITY_THRESHOLD=5
APP_ALLOWED_ORIGINS=https://your-frontend.vercel.app
```

### Frontend (Static Site)

1. **New Static Site** on Render
2. **Root Directory:** `edupulse-react`
3. **Build Command:** `npm install && npm run build`
4. **Publish Directory:** `dist`
5. **Environment Variables:**

```
VITE_API_BASE_URL=https://your-backend.onrender.com/api/v2
```

---

## Option 2: Railway

```bash
# Install Railway CLI
npm install -g @railway/cli
railway login

# Deploy backend
cd edupulse-backend-v2
railway init
railway up

# Deploy frontend
cd ../edupulse-react
railway init
railway up
```

Set environment variables in Railway dashboard.

---

## Option 3: Manual VPS (Ubuntu 22.04)

### Backend Setup

```bash
# Clone repo
git clone https://github.com/adi0213/Faculty_Feedback_System.git
cd Faculty_Feedback_System/edupulse-backend-v2

# Python environment
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
nano .env   # Fill in all values

# Seed initial data
python seed_v2.py

# Run with systemd or PM2
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend Build

```bash
cd ../edupulse-react
npm install
echo "VITE_API_BASE_URL=https://your-domain.com/api/v2" > .env.production
npm run build
# Serve dist/ with nginx
```

### Nginx Config

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    location / {
        root /var/www/edupulse/dist;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## Option 4: Docker Compose (Full Stack)

```bash
git clone https://github.com/adi0213/Faculty_Feedback_System.git
cd Faculty_Feedback_System/edupulse-backend-v2

cp .env.example .env
# Edit .env with real values

docker-compose up -d
```

---

## Database Notes

- **Development**: SQLite (zero config, auto-created by `seed_v2.py`)
- **Production**: PostgreSQL — update `DATABASE_URL` in `.env`

After deploying backend, run the seeder once:
```bash
python seed_v2.py
```

This creates all test accounts and sample faculty data.

---

## After Deployment

1. Visit `https://your-backend/docs` to verify API is running
2. Visit your frontend URL and login with test accounts
3. Check `/health` endpoint for liveness: `GET /health` → `{"status": "ok"}`
