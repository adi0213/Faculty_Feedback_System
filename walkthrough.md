# EduPulse React App — Agentic Faculty Evaluation System
**Project Location**: [D:/Faculty_feedback_system/edupulse-react/](file:///d:/Faculty_feedback_system/edupulse-react/)

---

## What Was Built

The Faculty Evaluation System has been completely rebuilt using **React (Vite)**, featuring a premium **Bento Grid × Skeuomorphism** blended design. The app uses client-side routing, React Context for authentication, and Recharts for all data visualizations.

---

## Screenshots

````carousel
![React Login Screen](C:\Users\Asus\.gemini\antigravity-ide\brain\6467957e-c539-4878-bacd-319210230479\login_screen_1784566499686.png)
<!-- slide -->
![React Faculty Dashboard](C:\Users\Asus\.gemini\antigravity-ide\brain\6467957e-c539-4878-bacd-319210230479\faculty_dashboard_1784566522468.png)
````

---

## Technical Stack
- **Framework**: React 18 + Vite
- **Routing**: React Router DOM v6
- **Styling**: CSS Modules with custom design tokens (`index.css`)
- **Charts**: Recharts (Radar, Line, Bar, Area, Pie)
- **Data**: LocalStorage mock database (`db.js`)

---

## Project Structure

```
edupulse-react/src/
├── context/
│   └── AuthContext.jsx      ← Global auth state provider
├── data/
│   ├── db.js                ← LocalStorage DB with mock users/faculties
│   ├── engine.js            ← Adaptive questioning logic
│   └── advisor.js           ← AI course matching & task plans
├── components/
│   ├── DashboardLayout/     ← Sidebar + Topbar wrapper
│   └── Card/                ← Skeuomorphic Bento Card component
├── pages/
│   ├── Login/               ← Split-panel login with demo credentials
│   ├── Student/             ← 3-screen adaptive feedback flow
│   ├── Faculty/             ← Self-dashboard with AI advisor panel
│   ├── HoD/                 ← Dept roster & performance comparison
│   ├── Principal/           ← College-wide KPI & dept breakdown
│   └── University/          ← System-wide metrics & FDP impact
├── App.jsx                  ← Route definitions
├── main.jsx                 ← Entry point
└── index.css                ← Global skeuomorphic design tokens
```

---

## Core Features

### 🧠 Adaptive Question Engine (Fixed & Integrated)
- Located in [engine.js](file:///d:/Faculty_feedback_system/edupulse-react/src/data/engine.js).
- Evaluates 6 core dimensions.
- If a student selects a negative option (value ≤ 2), the engine dynamically injects a dimension-specific follow-up sub-question.
- The total number of questions shown is strictly capped at **10**.

### 🤖 AI Improvement Advisor
- Scans faculty scores to identify dimensions below `3.5`.
- Automatically maps weak dimensions to NPTEL/SWAYAM courses.
- Generates a **4-week phase-based task plan** (Diagnose → Restructure → Practice → Evaluate).

### 🎨 Design System
- **Bento Grid Layout**: Responsive 12-column CSS Grid.
- **Skeuomorphism**: Layered inner and drop shadows to simulate depth, soft lighting gradients, and subtle paper grain textures.
- **Typography**: Playfair Display (Serif headers), Inter (Sans-serif body), JetBrains Mono (Data).

---

## Login Credentials (Demo)

| Role | Email | Password |
|------|-------|----------|
| 🎓 Student | `student@college.edu` | `student123` |
| 👨‍🏫 Faculty | `faculty@college.edu` | `faculty123` |
| 🏛️ HoD | `hod@college.edu` | `hod123` |
| 🎩 Principal | `principal@college.edu` | `principal123` |
| 🌐 University | `university@edu.in` | `univ123` |

---

## How to Run

1. Open a terminal in `d:\Faculty_feedback_system\edupulse-react`
2. Run `npm run dev`
3. Open the provided `localhost` URL (usually `http://localhost:5173/`) in your browser.

> [!TIP]
> The dev server is already running in the background. You can navigate directly to [http://localhost:5173/](http://localhost:5173/) to see it.
