"""
Database seed script — populates the database with realistic test data.
Creates users for all roles, faculty profiles, and sample feedback records.

Run:
    python seed_v2.py
"""
import asyncio
import json
import uuid
from datetime import datetime, timezone, timedelta
import random

# ── Bootstrap path ────────────────────────────────────────────────────────────
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import text
from app.config import get_settings
from app.core.security import hash_password, generate_pseudo_token, hash_pseudo_token
from app.db.session import Base, engine, AsyncSessionLocal
from app.models.user import User
from app.models.faculty import FacultyProfile
from app.models.feedback import FeedbackRecord, SubmissionRecord
from app.models.token import PseudoToken
from app.models.course_catalog import CourseCatalogEntry
from app.models.roadmap import CourseRecommendation, FacultyRoadmap
from app.models.audit_log import AuditLog

settings = get_settings()


DEPARTMENTS = ["Computer Science", "Electronics", "Mechanical", "Civil", "Mathematics"]
COLLEGES = ["GEC Thrissur", "CET Thiruvananthapuram", "Model Engineering College"]
UNIVERSITY = "KTU"
TERMS = ["2024-S1", "2024-S2", "2025-S1", "2025-S2"]
CURRENT_TERM = "2025-S2"

DIMENSIONS = ["clarity", "methodology", "punctuality", "fairness", "approachability", "pacing"]


def rnd_score(bias: float = 0.0) -> int:
    """Generate a random 1-4 Likert score with optional bias."""
    base = random.choices([1, 2, 3, 4], weights=[1, 2, 4, 3], k=1)[0]
    return max(1, min(4, base + int(bias)))


def make_id() -> str:
    return str(uuid.uuid4())


async def create_schemas(session):
    """Create PostgreSQL schemas or SQLite attached databases."""
    if engine.dialect.name == "sqlite":
        try:
            await session.execute(text("ATTACH DATABASE 'edupulse_v2_registry.db' AS registry"))
            await session.execute(text("ATTACH DATABASE 'edupulse_v2_feedback.db' AS feedback"))
        except Exception:
            pass
    else:
        await session.execute(text("CREATE SCHEMA IF NOT EXISTS registry"))
        await session.execute(text("CREATE SCHEMA IF NOT EXISTS feedback"))
    await session.commit()


async def drop_and_recreate(session):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


async def seed_users(session) -> dict:
    """Create one user per role per college."""
    users = {}

    # University admin
    u = User(id=make_id(), role="university", name="Dr. P. K. Suresh",
             email="university@keralaedu.in", hashed_password=hash_password("Kerala@Edu2025"),
             university=UNIVERSITY, is_active=True)
    session.add(u)
    users["university"] = u

    # Principals (one per college)
    p = User(id=make_id(), role="principal", name="Principal GEC Thrissur",
             email="principal@college.edu", hashed_password=hash_password("Principal@123"),
             college=COLLEGES[0], university=UNIVERSITY, is_active=True)
    session.add(p)
    users["principal"] = p

    # HoD
    h = User(id=make_id(), role="hod", name="Dr. HoD Computer Science",
             email="hod@college.edu", hashed_password=hash_password("HoD@Dept123"),
             dept="Computer Science", college=COLLEGES[0], university=UNIVERSITY, is_active=True)
    session.add(h)
    users["hod"] = h

    await session.flush()
    return users


async def seed_faculty(session) -> list[tuple[User, FacultyProfile]]:
    """Create faculty users and profiles."""
    faculty_pairs = []
    faculty_data = [
        ("Dr. Suresh Kumar", "Computer Science", "Data Structures & Algorithms", COLLEGES[0], "faculty@college.edu", 3.6),
        ("Dr. Priya Nair", "Computer Science", "Machine Learning", COLLEGES[0], "priya.nair@college.edu", 4.2),
        ("Dr. Anil Menon", "Electronics", "Digital Signal Processing", COLLEGES[0], "anil.menon@college.edu", 2.8),
        ("Dr. Sreeja Pillai", "Mechanical", "Thermodynamics", COLLEGES[1], "sreeja.pillai@college.edu", 3.9),
        ("Dr. Rajesh Varma", "Civil", "Structural Analysis", COLLEGES[1], "rajesh.varma@college.edu", 4.5),
        ("Dr. Meena Krishnan", "Mathematics", "Linear Algebra", COLLEGES[0], "meena.k@college.edu", 3.1),
    ]

    for i, (name, dept, subject, college, email, target_composite) in enumerate(faculty_data):
        fid = make_id()
        user = User(
            id=fid, role="faculty", name=name, email=email,
            hashed_password=hash_password("Faculty@123"),
            dept=dept, college=college, university=UNIVERSITY, is_active=True,
        )
        session.add(user)

        # Generate realistic dimension scores
        bias = (target_composite - 3.0) * 0.5
        dim_scores = {d: round(rnd_score(bias) * 1.25, 2) for d in DIMENSIONS}
        composite = round(sum(dim_scores.values()) / len(dim_scores), 2)
        band = "strong" if composite >= 4.0 else ("developing" if composite >= 3.0 else "needs_support")

        # Build trend history
        trend = []
        for j, term in enumerate(TERMS):
            trend_score = round(composite + random.uniform(-0.3, 0.3), 2)
            trend.append({"term": term, "composite_score": trend_score,
                         "response_count": random.randint(8, 45), "score_band": band})

        profile = FacultyProfile(
            id=make_id(), user_id=fid,
            faculty_code=f"FAC-{str(i+1).zfill(4)}",
            name=name, dept=dept, subject=subject, college=college, university=UNIVERSITY,
            response_count=random.randint(15, 45),
            dimension_scores_json=json.dumps(dim_scores),
            score_trend_json=json.dumps(trend),
            composite_score=composite,
            score_band=band,
        )
        session.add(profile)
        faculty_pairs.append((user, profile))

    await session.flush()
    return faculty_pairs


async def seed_feedback(session, faculty_pairs: list[tuple[User, FacultyProfile]]):
    """Generate realistic feedback records for each faculty."""
    comments_positive = [
        "Excellent teaching style, concepts are very clear.",
        "Very approachable and explains complex topics simply.",
        "Well organized, covers syllabus on time always.",
        "Best professor in the department, very helpful.",
    ]
    comments_negative = [
        "Lectures are too fast, hard to follow.",
        "Needs better examples when explaining algorithms.",
        "Syllabus coverage feels rushed near the end.",
        "Grading criteria not always transparent.",
    ]

    student_ids = [make_id() for _ in range(100)]

    for user, profile in faculty_pairs:
        n = profile.response_count
        for j in range(n):
            student_id = student_ids[j % len(student_ids)]
            token = generate_pseudo_token(student_id, str(profile.id), CURRENT_TERM)
            token_hash = hash_pseudo_token(token)

            # Vary scores around the faculty's composite
            bias = (profile.composite_score or 3.0) - 3.0
            scores = {d: rnd_score(bias * 0.5) for d in DIMENSIONS}

            comment = None
            if random.random() > 0.4:
                pool = comments_positive if bias >= 0 else comments_negative
                comment = random.choice(pool)

            fb = FeedbackRecord(
                id=make_id(),
                student_token=token[:32],
                faculty_profile_id=str(profile.id),
                term=CURRENT_TERM,
                scores_json=json.dumps(scores),
                comment_raw=comment,
                sentiment_score=round(random.uniform(-0.5 if bias < 0 else 0, 1.0), 3),
                sentiment_label="positive" if bias >= 0 else "negative",
                nlp_processed=True,
                nlp_processed_at=datetime.now(timezone.utc),
                submitted_at=datetime.now(timezone.utc) - timedelta(days=random.randint(1, 60)),
            )
            session.add(fb)

            sub = SubmissionRecord(
                student_token=token_hash,
                faculty_profile_id=str(profile.id),
                term=CURRENT_TERM,
            )
            session.add(sub)

    await session.flush()


async def seed_students(session, faculty_pairs: list[tuple[User, FacultyProfile]]):
    """Create demo student users enrolled with sample faculties."""
    enrolled = [str(p.id) for _, p in faculty_pairs[:3]]
    student = User(
        id=make_id(), role="student", name="Arjun S",
        email="student@college.edu",
        hashed_password=hash_password("Student@123"),
        dept="Computer Science", college=COLLEGES[0], university=UNIVERSITY,
        semester=5, is_active=True,
        enrolled_faculty_ids=json.dumps(enrolled),
    )
    session.add(student)
    await session.flush()


async def seed_courses(session):
    """Load course catalog from JSON into the database."""
    import pathlib
    catalog_path = pathlib.Path(__file__).parent / "data" / "course_catalog.json"
    if not catalog_path.exists():
        print("Course catalog JSON not found, skipping.")
        return

    with open(catalog_path, encoding="utf-8") as f:
        courses = json.load(f)

    for c in courses:
        entry = CourseCatalogEntry(
            id=make_id(),
            title=c["title"],
            provider=c["provider"],
            institution=c.get("institution"),
            url=c.get("url"),
            description=c["description"],
            duration_weeks=c.get("duration_weeks"),
            duration_label=c.get("duration_label"),
            primary_dimension=c.get("primary_dimension"),
            secondary_dimensions_json=json.dumps(c.get("secondary_dimensions", [])),
            level=c.get("level"),
            category=c.get("category"),
            learning_outcomes_json=json.dumps(c.get("learning_outcomes", [])),
            is_active=True,
            last_verified=datetime.now(timezone.utc),
        )
        session.add(entry)

    await session.flush()
    print(f"  - Seeded {len(courses)} courses")


async def main():
    print("\n--- EduPulse v2 Database Seed Script ---")
    print("=" * 45)

    print("  Creating schemas...")
    async with AsyncSessionLocal() as session:
        await create_schemas(session)

    print("  Dropping and recreating tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    print("  Seeding data...")
    async with AsyncSessionLocal() as session:
        await seed_users(session)
        faculty_pairs = await seed_faculty(session)
        await seed_students(session, faculty_pairs)
        await seed_feedback(session, faculty_pairs)
        await seed_courses(session)
        await session.commit()

    print("\n[SUCCESS] Seed complete! Demo credentials:")
    print("  Student:    student@college.edu / Student@123")
    print("  Faculty:    faculty@college.edu / Faculty@123")
    print("  HoD:        hod@college.edu / HoD@Dept123")
    print("  Principal:  principal@college.edu / Principal@123")
    print("  University: university@keralaedu.in / Kerala@Edu2025")
    print()


if __name__ == "__main__":
    asyncio.run(main())
