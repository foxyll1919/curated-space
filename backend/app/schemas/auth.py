from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field

from app.db.models import User


def _as_utc(value: datetime) -> datetime:
    """SQLite hands back naive datetimes; the API contract is UTC-aware."""
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


def _utc(value: datetime | None) -> datetime:
    """Same, for a column that is never null."""
    assert value is not None, "expected a non-null timestamp"
    return _as_utc(value)


class UserResponse(BaseModel):
    """The signed-in account. Never carries the password hash."""

    id: str
    email: str
    created_at: datetime

    @classmethod
    def from_model(cls, user: User) -> "UserResponse":
        return cls(id=user.id, email=user.email, created_at=_utc(user.created_at))


class RegisterRequest(BaseModel):
    model_config = {"extra": "forbid"}

    email: str = Field(max_length=254)
    password: str = Field(min_length=1, max_length=256)


class LoginRequest(BaseModel):
    model_config = {"extra": "forbid"}

    email: str = Field(max_length=254)
    password: str = Field(min_length=1, max_length=256)


class SessionResponse(BaseModel):
    user: UserResponse
    expires_at: datetime

    @classmethod
    def from_model(cls, user: User, expires_at: datetime) -> "SessionResponse":
        return cls(user=UserResponse.from_model(user), expires_at=_utc(expires_at))


class AuthStatusResponse(BaseModel):
    """Answers "can this page offer a create-account form?" without authenticating."""

    users: int
    registration_open: bool
