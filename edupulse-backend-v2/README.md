# EduPulse Backend v2 — Quick start

## Prerequisites
- Python 3.12+
- PostgreSQL 16 with pgvector extension
- Redis 7
- (Optional) OpenAI API key for LLM features

## Local Setup

```bash
# 1. Clone and navigate to backend
cd edupulse-backend-v2

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 4. Configure environment
copy .env.example .env
# Edit .env with your DB credentials and secrets

# 5. Start PostgreSQL and Redis
# Option A: Docker Compose (recommended)
docker-compose up -d postgres redis

# Option B: Local installation
# Make sure PostgreSQL has pgvector installed

# 6. Create schemas (run manually or via Alembic)
psql -U edupulse -d edupulse_v2 -c "CREATE SCHEMA IF NOT EXISTS registry; CREATE SCHEMA IF NOT EXISTS feedback; CREATE EXTENSION IF NOT EXISTS vector;"

# 7. Run Alembic migrations
alembic upgrade head

# 8. Seed the database
python seed_v2.py

# 9. Start the API server
uvicorn app.main:app --reload --port 8000

# 10. (Optional) Start the NLP worker in a separate terminal
python -m app.tasks.worker
```

## API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Demo Credentials
| Role       | Email                          | Password        |
|------------|--------------------------------|-----------------|
| Student    | student@college.edu            | Student@123     |
| Faculty    | faculty@college.edu            | Faculty@123     |
| HoD        | hod.computersc@college.edu     | HoD@Dept123     |
| Principal  | principal.gecthriss@college.edu | Principal@123  |
| University | university@keralaedu.in        | Kerala@Edu2025  |

## Run Tests
```bash
pytest tests/ -v --tb=short
```

## Docker Full Stack
```bash
docker-compose up --build
```

## Key API Endpoints
| Endpoint                                      | Method | Role        |
|-----------------------------------------------|--------|-------------|
| `/api/v2/auth/login`                          | POST   | All         |
| `/api/v2/auth/me`                             | GET    | Authenticated |
| `/api/v2/feedback/submit`                     | POST   | Student     |
| `/api/v2/feedback/status`                     | GET    | Student     |
| `/api/v2/faculty/me`                          | GET    | Faculty     |
| `/api/v2/faculty/list`                        | GET    | HoD+        |
| `/api/v2/analytics/departments`               | GET    | HoD+        |
| `/api/v2/analytics/clusters`                  | GET    | Principal+  |
| `/api/v2/analytics/health`                    | GET    | University+ |
| `/api/v2/recommendations/generate/{id}`       | POST   | Faculty+    |
| `/api/v2/recommendations/roadmap/{id}`        | GET    | Faculty+    |
| `/api/v2/admin/scoring/recompute-all`         | POST   | Admin       |
