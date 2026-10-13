"""User accounts and browser sessions.

A signed-in browser holds an opaque token in an httpOnly cookie; the database
stores only its digest. Item ownership already keys on `items.owner_id`, which a
user satisfies by handing out its uuid, so no item query changes here.

Every failure mode returns the same `AuthenticationError`: whether the address
is unknown, the password is wrong or the account exists at all is never told
apart to the caller.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any, cast
from uuid import uuid4

from sqlalchemy import CursorResult, func, select, update
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import AuthenticationError, BadRequestError, ConflictError
from app.core.security import hash_password, hash_session_token, new_session_token, verify_password
from app.db.models import Item, Session as SessionRow, User


logger = logging.getLogger(__name__)

MAX_EMAIL_LENGTH = 254
# Cheap structural check only. It rejects the obvious mistakes without trying to
# out-argue the address grammar; the confirmation field is the real safeguard.
_EMAIL_LOCAL_LIMIT = 64


def normalize_email(email: str) -> str:
    return email.strip().lower()


def _is_plausible_email(email: str) -> bool:
    if not email or len(email) > MAX_EMAIL_LENGTH or ".." in email:
        return False
    local, _, domain = email.partition("@")
    if not local or len(local) > _EMAIL_LOCAL_LIMIT or "." not in domain:
        return False
    if domain.startswith(".") or domain.endswith(".") or " " in email:
        return False
    return all(character not in local for character in " \t\r\n\"'")


def count_users(session: Session) -> int:
    return session.scalar(select(func.count()).select_from(User)) or 0


def find_user(session: Session, email: str) -> User | None:
    return session.scalar(select(User).where(User.email == normalize_email(email)))


def create_user(
    session: Session, settings: Settings, *, email: str, password: str
) -> tuple[User, bool]:
    """Create an account. Returns the user and whether this was the first one.

    The first account on a fresh install is always allowed, otherwise a new
    deployment would have no way in. Every later account needs
    `auth_allow_registration` or the CLI.
    """
    normalized = normalize_email(email)
    if not _is_plausible_email(normalized):
        raise BadRequestError("Enter a valid email address.")
    if len(password) < settings.auth_password_min_length:
        raise BadRequestError(f"Use at least {settings.auth_password_min_length} characters.")

    is_first_user = count_users(session) == 0
    if not is_first_user and not settings.auth_allow_registration:
        raise ConflictError("Registration is closed. Ask the owner for an account.")
    if find_user(session, normalized) is not None:
        # Deliberately the same shape as the closed-registration answer is not
        # used: a duplicate address is a user error, not an auth failure.
        raise ConflictError("An account already exists for that address.")

    user = User(
        id=str(uuid4()),
        email=normalized,
        password_hash=hash_password(password, iterations=settings.password_hash_iterations),
    )
    session.add(user)
    session.flush()

    if is_first_user:
        _claim_legacy_items(session, user, legacy_owner_id=settings.api_key_owner_id)
    session.commit()
    logger.info("user_created", extra={"stage": "auth", "user_id": user.id})
    return user, is_first_user


def _claim_legacy_items(session: Session, user: User, *, legacy_owner_id: str) -> None:
    """Hand pre-auth items to the first real account.

    Rows from before user accounts existed carry the configured API-key owner
    id. They belong to whoever set the library up, which is the first account
    that registers, so they are re-owned here instead of being orphaned.
    """
    result = session.execute(
        update(Item).where(Item.owner_id == legacy_owner_id).values(owner_id=user.id)
    )
    row_count = cast(CursorResult[Any], result).rowcount or 0
    if row_count:
        logger.info("legacy_items_claimed", extra={"stage": "auth", "item_count": int(row_count)})


def authenticate(session: Session, settings: Settings, *, email: str, password: str) -> User:
    """Return the user for valid credentials, else raise the same 401 for all failures."""
    user = find_user(session, email)
    # Hash a dummy value when the address is unknown so the response time does
    # not reveal which addresses exist.
    encoded = user.password_hash if user is not None else "pbkdf2_sha256$1$AAAA$AAAA"
    valid = verify_password(password, encoded)
    if user is None or not valid:
        raise AuthenticationError()
    return user


def create_session(session: Session, settings: Settings, user: User) -> tuple[str, SessionRow]:
    """Issue a session token; only `token` ever leaves the server."""
    token = new_session_token()
    row = SessionRow(
        id=str(uuid4()),
        user_id=user.id,
        token_hash=hash_session_token(token),
        expires_at=datetime.now(UTC) + timedelta(days=settings.auth_session_ttl_days),
    )
    session.add(row)
    session.commit()
    return token, row


def user_for_token(session: Session, token: str | None) -> User | None:
    """Resolve a cookie token to its user, deleting the row if it has expired."""
    if not token:
        return None
    row = session.scalar(
        select(SessionRow).where(SessionRow.token_hash == hash_session_token(token))
    )
    if row is None:
        return None
    expires_at = row.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if expires_at <= datetime.now(UTC):
        session.delete(row)
        session.commit()
        return None
    user = session.get(User, row.user_id)
    if user is None:
        session.delete(row)
        session.commit()
        return None
    return user


def revoke_session(session: Session, token: str | None) -> None:
    if not token:
        return
    row = session.scalar(
        select(SessionRow).where(SessionRow.token_hash == hash_session_token(token))
    )
    if row is not None:
        session.delete(row)
        session.commit()


def purge_expired_sessions(session: Session) -> int:
    """Drop sessions past their expiry so the table cannot grow without bound.

    Expiry is compared in Python, not SQL: SQLite returns naive datetimes and
    binding an aware one for a text comparison is not reliable.
    """
    now = datetime.now(UTC)
    removed = 0
    for row in session.scalars(select(SessionRow)):
        expires_at = row.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        if expires_at <= now:
            session.delete(row)
            removed += 1
    if removed:
        session.commit()
    return removed
