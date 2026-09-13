# EduPulse AI — Faculty Feedback & Development Platform

<div align="center">
  <img src="https://img.shields.io/badge/Python-3.12-blue?logo=python" />
  <img src="https://img.shields.io/badge/FastAPI-0.115-green?logo=fastapi" />
  <img src="https://img.shields.io/badge/React-18-61DAFB?logo=react" />
  <img src="https://img.shields.io/badge/Vite-8-646CFF?logo=vite" />
  <img src="https://img.shields.io/badge/License-MIT-yellow" />
  <img src="https://img.shields.io/badge/DPDP_Act_2023-Compliant-green" />
</div>

---

> **EduPulse AI** is an AI-powered, privacy-compliant faculty evaluation and professional development platform built for Kerala Higher Education institutions (KTU). It collects anonymous student feedback, scores it statistically, and generates AI-driven improvement plans for faculty.

## ✨ Key Features

- 🔒 **Anonymous feedback** — HMAC pseudonymization, no student identity stored
- 📊 **Statistical scoring** — Winsorizing + Empirical Bayes shrinkage
- 🤖 **AI recommendations** — RAG-based course matching + GPT-4o-mini roadmaps
- 👥 **6 Role-based portals** — Student, Faculty, HoD, Principal, University, Admin
- 🛡️ **DPDP Act 2023 compliant** — K-anonymity, purpose limitation, audit trail
- 📈 **Real-time dashboards** — Recharts visualizations with trend analysis

## 🏗️ Project Structure

```
Faculty_Feedback_System/
├── edupulse-backend-v2/     # FastAPI Python backend (port 8000)
│   ├── app/
│   │   ├── ai/              # NLP: Sentiment, ABSA, RAG, Spam detection
│   │   ├── models/          # SQLAlchemy ORM models
│   │   ├── routers/         # API route handlers
│   │   ├── services/        # Scoring, recommendations, auth services
│   │   └── main.py          # FastAPI application factory
│   ├── seed_v2.py           # Database seeder with test accounts
│   ├── requirements.txt
│   └── .env.example
│
└── edupulse-react/          # React 18 + Vite frontend (port 5173)
    └── src/
        ├── pages/           # Student, Faculty, HoD, Principal, University portals
        ├── components/      # Shared UI components
        ├── context/         # Auth context
        └── data/            # API client (db.js) + advisor engine
```

## 🚀 Quick Start

### Backend

```bash
cd edupulse-backend-v2
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux

pip install -r requirements.txt
cp .env.example .env            # Fill in your values
python seed_v2.py               # Seed test data
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd edupulse-react
npm install
cp .env.example .env.local      # Fill in your values
npm run dev                     # → http://localhost:5173
```

### API Docs
Open [http://localhost:8000/docs](http://localhost:8000/docs) for interactive Swagger UI.

## 👤 Test Accounts

| Role       | Email                      | Password       |
|------------|---------------------------|----------------|
| Student    | `student@college.edu`     | `student123`   |
| Faculty    | `faculty@college.edu`     | `faculty123`   |
| HoD        | `hod@college.edu`         | `hod123`       |
| Principal  | `principal@college.edu`   | `principal123` |
| University | `university@ktu.edu`      | `university123`|
| Admin      | `admin@edupulse.ai`       | `admin123`     |

## 🔧 Environment Variables

Copy `edupulse-backend-v2/.env.example` to `edupulse-backend-v2/.env` and fill in:

| Variable | Description |
|---|---|
| `DATABASE_URL` | SQLite (dev) or PostgreSQL URL (prod) |
| `APP_SECRET_KEY` | Min 32-char secret for JWT signing |
| `HMAC_SECRET` | Min 16-char secret for student pseudonymization |
| `OPENAI_API_KEY` | Required for AI course recommendations |
| `LLM_ENABLED` | `false` to disable LLM (uses rule-based fallback) |

## 🏛️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI 0.115, Python 3.12, SQLAlchemy 2.0 |
| Database | SQLite (dev) / PostgreSQL 15+ (prod) |
| Auth | JWT HS256 + bcrypt |
| AI/NLP | GPT-4o-mini, ABSA, TF-IDF RAG, VADER Sentiment |
| Frontend | React 18, Vite, Recharts, CSS Modules |

## 🌐 Hosting

See [DEPLOYMENT.md](DEPLOYMENT.md) for full deployment instructions (Render, Railway, Vercel).

## 📄 License

MIT License — see [LICENSE](LICENSE)

---

*Built for Kerala Higher Education · DPDP Act 2023 Compliant · Version 2.0.0*
