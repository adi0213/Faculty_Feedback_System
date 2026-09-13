"""
JWT authentication and password hashing.
Uses HS256 for development (configurable to RS256 for production).
"""
import hashlib
import hmac
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
import bcrypt

from app.config import get_settings

settings = get_settings()

# ── Password Hashing ──────────────────────────────────────────────────────────
def hash_password(plain: str) -> str:
    """Hash a plaintext password with bcrypt (truncated to 72 bytes)."""
    pwd_bytes = plain.encode("utf-8")[:72]
    return bcrypt.hashpw(pwd_bytes, bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    pwd_bytes = plain.encode("utf-8")[:72]
    hashed_bytes = hashed.encode("utf-8")
    try:
        return bcrypt.checkpw(pwd_bytes, hashed_bytes)
    except Exception:
        return False


# ── JWT Tokens ────────────────────────────────────────────────────────────────
def _make_token(data: dict[str, Any], expires_delta: timedelta) -> str:
    payload = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    payload.update({"exp": expire, "iat": datetime.now(timezone.utc), "jti": str(uuid.uuid4())})
    return jwt.encode(payload, settings.app_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(subject: str, role: str, extra: dict | None = None) -> str:
    """Create a short-lived access JWT."""
    data = {"sub": subject, "role": role, "type": "access"}
    if extra:
        data.update(extra)
    return _make_token(data, timedelta(minutes=settings.jwt_access_token_expire_minutes))


def create_refresh_token(subject: str) -> str:
    """Create a long-lived refresh JWT."""
    data = {"sub": subject, "type": "refresh"}
    return _make_token(data, timedelta(days=settings.jwt_refresh_token_expire_days))


def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT. Raises JWTError on failure.
    Returns the payload dict.
    """
    return jwt.decode(token, settings.app_secret_key, algorithms=[settings.jwt_algorithm])


# ── HMAC Pseudonymous Token ───────────────────────────────────────────────────
def generate_pseudo_token(user_id: str, faculty_profile_id: str, term: str) -> str:
    """
    Generate a deterministic, non-reversible pseudonymous token for one
    (student, faculty, term) combination. Uses HMAC-SHA256 with the HMAC secret.
    The same inputs always produce the same token — enabling deduplication
    without storing the student ID in the feedback schema.
    """
    message = f"{user_id}:{faculty_profile_id}:{term}".encode("utf-8")
    h = hmac.new(settings.hmac_secret.encode("utf-8"), message, hashlib.sha256)
    return h.hexdigest()


def hash_pseudo_token(token: str) -> str:
    """SHA-256 hash of a pseudo token, for storage in the DB."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
