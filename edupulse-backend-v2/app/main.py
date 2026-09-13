"""
FastAPI application factory.
Creates the app, registers all middleware, routers, and startup events.
"""
import logging
from contextlib import asynccontextmanager

from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.middleware import add_middlewares

logger = logging.getLogger(__name__)
settings = get_settings()


def _configure_logging() -> None:
    import sys
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    fmt = "%(asctime)s %(levelname)s %(name)s: %(message)s"
    logging.basicConfig(level=level, format=fmt, stream=sys.stdout)
    # Quieten noisy libraries
    for noisy in ("uvicorn.access", "sqlalchemy.engine", "litellm"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    _configure_logging()
    logger.info("EduPulse API starting (env=%s, llm_enabled=%s)", settings.app_env, settings.llm_enabled)

    # ── Auto-initialize DB schemas and tables if missing ─────────────────────
    try:
        import app.models  # Register all ORM models with Base
        from app.db.session import engine, Base
        from sqlalchemy import text

        async with engine.begin() as conn:
            if engine.dialect.name != "sqlite":
                await conn.execute(text("CREATE SCHEMA IF NOT EXISTS registry"))
                await conn.execute(text("CREATE SCHEMA IF NOT EXISTS feedback"))
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database schemas and tables initialized successfully")
    except Exception as e:
        logger.warning("Database schema auto-creation failed: %s", e)

    # ── Auto-seed demo data on first boot (if DB is empty) ───────────────────
    try:
        from app.db.session import AsyncSessionLocal
        from sqlalchemy import text as sql_text

        async with AsyncSessionLocal() as session:
            result = await session.execute(sql_text("SELECT COUNT(*) FROM registry.users"))
            user_count = result.scalar()

        if user_count == 0:
            logger.info("Database is empty — running auto-seed...")
            import sys, os
            sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
            from seed_v2 import seed_only
            await seed_only()
            logger.info("Auto-seed completed — demo accounts ready")
        else:
            logger.info("Database already has %d users — skipping seed", user_count)
    except Exception as e:
        logger.warning("Auto-seed failed (non-fatal): %s", e)

    # ── Pre-warm RAG engine at startup ───────────────────────────────────────
    try:
        from app.ai.rag_engine import get_rag_engine
        get_rag_engine()
        logger.info("RAG engine pre-loaded")
    except Exception as e:
        logger.warning("RAG engine pre-load failed: %s", e)

    yield

    logger.info("EduPulse API shutting down")


def create_app() -> FastAPI:
    """Application factory — creates and configures the FastAPI instance."""
    app = FastAPI(
        title="EduPulse AI — Faculty Feedback & Development Platform",
        description=(
            "Production-grade AI-powered faculty evaluation system for Kerala Higher Education. "
            "Implements anonymized feedback collection, statistical scoring (Winsorizing, "
            "Empirical Bayes, cohort normalization), NLP analysis, RAG-based course "
            "recommendations, and 30/60/90-day personalized improvement roadmaps."
        ),
        version="2.0.0",
        docs_url="/docs" if settings.app_env != "production" else None,
        redoc_url="/redoc" if settings.app_env != "production" else None,
        default_response_class=ORJSONResponse,
        lifespan=lifespan,
    )

    # ── CORS ────────────────────────────────────────────────────────────────
    cors_origins = settings.allowed_origins
    allow_all = "*" in cors_origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if allow_all else cors_origins,
        allow_credentials=not allow_all,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID", "X-API-Key"],
        expose_headers=["X-Request-ID"],
        max_age=600,
    )

    # ── Custom middleware (order: outermost first) ──────────────────────────
    add_middlewares(app)

    # ── Exception handlers ──────────────────────────────────────────────────
    register_exception_handlers(app)

    # ── Routers ─────────────────────────────────────────────────────────────
    from app.routers import admin, analytics, auth, faculty, feedback, recommendations, faculty_development

    api_prefix = "/api/v2"
    app.include_router(auth.router, prefix=api_prefix)
    app.include_router(feedback.router, prefix=api_prefix)
    app.include_router(faculty.router, prefix=api_prefix)
    app.include_router(faculty_development.router, prefix=api_prefix)
    app.include_router(analytics.router, prefix=api_prefix)
    app.include_router(recommendations.router, prefix=api_prefix)
    app.include_router(admin.router, prefix=api_prefix)

    # ── Static files (uploaded certificates) ────────────────────────────────
    _candidates = [Path("uploads/certificates"), Path("/tmp/edupulse/uploads/certificates")]
    uploads_dir = None
    for _d in _candidates:
        try:
            _d.mkdir(parents=True, exist_ok=True)
            uploads_dir = _d
            break
        except (PermissionError, OSError):
            continue
    if uploads_dir:
        app.mount("/uploads/certificates", StaticFiles(directory=str(uploads_dir)), name="certificates")
    else:
        logger.warning("Could not create uploads directory — certificate serving disabled")


    # ── Metrics ─────────────────────────────────────────────────────────────
    try:
        from prometheus_fastapi_instrumentator import Instrumentator
        Instrumentator().instrument(app).expose(app, endpoint="/metrics")
    except ImportError:
        logger.info("prometheus_fastapi_instrumentator not installed, metrics disabled")

    # ── Root health check ───────────────────────────────────────────────────
    @app.get("/", tags=["Health"], summary="API root / health check")
    async def root():
        return {
            "service": "EduPulse AI Faculty Feedback Platform",
            "version": "2.0.0",
            "status": "healthy",
            "docs": "/docs",
        }

    @app.get("/health", tags=["Health"], summary="Liveness probe")
    async def health():
        return {"status": "ok"}

    return app




def get_application() -> FastAPI:
    """Return the configured FastAPI app. Used by uvicorn and tests."""
    return create_app()


# Module-level app instance for uvicorn: `uvicorn app.main:app`
app = create_app()
