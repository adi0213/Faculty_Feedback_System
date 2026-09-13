# Kerala Faculty Feedback & Improvement System — Architecture Blueprint

## Executive Summary

This document outlines a faculty feedback system for Kerala's state higher
education institutions, designed around four non‑negotiable principles:

1. **De‑identification by construction** — student identity and feedback
   content are technically separated at the database/role level, not just by
   policy.
2. **Statistically defensible scoring** — objective and subjective signals
   are combined using cohort‑relative normalization, outlier control, and
   Empirical Bayes shrinkage, so a faculty member is never judged on a
   handful of unrepresentative responses.
3. **Corrective, not punitive, by legal design** — the system produces
   formative reports with concrete development pathways (methodology
   changes, NPTEL/SWAYAM certifications), not disciplinary scores, and this
   distinction is backed by an explicit governance instrument, not just
   intent.
4. **Government infrastructure, not a vendor product** — built to run on
   state/NIC infrastructure, integrated with existing accreditation
   requirements (NAAC Student Satisfaction Survey) rather than competing
   with them, with a separate licensing track reserved for self‑financing
   institutions later.

---

## 1. Positioning and Institutional Anchoring

Rather than launching as a standalone new mandate, anchor the system to
infrastructure that already exists and already carries institutional
weight:

- **NAAC's Student Satisfaction Survey (SSS)** is already a mandatory input
  for accreditation. Position this system as the official digital
  instrument that *fulfils* that requirement with richer, AI‑assisted
  analysis — this converts "another portal to comply with" into "the tool
  that already does what we must do anyway."
- **Likely institutional home**: Department of Higher Education / Kerala
  State Higher Education Council (or equivalent state academic governance
  body), in partnership with the state IT implementation agency (e.g.
  Kerala State IT Mission / NIC Kerala) for hosting and security
  certification. Universities (e.g. KTU, Kerala University, Calicut
  University) act as the academic governance layer above individual
  colleges.
- **Stakeholder council before code**: a standing oversight committee with
  faculty‑association representation, student‑union representation, and
  IQAC coordinators should approve the question instrument, the scoring
  weights, and the release thresholds *before* the pilot. Faculty buy‑in is
  the single biggest determinant of whether this succeeds politically — a
  system perceived as imposed top‑down invites boycott or gaming.
- **Phased licensing for private institutions** is a separate downstream
  decision (Section 11) — keep that commercial path architecturally
  possible (multi‑tenant from day one) without conflating it with the
  government rollout.

## 2. Governance and Legal Considerations

- **Data protection**: design for compliance with India's Digital Personal
  Data Protection Act, 2023 — explicit purpose limitation (formative
  feedback only), defined retention periods, and a documented lawful basis
  (likely framed as part of the institution's academic‑quality function
  rather than individual consent per submission, given the operational
  need for mandatory participation).
- **Non‑punitive ring‑fencing**: this needs a Government Order or equivalent
  binding instrument stating that system‑generated scores cannot be used as
  the *sole* basis for adverse service action against a faculty member.
  Reports should explicitly route into a **Faculty Development Program
  (FDP) / mentoring pathway**, with any disciplinary process — if ever
  triggered — required to go through existing, independent service rules
  and due process, with this system's output treated as one input among
  several, not a verdict.
- **Defamation/liability exposure from free‑text comments**: define and
  publish moderation rules (a comment alleging a specific criminal act, for
  instance, should route to a separate grievance/vigilance process, not
  appear verbatim in a routine report).
- **Security certification**: government portals handling personal data in
  India typically require an independent security audit (e.g. CERT‑In
  empanelled auditor) before public launch — budget time and cost for this
  from the outset, not as an afterthought.

## 3. System Architecture

The system is organized into six layers, with anonymization treated as a
structural boundary rather than a single feature:

```
Student-Facing Layer → Anonymization & Code Registry → Core Data &
Processing → AI/LLM Layer (codes-only) → Role-Based Dashboards →
Audit & Compliance (cross-cutting)
```

See `system_architecture.mermaid` for the full component diagram. Key
points:

- **Identity verification happens once, at the edge.** A student
  authenticates via college SSO / existing student database to prove
  enrollment, and the Token Service immediately issues a one‑time,
  non‑reversible response token (HMAC‑derived). No table downstream of the
  token issuance step contains a student identifier.
- **The AI/LLM layer never has a path to identity‑bearing tables.** This is
  enforced with separate database schemas and role‑based grants (see
  `database_schema.sql`), so "anonymized data only" is a property of the
  access control system, not a coding convention someone could forget.
- **Dashboards read only pre‑aggregated, gated outputs** — never raw
  responses — regardless of which authority level is viewing them.

## 4. Anonymization Protocol

Step by step, for a single feedback submission:

1. Student logs in through the college's existing SSO/ERP credential.
2. The **Enrollment Verification Service** confirms the student is
   genuinely enrolled in the specific course/section/term being rated
   (prevents non‑enrolled or duplicate voting) — this check happens against
   the *existing* student database; no new identity store is created for
   feedback purposes.
3. The **Token Service** issues a single‑use pseudonymous token for that
   (student, course, term) triple, generated via a keyed HMAC so it cannot
   be reversed to the student without a separate secret key held by a
   different custodian (e.g. registrar/IT‑cell split custody — no single
   party can unilaterally de‑anonymize).
4. The student submits objective ratings + free‑text comment, tagged only
   with `token`, `faculty_code`, `course_code`, `term_code`.
5. **k‑Anonymity gate**: a faculty/course/term combination only produces a
   releasable report once it has at least *k* responses (recommended
   starting point: k = 5–8, calibrated during the pilot). Below that
   threshold, no report — individual or aggregate — is generated, since
   small samples both bias scores and risk re‑identifying a vocal
   minority's comments.
6. For very small comment samples that do clear the k‑anonymity threshold,
   consider paraphrasing/clustering free‑text excerpts in the faculty
   report (rather than verbatim quoting) to reduce the chance that a
   distinctively worded comment is traceable to one student.

## 5. Portal Layout / Information Architecture

**Public landing**: what the system is, the non‑punitive policy statement,
FAQ, grievance‑redressal contact — transparency here is what earns
legitimacy with both faculty and students.

**Student flow** (logged in):
- My enrolled courses this term → Select course → Feedback form
  (objective Likert block + optional free‑text) → Confirmation (no score
  shown back to the student — this is not a public rating site).

**Faculty dashboard** (private, self‑only):
- Overview: current‑term composite score band (not a raw punitive number —
  see Section 6.4) and trend across terms.
- Dimension breakdown: where the formative detail lives (clarity,
  fairness, pacing, etc.) with the underlying (de‑identified, clustered)
  comment themes.
- Suggested actions: methodology suggestions and matched NPTEL/SWAYAM
  certification recommendations.
- Response‑count and confidence indicator, so the faculty member can see
  how statistically stable their score is.

**HoD / Principal dashboard**:
- Department roster with score bands (not raw ranks — see Section 8) and
  flags (temporal‑clustering anomalies, low‑response‑count courses needing
  encouragement to participate).
- Cohort comparisons to contextualize any single faculty's standing.

**University / State authority dashboard**:
- Aggregated, anonymized‑at‑the‑faculty‑level system health: participation
  rates, dimension‑level trends across institutions, FDP uptake and
  correlation with subsequent score movement (closing the "corrective, not
  punitive" loop with evidence).
- No individual faculty drill‑down by default; any escalation beyond
  aggregate view requires a logged, authorized, due‑process‑triggered
  access request (captured in the Audit layer).

## 6. Scoring Methodology

### 6.1 Objective Score

Use a multi‑dimensional Likert instrument (1–5) rather than a single
"overall rating" — this is what makes the report formative rather than
just evaluative. Suggested starting dimensions and sample items (refine
with the oversight committee and pilot data):

| Dimension | Sample item |
|---|---|
| Clarity | "The instructor explains concepts in a way I can follow." |
| Punctuality | "Classes start/end on schedule and the full allotted hours are conducted." |
| Fairness | "Internal assessments and grading are applied consistently." |
| Approachability | "The instructor is accessible for doubt‑clearing outside class hours." |
| Methodology | "The instructor uses examples, demonstrations, or teaching aids effectively." |
| Pacing | "The syllabus is covered at an appropriate pace without rushing near the end." |

Dimension weights should be derived empirically from pilot data (e.g. via
factor analysis or an expert‑elicited weighting such as the Analytic
Hierarchy Process), not hard‑coded as equal weights by default.

### 6.2 Subjective (Sentiment) Score

Free‑text comments are processed through an aspect‑based sentiment
pipeline: each comment is classified by polarity (typically −1 to +1) *and*
tagged to the dimension(s) it addresses, so a comment about fairness
doesn't get blended anonymously into an overall "vibe" score. Given Kerala
classrooms, the NLP pipeline needs to handle Malayalam, English, and
Malayalam‑English code‑mixed text — a multilingual model (e.g. an
IndicBERT/MuRIL‑family model, or a general LLM prompted carefully) should
be evaluated against locally collected pilot comments before being locked
in.

### 6.3 Bias and "Revenge Rating" Correction

This is the part most rating systems get wrong, so it deserves the most
rigor:

- **Winsorizing** (capping, not deleting, extreme values at the 5th/95th
  percentile within each dimension) blunts the effect of a burst of
  spite‑driven 1‑star ratings without discarding genuine signal.
- **Cohort‑relative z‑score normalization**: compare a faculty member's
  score against peers teaching structurally similar courses (same
  department, course level, term) rather than against a single global
  average — this controls for the fact that inherently harder or
  compulsory courses systematically attract lower satisfaction regardless
  of teaching quality.
- **Empirical Bayes shrinkage**: for courses with few respondents, shrink
  the raw score toward the cohort mean —

  `Shrunk_Score = (n / (n + k)) × Faculty_Mean + (k / (n + k)) × Cohort_Mean`

  where `n` is the response count and `k` is a governance‑set "equivalent
  prior sample size" (start around 8, calibrate on pilot variance). This is
  the same logic used in any small‑sample rating problem — a handful of
  votes, friendly or hostile, cannot swing the score far from a defensible
  baseline.
- **Temporal‑cluster flagging**: if a disproportionate share of extreme‑low
  ratings arrive within a short window of each other (e.g. immediately
  after a grade release), flag the course for human review rather than
  silently excluding the data — this preserves both fairness and
  auditability.
- **Non‑constructive comment filtering**: classify comments as
  substantive‑critique vs. personal‑attack/non‑actionable; report the count
  of the latter separately and exclude them from the sentiment score, while
  never deleting them outright (they remain available for grievance
  processes if needed).

### 6.4 Composite Score and Confidence Reporting

`Composite = α × Objective_Corrected + (1 − α) × Sentiment_Corrected`

`α` is a **governance parameter**, reviewed periodically by the oversight
committee — not an engineering default buried in code (a reasonable
starting point is α ≈ 0.7, weighting structured ratings somewhat higher
than free‑text sentiment, but this should be revisited against pilot
outcomes).

Rather than displaying a bare numeric score (which invites exactly the
ranking‑culture dynamics RateMyProfessor is criticized for), display
**bands** (e.g. "Strong," "Developing," "Needs Support") derived from
control limits around the cohort distribution, alongside a **confidence
indicator** based on response count and variance. This nudges the system
toward "where do I stand and what should I work on" rather than "what is my
number versus everyone else's."

## 7. AI/LLM Integration Pattern

- Every payload sent to an LLM (whether a hosted API or a self‑hosted open
  model) contains only `faculty_code`, `course_code`, `department_code`,
  numeric ratings, and de‑identified comment text — never a name, roll
  number, or anything from the registry schema. This is enforced at the
  database role level (Section 9 / `database_schema.sql`), so it can't be
  violated by an oversight in application code.
- Given data‑sovereignty expectations for a government system, evaluate
  **self‑hosting an open‑weight model** (e.g. via a local inference server
  on state/NIC infrastructure) for the sentiment and report‑drafting steps,
  rather than routing every comment through a third‑party API — this trades
  some capability for full data control, and is worth the trade‑off for a
  state‑run education system.
- **Human‑in‑the‑loop before publication**: AI‑drafted suggestions
  (methodology changes, certification matches) should be reviewed by an
  IQAC coordinator or academic mentor before a report is finalized — this
  guards against tone‑deaf or hallucinated suggestions reaching a faculty
  member without context, and is important for the system's credibility.
- **NPTEL/SWAYAM matching**: maintain a periodically refreshed catalog of
  NPTEL/SWAYAM course metadata (title, domain, level — not full course
  content), and match it to a faculty member's weak dimensions/subject area
  using semantic similarity (embedding‑based search) between the matched
  themes and course descriptions, surfaced as suggestions, not mandates.

## 8. Statistical Insights and Analytics Layer

- **Longitudinal tracking** of each faculty's dimension scores across
  terms — the system's real value is in *trend*, not a single snapshot.
- **Banding instead of ranking**: use control‑chart‑style limits (e.g.
  based on cohort mean ± a multiple of robust standard deviation) to
  classify into bands rather than publishing ordinal leaderboards, which
  invite gaming and morale damage without commensurate benefit.
- **Clustering** (e.g. k‑means over dimension‑score vectors) to identify
  common patterns across faculty — e.g. a cluster strong on content but
  weak on engagement — to target FDP topics efficiently rather than
  one‑size‑fits‑all training.
- **Dimension‑outcome regression**: identify which dimensions most predict
  negative sentiment overall, to prioritize what institutional training
  investment actually moves the needle.
- **Outcome‑loop tracking**: correlate FDP/certification completion with
  subsequent score movement — this is the evidence base that makes
  "corrective, not punitive" credible over time, to faculty and to
  policymakers alike.
- **System health metrics** for administrators: participation rate by
  college/department (a low rate undermines validity and should itself be
  a tracked KPI), anomaly counts, and report‑generation latency.

## 9. Report Content by Audience

| Audience | Content | Excluded |
|---|---|---|
| Faculty (self) | Score band + trend, dimension breakdown, comment themes (clustered/paraphrased if n is small), specific methodology suggestions, NPTEL/SWAYAM matches, confidence indicator | Comparison to named peers |
| HoD / Principal | Department roster with bands, cohort comparisons, participation rates, anomaly/review flags | Raw comments, raw response‑level data |
| University / State | Aggregated trends across institutions, FDP‑uptake/outcome correlation, system health KPIs | Any individually identifiable faculty drill‑down outside an authorized, audited escalation process |

## 10. Recommended Technology Stack

| Layer | Suggestion | Rationale |
|---|---|---|
| Frontend | React/Next.js PWA, Malayalam + English i18n, WCAG‑accessible | Mobile‑first usage pattern expected among students |
| Backend | Modular monolith to start (Python/FastAPI or Node/NestJS) | Easier to audit and secure than a sprawling microservice mesh at government scale; split into services later if load demands it |
| Primary DB | PostgreSQL, with `registry` and `feedback` schemas physically/logically separated (Section 9) | Native row/column‑level GRANT support makes the anonymization boundary enforceable, not just documented |
| Queue/Async | RabbitMQ or a lightweight task queue for the sentiment‑analysis pipeline | Decouples submission latency from NLP processing time |
| NLP/LLM | Multilingual model evaluated on real Malayalam/English/code‑mixed pilot comments; self‑hosted option assessed for sovereignty | Generic English‑only sentiment models will under‑perform on Kerala's actual comment text |
| Hosting | State data centre / NIC "MeghRaj" GI Cloud, or equivalent in‑country government infrastructure | Data sovereignty and public trust for a state‑run education system |
| Security audit | CERT‑In empanelled auditor (or equivalent) before public launch | Standard requirement for Indian government‑facing portals handling personal data |

## 11. Rollout Plan

1. **Phase 0 — Stakeholder co‑design**: oversight committee formed with
   faculty‑association, student‑union, and IQAC representation; question
   instrument and scoring weights drafted *with* them, not announced *to*
   them.
2. **Phase 1 — Pilot**: a small set of willing colleges/courses, real data
   used to calibrate `α`, `k` (shrinkage prior), and the k‑anonymity
   threshold; NLP model evaluated against actual pilot comments.
3. **Phase 2 — Single‑university rollout**: full integration with the
   NAAC SSS requirement for that university; outcome‑loop tracking
   (FDP → score movement) begins generating the evidence base for the
   non‑punitive framing.
4. **Phase 3 — State‑wide govt/aided rollout**, with the Government Order
   on non‑punitive use formally in place before this phase, not after.
5. **Phase 4 (optional, separate track) — Private/self‑financing licensing
   model**, spun out as a distinct commercial/legal entity if pursued, kept
   architecturally possible via multi‑tenancy from day one but politically
   and legally separate from the government deployment.

## 12. Risk Register

| Risk | Mitigation |
|---|---|
| Faculty distrust / perceived surveillance | Co‑design, transparent non‑punitive policy, FDP‑routing instead of scores‑only output |
| Student collusion to inflate/deflate scores | k‑anonymity gate, temporal‑cluster flagging, one‑token‑per‑student‑per‑course enforcement |
| Re‑identification via distinctive comments | Comment clustering/paraphrasing in small‑n reports, k‑anonymity threshold |
| AI hallucination in suggestions | Human‑in‑the‑loop review (IQAC coordinator) before report finalization |
| Future misuse for disciplinary action | Government Order explicitly limiting use, independent due‑process requirement |
| Low participation undermining statistical validity | Track participation as a system‑health KPI; consider integrating submission into an existing mandatory academic workflow (e.g. tied to NAAC SSS completion) |
| Security breach of identity‑mapping data | Schema/role separation (Section 9), encryption at rest, CERT‑In‑grade audit before launch |

## 13. Reference Implementation Files

Three accompanying files demonstrate the concepts above concretely:

- `system_architecture.mermaid` — the full component diagram (Section 3).
- `scoring_engine.py` — a runnable Python reference implementation of
  Winsorizing, cohort z‑scores, Empirical Bayes shrinkage, temporal‑cluster
  flagging, and the composite score (Section 6).
- `database_schema.sql` — PostgreSQL DDL demonstrating the `registry` vs.
  `feedback` schema separation and role‑based grants that make
  "AI sees codes only" an enforced property of the database, not a promise
  in documentation (Sections 4 and 7).
