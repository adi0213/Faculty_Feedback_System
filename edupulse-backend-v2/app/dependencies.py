"""
FastAPI dependencies: database session, current user extraction, and RBAC.
"""
from typing import Annotated

from fastapi import Depends, Header, Request
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError, AuthorizationError
from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User

# ── Database dependency ───────────────────────────────────────────────────────
DbDep = AsyncSession


# ── Auth dependency ───────────────────────────────────────────────────────────
async def get_current_user(
    db: AsyncSession = Depends(get_db),
    authorization: str | None = Header(default=None),
) -> User:
    """
    Extract and validate the JWT bearer token.
    Returns the authenticated User ORM object.
    Raises AuthenticationError on any failure.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise AuthenticationError("Missing or invalid Authorization header")

    token = authorization.split(" ", 1)[1]
    try:
        payload = decode_token(token)
    except JWTError:
        raise AuthenticationError("Invalid or expired token")

    if payload.get("type") != "access":
        raise AuthenticationError("Invalid token type")

    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError("Malformed token payload")

    result = await db.execute(select(User).where(User.id == user_id, User.is_active.is_(True)))
    user = result.scalar_one_or_none()
    if not user:
        raise AuthenticationError("User account not found or inactive")

    return user


# Simple type alias (no Annotated+Depends) for use in function signatures
CurrentUser = User


def require_role(*roles: str):
    """
    FastAPI dependency factory: raises 403 if the current user's role
    is not in the allowed roles list.
    """
    async def _dep(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise AuthorizationError(
                f"This action requires one of: {', '.join(roles)}. "
                f"Your role is: {user.role}"
            )
        return user

    return _dep


def require_self_or_role(user_id_param: str = "user_id", *admin_roles: str):
    """
    Allows access if the current user IS the target user, OR has an admin role.
    """
    async def _dep(request: Request, user: User = Depends(get_current_user)) -> User:
        target_id = request.path_params.get(user_id_param)
        if user.id == target_id or user.role in admin_roles:
            return user
        raise AuthorizationError("You can only access your own resources")
    return _dep
