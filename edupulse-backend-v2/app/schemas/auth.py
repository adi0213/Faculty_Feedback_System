"""Pydantic schemas for authentication."""
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, EmailStr, Field, field_validator


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.lower().strip()


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["Bearer"] = "Bearer"
    expires_in: int  # seconds


class RefreshRequest(BaseModel):
    refresh_token: str


class UserPublicResponse(BaseModel):
    id: str
    role: str
    name: str
    email: str
    dept: str | None = None
    college: str | None = None
    university: str | None = None
    enrolled_faculty_ids: list[str] = Field(default_factory=list)
    is_active: bool

    model_config = {"from_attributes": True}


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=10, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v
