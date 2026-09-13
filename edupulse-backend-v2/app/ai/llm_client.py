"""
LLM client using LiteLLM for provider-agnostic access.
Handles structured prompt templates, retry logic, response parsing,
and mock mode for development/testing.
"""
import json
import logging
from dataclasses import dataclass, field
from typing import Any

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# ── Prompt Templates ──────────────────────────────────────────────────────────

RECOMMENDATION_PROMPT = """You are an expert faculty development advisor for Kerala Higher Education institutions.
You are analyzing ANONYMIZED feedback data (no student or faculty names) to generate evidence-based improvement recommendations.

FACULTY CONTEXT (anonymized):
- Department: {dept}
- Subject Area: {subject}
- Score Band: {score_band} (composite score: {composite_score}/5)
- Response Count: {response_count}

WEAK DIMENSIONS (lowest-scoring areas):
{weak_dimensions}

FLAGGED FEEDBACK THEMES (from NLP analysis):
{feedback_themes}

RETRIEVED COURSE OPTIONS:
{course_options}

Based on the above, generate a JSON response with this exact structure:
{{
  "recommendations": [
    {{
      "course_title": "<exact title from retrieved courses>",
      "target_dimension": "<primary dimension this addresses>",
      "confidence_score": <0.0-1.0>,
      "justification": "<2-3 sentences explaining why this course addresses the identified issues>",
      "learning_outcomes_summary": "<1-2 sentences on what the faculty will be able to do after completing this>",
      "expected_impact": "<1-2 sentences on how student feedback is expected to improve>"
    }}
  ],
  "root_cause_analysis": "<2-3 paragraphs analyzing the pattern of weak dimensions and likely underlying causes>",
  "executive_summary": "<1 paragraph overall assessment and main recommendation>"
}}

IMPORTANT: Only recommend courses from the RETRIEVED COURSE OPTIONS list. Do not fabricate courses.
IMPORTANT: Keep all content professional, constructive, and actionable. This is formative, not punitive.
Respond with valid JSON only."""

ROADMAP_PROMPT = """You are designing a personalized 30/60/90-day professional development roadmap for an educator.
This is based on anonymized feedback data. Your tone must be constructive, encouraging, and specific.

FACULTY CONTEXT (anonymized):
- Department: {dept}  
- Score Band: {score_band} (composite: {composite_score}/5)
- Primary Development Areas: {weak_dimensions}
- Recommended Courses: {recommended_courses}

Generate a JSON roadmap with this exact structure:
{{
  "day30": {{
    "phase_label": "30-Day",
    "theme": "<motivating theme for this phase>",
    "focus_dimensions": ["<dim1>", "<dim2>"],
    "weeks": [
      {{
        "week_number": 1,
        "title": "<week theme>",
        "phase": "Foundation",
        "goals": ["<goal 1>", "<goal 2>"],
        "actions": ["<specific action 1>", "<specific action 2>", "<specific action 3>"],
        "success_metrics": ["<how to know this week was successful>"]
      }},
      {{
        "week_number": 2,
        "title": "<week theme>",
        "phase": "Build",
        "goals": ["<goal 1>"],
        "actions": ["<action 1>", "<action 2>"],
        "success_metrics": ["<metric 1>"]
      }},
      {{
        "week_number": 3,
        "title": "<week theme>",
        "phase": "Practice",
        "goals": ["<goal 1>"],
        "actions": ["<action 1>", "<action 2>"],
        "success_metrics": ["<metric 1>"]
      }},
      {{
        "week_number": 4,
        "title": "<week theme>",
        "phase": "Reflect",
        "goals": ["<goal 1>"],
        "actions": ["<action 1>", "<action 2>"],
        "success_metrics": ["<metric 1>"]
      }}
    ],
    "milestone": "<What concrete outcome should be achieved by day 30>"
  }},
  "day60": {{
    "phase_label": "60-Day",
    "theme": "<theme for this deeper phase>",
    "focus_dimensions": ["<dim1>"],
    "weeks": [
      {{"week_number": 5, "title": "<>", "phase": "Deepen", "goals": [], "actions": [], "success_metrics": []}},
      {{"week_number": 6, "title": "<>", "phase": "Apply", "goals": [], "actions": [], "success_metrics": []}},
      {{"week_number": 7, "title": "<>", "phase": "Measure", "goals": [], "actions": [], "success_metrics": []}},
      {{"week_number": 8, "title": "<>", "phase": "Adjust", "goals": [], "actions": [], "success_metrics": []}}
    ],
    "milestone": "<Day 60 milestone>"
  }},
  "day90": {{
    "phase_label": "90-Day",
    "theme": "<mastery and sustainability theme>",
    "focus_dimensions": ["<dim1>"],
    "weeks": [
      {{"week_number": 9, "title": "<>", "phase": "Integrate", "goals": [], "actions": [], "success_metrics": []}},
      {{"week_number": 10, "title": "<>", "phase": "Share", "goals": [], "actions": [], "success_metrics": []}},
      {{"week_number": 11, "title": "<>", "phase": "Sustain", "goals": [], "actions": [], "success_metrics": []}},
      {{"week_number": 12, "title": "<>", "phase": "Plan Next", "goals": [], "actions": [], "success_metrics": []}}
    ],
    "milestone": "<Day 90 milestone — sustained behavior change evidence>"
  }}
}}

Be concrete and practical. Actions should be specific enough to do on a Tuesday afternoon.
Respond with valid JSON only."""


# ── Mock responses for testing ────────────────────────────────────────────────
MOCK_RECOMMENDATION_RESPONSE = {
    "recommendations": [
        {
            "course_title": "Effective Teaching: Explanation and Concept Clarity",
            "target_dimension": "clarity",
            "confidence_score": 0.87,
            "justification": "Student feedback consistently highlights difficulty following complex concept explanations. This course directly addresses structured explanation techniques and analogy-based teaching that address the identified clarity deficit.",
            "learning_outcomes_summary": "Faculty will design clear, step-by-step explanations using Bloom's taxonomy to sequence content appropriately for the student level.",
            "expected_impact": "Students report higher comprehension rates and improved ability to connect concepts to problem-solving within one semester."
        },
        {
            "course_title": "Innovative Pedagogy for Engineering Education",
            "target_dimension": "methodology",
            "confidence_score": 0.79,
            "justification": "Feedback themes indicate monotonous lecture-only delivery. This course provides evidence-based active learning strategies and problem-based learning techniques relevant to engineering classrooms.",
            "learning_outcomes_summary": "Faculty will implement at least two active learning strategies per week and design flipped classroom modules for selected topics.",
            "expected_impact": "Student engagement scores expected to improve by 0.5+ points within two semesters of consistent implementation."
        }
    ],
    "root_cause_analysis": "The pattern of low scores in clarity and methodology, combined with moderate engagement scores, suggests that the faculty has strong subject knowledge but relies on a traditional transmission-based teaching style. This is a common developmental stage for subject-matter experts transitioning to teaching roles. The core issue appears to be a gap between knowing content deeply and translating that knowledge into forms accessible to students at varying readiness levels. Feedback themes around 'hard to follow' and 'too fast' suggest a pacing-clarity interaction: the faculty may be covering material at the speed appropriate for their own expertise level rather than the students' learning pace.",
    "executive_summary": "This faculty member is at the 'Developing' stage with particular strengths in subject knowledge and punctuality, but requires structured development in pedagogical techniques. Two targeted courses are recommended focusing on clarity of explanation and innovative methodology. The 90-day roadmap below provides a practical, achievable pathway to move toward the 'Strong' band within two semesters."
}

MOCK_ROADMAP_RESPONSE = {
    "day30": {
        "phase_label": "30-Day",
        "theme": "Foundation: Clarity First",
        "focus_dimensions": ["clarity", "methodology"],
        "weeks": [
            {"week_number": 1, "title": "Audit & Diagnose", "phase": "Foundation",
             "goals": ["Understand current teaching patterns", "Identify 3 specific clarity gaps"],
             "actions": ["Record one class session and watch it back noting where explanations lose clarity",
                        "Map the last 3 weeks of content to Bloom's taxonomy levels",
                        "List the 5 topics students most frequently ask about after class"],
             "success_metrics": ["Completed self-audit document with 3+ actionable findings"]},
            {"week_number": 2, "title": "Restructure Explanations", "phase": "Build",
             "goals": ["Redesign 2 lesson explanations using structured template"],
             "actions": ["Apply the 'Concrete-Representational-Abstract' (CRA) framework to one concept per day",
                        "Prepare 3 real-world analogies for the next difficult topic"],
             "success_metrics": ["2 restructured lesson plans ready", "Student comprehension check scores > 70%"]},
            {"week_number": 3, "title": "Introduce One Active Element", "phase": "Practice",
             "goals": ["Add one interactive element per class"],
             "actions": ["Implement 'Think-Pair-Share' for one question per lecture",
                        "End each class with a 2-minute muddiest-point exit card"],
             "success_metrics": ["Students completing exit cards", "Able to identify most common confusion points"]},
            {"week_number": 4, "title": "Reflect & Adjust", "phase": "Reflect",
             "goals": ["Consolidate what worked, plan next month"],
             "actions": ["Review exit card data to spot recurring themes",
                        "Share one lesson improvement with a peer or mentor"],
             "success_metrics": ["Written reflection completed", "Peer observation scheduled"]}
        ],
        "milestone": "By Day 30: At least 2 lessons redesigned with structured clarity techniques and one active learning element consistently embedded in weekly delivery."
    },
    "day60": {
        "phase_label": "60-Day",
        "theme": "Deepen: Methodology Upgrade",
        "focus_dimensions": ["methodology", "engagement"],
        "weeks": [
            {"week_number": 5, "title": "Flipped Classroom Pilot", "phase": "Deepen",
             "goals": ["Design and run one flipped classroom session"],
             "actions": ["Record a 10-minute pre-class explainer video for one topic",
                        "Design an in-class activity that uses flipped time productively"],
             "success_metrics": ["Flipped session delivered", "Student pre-watch rate > 60%"]},
            {"week_number": 6, "title": "Problem-Based Learning", "phase": "Apply",
             "goals": ["Design one PBL case study for the course"],
             "actions": ["Map a real-world engineering problem to the current topic",
                        "Run a structured 30-minute PBL session with student teams"],
             "success_metrics": ["PBL case designed and piloted", "Student team participation observed"]},
            {"week_number": 7, "title": "Measure Impact", "phase": "Measure",
             "goals": ["Gather informal mid-semester student feedback"],
             "actions": ["Run anonymous 3-question feedback check (clarity, pace, engagement)",
                        "Compare against last semester's early-term response to similar questions"],
             "success_metrics": ["Feedback data collected", "Observable improvement in at least 2 dimensions"]},
            {"week_number": 8, "title": "Iterate", "phase": "Adjust",
             "goals": ["Adjust based on feedback data"],
             "actions": ["Refine the element with lowest satisfaction scores",
                        "Document the change and rationale for end-of-semester review"],
             "success_metrics": ["Specific change implemented and documented"]}
        ],
        "milestone": "By Day 60: One flipped classroom module and one PBL activity delivered and iterated based on student feedback data."
    },
    "day90": {
        "phase_label": "90-Day",
        "theme": "Sustain: Embed and Share",
        "focus_dimensions": ["overall", "methodology"],
        "weeks": [
            {"week_number": 9, "title": "Integrate Into Course Design", "phase": "Integrate",
             "goals": ["Embed improved techniques into permanent course structure"],
             "actions": ["Update course outline to formally include active learning activities",
                        "Revise lesson plans for next semester using new approach"],
             "success_metrics": ["Updated course plan for next semester ready"]},
            {"week_number": 10, "title": "Peer Learning", "phase": "Share",
             "goals": ["Share what worked with a department colleague"],
             "actions": ["Present a 15-minute 'what I tried and what worked' session at a department meeting",
                        "Offer to co-design one session with a junior colleague"],
             "success_metrics": ["Peer session delivered", "At least one colleague interested in trying the approach"]},
            {"week_number": 11, "title": "Complete Recommended Course", "phase": "Sustain",
             "goals": ["Finish the recommended NPTEL/SWAYAM course"],
             "actions": ["Complete remaining modules and assessment",
                        "Apply at least one new technique learned from the course"],
             "success_metrics": ["Course certificate obtained", "New technique trialed in class"]},
            {"week_number": 12, "title": "Plan Next Term", "phase": "Plan Next",
             "goals": ["Set development goals for next semester before it starts"],
             "actions": ["Review end-of-term feedback when available",
                        "Write a 3-point improvement plan for next semester",
                        "Schedule peer observation for week 4 of next term"],
             "success_metrics": ["Next-term improvement plan documented and shared with HoD/mentor"]}
        ],
        "milestone": "By Day 90: Systematic teaching improvements embedded in course design, one course completed, peer learning initiated, and next-term development goals set."
    }
}


@dataclass
class LLMResponse:
    raw_response: str = ""
    parsed_json: dict = field(default_factory=dict)
    is_mock: bool = False
    error: str | None = None


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(Exception),
    reraise=False,
)
async def _call_llm(prompt: str) -> str:
    """Call LLM via LiteLLM with retry logic."""
    import litellm
    response = await litellm.acompletion(
        model=settings.llm_model,
        messages=[
            {"role": "system", "content": "You are a precise faculty development advisor. Always respond with valid JSON."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=settings.llm_max_tokens,
        temperature=settings.llm_temperature,
        response_format={"type": "json_object"},
    )
    return response.choices[0].message.content or ""


async def generate_recommendations(
    *,
    dept: str,
    subject: str,
    score_band: str,
    composite_score: float,
    response_count: int,
    weak_dimensions: list[str],
    feedback_themes: list[str],
    retrieved_courses: list[dict],
) -> LLMResponse:
    """Generate course recommendations using LLM + RAG."""
    if not settings.llm_enabled:
        return LLMResponse(parsed_json=MOCK_RECOMMENDATION_RESPONSE, is_mock=True)

    course_options = "\n".join(
        f"- {c.get('title', 'N/A')} ({c.get('provider', '')}, {c.get('duration_label', 'N/A')}): "
        f"{c.get('description', '')[:150]}..."
        for c in retrieved_courses[:6]
    )
    prompt = RECOMMENDATION_PROMPT.format(
        dept=dept,
        subject=subject or "Not specified",
        score_band=score_band,
        composite_score=composite_score,
        response_count=response_count,
        weak_dimensions="\n".join(f"- {d}" for d in weak_dimensions),
        feedback_themes="\n".join(f"- {t}" for t in feedback_themes) or "No comment themes extracted",
        course_options=course_options,
    )

    try:
        raw = await _call_llm(prompt)
        parsed = json.loads(raw)
        return LLMResponse(raw_response=raw, parsed_json=parsed, is_mock=False)
    except Exception as e:
        logger.warning("LLM call failed, returning mock response: %s", e)
        return LLMResponse(parsed_json=MOCK_RECOMMENDATION_RESPONSE, is_mock=True, error=str(e))


async def generate_roadmap(
    *,
    dept: str,
    score_band: str,
    composite_score: float,
    weak_dimensions: list[str],
    recommended_courses: list[str],
) -> LLMResponse:
    """Generate a 30/60/90-day roadmap using LLM."""
    if not settings.llm_enabled:
        return LLMResponse(parsed_json=MOCK_ROADMAP_RESPONSE, is_mock=True)

    prompt = ROADMAP_PROMPT.format(
        dept=dept,
        score_band=score_band,
        composite_score=composite_score,
        weak_dimensions="\n".join(f"- {d}" for d in weak_dimensions),
        recommended_courses="\n".join(f"- {c}" for c in recommended_courses),
    )

    try:
        raw = await _call_llm(prompt)
        parsed = json.loads(raw)
        return LLMResponse(raw_response=raw, parsed_json=parsed, is_mock=False)
    except Exception as e:
        logger.warning("LLM roadmap generation failed, returning mock: %s", e)
        return LLMResponse(parsed_json=MOCK_ROADMAP_RESPONSE, is_mock=True, error=str(e))
