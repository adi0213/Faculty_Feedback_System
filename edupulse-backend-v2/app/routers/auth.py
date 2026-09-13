"""Auth router — login, token refresh, logout, current user."""
import logging
from fastapi import APIRouter, Depends, Request

from app.core.audit import audit_context_from_request, log_event
from app.core.exceptions import AuthenticationError
from app.core.rate_limit import auth_rate_limit
from app.db.session import get_db
from app.dependencies import get_current_user
from app.schemas.auth import LoginRequest, RefreshRequest, TokenResponse, UserPublicResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = logging.getLogger(__name__)


@router.post("/login", response_model=TokenResponse, summary="Authenticate and receive JWT tokens")
async def login(
    req: LoginRequest,
    request: Request,
    db=Depends(get_db),
    _rl=Depends(auth_rate_limit),
):
    """
    Authenticate with email + password.
    Returns an access token (30 min) and refresh token (7 days).
    Rate limited to 5 attempts per minute per IP.
    """
    ctx = audit_context_from_request(request)
    try:
        user = await auth_service.authenticate_user(db, req.email, req.password)
        tokens = auth_service.issue_tokens(user)
        await log_event(db, event_type="auth.login", event_outcome="success",
                        user_id=user.id, user_role=user.role,
                        resource_type="user", resource_id=user.id, **ctx)
        return tokens
    except AuthenticationError:
        await log_event(db, event_type="auth.login", event_outcome="failure",
                        details={"email": req.email[:30]}, **ctx)
        raise


@router.post("/refresh", response_model=TokenResponse, summary="Refresh access token")
async def refresh(req: RefreshRequest, db=Depends(get_db)):
    """Exchange a valid refresh token for a new access + refresh token pair."""
    return await auth_service.refresh_access_token(db, req.refresh_token)


@router.post("/logout", summary="Invalidate current session")
async def logout(user=Depends(get_current_user)):
    """
    Client-side logout. In a stateless JWT system this is a no-op on the server.
    Clients must discard both tokens. For full server-side invalidation,
    add the JTI to a Redis blocklist here.
    """
    return {"message": "Logged out successfully. Please discard your tokens."}


@router.get("/me", response_model=UserPublicResponse, summary="Get current user profile")
async def get_me(user=Depends(get_current_user)):
    """Return the authenticated user's profile."""
    return auth_service.user_to_public(user)
