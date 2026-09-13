# Agentic Faculty Evaluation System — Implementation Plan

A fully browser-based, single-codebase faculty feedback system built in pure HTML/CSS/JS (no backend required for the demo), featuring an **agentic adaptive question engine**, **role-based dashboards**, and **AI-generated improvement suggestions**.

---

## Design Direction

- **Theme**: Bento Grid UI + Skeuomorphism blend (paper textures, card depth, real shadows, glass overlay accents)
- **Color Palette**: Deep teal (`#0D2B2B`), warm parchment (`#F5F0E8`), gold accent (`#C9954A`), sage green (`#5C7A66`)
- **Typography**: `Playfair Display` (serif headings), `Inter` (body), `JetBrains Mono` (data/codes)
- **Animations**: Subtle card lifts, question transitions (fade+slide), progress bar morphing, chart animations

---

## Architecture: All-in-One HTML SPA

The entire system is a single `index.html` with multiple page states managed by JavaScript.

### Pages / Screens

| Screen | Purpose |
|---|---|
| `landing.html` | Public landing with login options |
| `login.html` | Shared login with role detection |
| `student/feedback.html` | Adaptive 10-question form with branching |
| `faculty/dashboard.html` | Self-only result + AI suggestions |
| `hod/dashboard.html` | Department roster + analytics |
| `principal/dashboard.html` | College-wide view |
| `university/dashboard.html` | System-wide overview |

> [!IMPORTANT]
> All pages are separate HTML files in a structured folder for clean navigation

---

## Proposed File Structure

```
EduPulse/
├── index.html                  ← Landing page
├── login.html                  ← Shared login
├── assets/
│   ├── css/
│   │   ├── main.css            ← Core design tokens + utilities
│   │   ├── bento.css           ← Bento grid + card components
│   │   └── skeuomorph.css      ← Texture, shadow, depth effects
│   ├── js/
│   │   ├── app.js              ← Router + session management
│   │   ├── data.js             ← Mock data store (localStorage)
│   │   ├── engine.js           ← Adaptive question engine
│   │   └── ai.js               ← AI suggestion generator (rule-based + GPT-style)
│   └── img/
│       └── (generated assets)
├── student/
│   └── feedback.html           ← Adaptive feedback form
├── faculty/
│   └── dashboard.html          ← Faculty self-view
├── hod/
│   └── dashboard.html          ← HoD department view
├── principal/
│   └── dashboard.html          ← Principal college view
└── university/
    └── dashboard.html          ← University aggregate view
```

---

## Core Feature: Adaptive Question Engine

### Logic (engine.js)
- Start with a pool of 20 subject-specific questions
- Serve question 1–10 adaptively:
  - If student selects a **negative option** (Poor / Unsatisfactory / Needs Improvement) on question N → inject a **follow-up sub-question** specific to that dimension next
  - Replace the next scheduled question with the sub-question
  - Total count always stays at exactly **10 questions shown**
- Each question has 4 options: `Excellent`, `Good`, `Needs Improvement`, `Poor`
- Sub-questions are pre-mapped to each main question's topic area

### Sample Question Pool (per subject dimension)
| # | Dimension | Main Question |
|---|---|---|
| 1 | Clarity | "How clearly does the faculty explain concepts?" |
| 2 | Methodology | "Does the faculty use effective teaching methods?" |
| 3 | Punctuality | "Does the faculty conduct classes on time?" |
| 4 | Fairness | "Are internal marks awarded fairly?" |
| 5 | Approachability | "Is the faculty available for doubt-clearing?" |
| 6 | Coverage | "Is the syllabus covered at an appropriate pace?" |
| 7 | Engagement | "Does the faculty make classes interactive?" |
| 8 | Practical | "Are practical/lab sessions conducted effectively?" |
| 9 | Assessment | "Are assignments/tests reasonable and clear?" |
| 10 | Overall | "Would you recommend this faculty to juniors?" |

Sub-questions for negative responses:
- Clarity → "Which specific topic was hardest to understand?"
- Methodology → "What teaching method would help you more?"
- Fairness → "What aspect of assessment felt unfair?"
- etc.

---

## Role-Based Login System

| Role | Username | Password | Landing |
|---|---|---|---|
| Student | student@college.edu | student123 | /student/feedback.html |
| Faculty | faculty@college.edu | faculty123 | /faculty/dashboard.html |
| HoD | hod@college.edu | hod123 | /hod/dashboard.html |
| Principal | principal@college.edu | principal123 | /principal/dashboard.html |
| University | university@edu.in | univ123 | /university/dashboard.html |

---

## AI Suggestions Engine (ai.js)

Rule-based suggestion generator triggered when faculty score falls below threshold:

### If score < 3.0 on any dimension:
- **Clarity** → Suggest NPTEL "Teaching Techniques for STEM" + 4-week daily task plan
- **Methodology** → Suggest SWAYAM "Active Learning Strategies" + weekly task plan
- **Fairness** → Suggest workshops on assessment design
- **Approachability** → Suggest mentoring habits guide + weekly check-in tasks

### Output format:
1. **6-Month Course Recommendation** (NPTEL/SWAYAM matched)
2. **4-Week Weekly Task Plan** (specific, actionable weekly goals)
3. Score trend projection if tasks completed

---

## Dashboards Design

### Faculty Dashboard (Bento Grid)
- Large score band card (top-left, wide)
- Radar chart: Dimensions vs department average
- Trend line chart: Score across semesters
- Comment theme chips
- AI Suggestion panel (glassmorphism card)
- 6-month course recommendation cards (3-column bento)
- 4-week task tracker

### HoD Dashboard
- 4 KPI cards (participation %, faculty count, flags, low-n courses)
- Faculty roster table with band pills
- Bar chart: Dept vs University dimension averages
- Alert panel for flagged courses

### Principal Dashboard
- Department comparison chart
- College-wide band distribution
- Department-level roster

### University Dashboard
- Statewide participation metrics
- Band distribution (horizontal bar)
- FDP completion vs score movement chart
- College onboarding tracker

---

## Verification Plan

### Manual Verification
1. Log in as each role and verify correct redirect
2. Complete student feedback form — verify 10 questions total, sub-question triggers on negative selection
3. Check faculty dashboard shows score + AI suggestion when score is low
4. Verify HoD/Principal/University dashboards show appropriate aggregated data
5. Test responsive layout on mobile viewport
