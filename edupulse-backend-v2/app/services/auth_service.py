"""
Authentication service: login, token issuance, user retrieval.
"""
import json
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import TokenResponse, UserPublicResponse

logger = logging.getLogger(__name__)


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User:
    """
    Verify email + password. Returns the User ORM object on success.
    Uses constant-time comparison (via passlib) to prevent timing attacks.
    """
    result = await db.execute(
        select(User).where(User.email == email.lower().strip())
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.hashed_password):
        # Deliberate generic message — don't reveal whether email exists
        raise AuthenticationError("Invalid email or password")

    if not user.is_active:
        raise AuthenticationError("Account is deactivated. Contact your administrator.")

    # Update last login
    user.last_login_at = datetime.now(timezone.utc)
    db.add(user)

    return user


def issue_tokens(user: User) -> TokenResponse:
    """Issue access + refresh token pair for an authenticated user."""
    access = create_access_token(subject=user.id, role=user.role)
    refresh = create_refresh_token(subject=user.id)
    from app.config import get_settings
    settings = get_settings()
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        expires_in=settings.jwt_access_token_expire_minutes * 60,
    )


async def get_user_by_id(db: AsyncSession, user_id: str) -> User | None:
    """Fetch a user by primary key. Returns None if not found."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


def user_to_public(user: User) -> UserPublicResponse:
    """Serialize a User ORM object to the public-facing schema."""
    enrolled = []
    if user.enrolled_faculty_ids:
        try:
            enrolled = json.loads(user.enrolled_faculty_ids)
        except (ValueError, TypeError):
            pass

    return UserPublicResponse(
        id=user.id,
        role=user.role,
        name=user.name,
        email=user.email,
        dept=user.dept,
        college=user.college,
        university=user.university,
        enrolled_faculty_ids=enrolled,
        is_active=user.is_active,
    )


async def refresh_access_token(db: AsyncSession, refresh_token: str) -> TokenResponse:
    """
    Validate a refresh token and issue a new access token pair.
    """
    from jose import JWTError
    try:
        payload = decode_token(refresh_token)
    except JWTError:
        raise AuthenticationError("Invalid or expired refresh token")

    if payload.get("type") != "refresh":
        raise AuthenticationError("Invalid token type")

    user = await get_user_by_id(db, payload["sub"])
    if not user or not user.is_active:
        raise AuthenticationError("User not found or inactive")

    return issue_tokens(user)
