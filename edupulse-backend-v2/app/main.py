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

    # Pre-warm RAG engine at startup
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
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
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
    uploads_dir = Path("uploads/certificates")
    uploads_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/uploads/certificates", StaticFiles(directory=str(uploads_dir)), name="certificates")

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
