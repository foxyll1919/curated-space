"""Account routes: create an account, sign in, sign out, current account.

The session token is delivered only in an httpOnly cookie, never in a JSON
body, so page scripts cannot read it and no frontend bundle can leak it.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import delete

from app.api.deps import SessionDep, UserDep, get_settings_dep
from app.core.config import Settings
from app.db.models import Session as SessionRow
from app.schemas.auth import (
    AuthStatusResponse,
    LoginRequest,
    RegisterRequest,
    SessionResponse,
    UserResponse,
)
from app.services.auth import (
    authenticate,
    count_users,
    create_session,
    create_user,
    revoke_session,
)
from app.services.rate_limit import enforce_rate_limit


router = APIRouter(prefix="/auth", tags=["auth"])

# A cookie is only ever set for the whole app, so the path is fixed and shared
# with `_clear_session_cookie`.
COOKIE_PATH = "/"

SettingsDep = Annotated[Settings, Depends(get_settings_dep)]


def set_session_cookie(response: Response, settings: Settings, token: str) -> None:
    response.set_cookie(
        key=settings.auth_cookie_name,
        value=token,
        max_age=settings.auth_session_ttl_days * 24 * 60 * 60,
        path=COOKIE_PATH,
        httponly=True,
        # `lax` keeps the cookie out of cross-site form posts while still
        # surviving a normal navigation back into the app.
        samesite="lax",
        secure=settings.auth_cookie_secure,
    )


def clear_session_cookie(response: Response, settings: Settings) -> None:
    response.delete_cookie(key=settings.auth_cookie_name, path=COOKIE_PATH)


@router.get("/status", response_model=AuthStatusResponse)
def auth_status(session: SessionDep, settings: SettingsDep) -> AuthStatusResponse:
    """Whether the sign-in page should offer registration, without authenticating.

    The first account is always allowed so a fresh install has a way in; after
    that the answer depends on `AUTH_ALLOW_REGISTRATION`.
    """
    users = count_users(session)
    return AuthStatusResponse(
        users=users,
        registration_open=users == 0 or settings.auth_allow_registration,
    )


@router.post("/register", response_model=SessionResponse, status_code=201)
def register(
    request: Request,
    body: RegisterRequest,
    response: Response,
    session: SessionDep,
    settings: SettingsDep,
) -> SessionResponse:
    enforce_rate_limit(request, "register")
    user, _is_first_user = create_user(session, settings, email=body.email, password=body.password)
    token, row = create_session(session, settings, user)
    set_session_cookie(response, settings, token)
    return SessionResponse.from_model(user, row.expires_at)


@router.post("/login", response_model=SessionResponse)
def login(
    request: Request,
    body: LoginRequest,
    response: Response,
    session: SessionDep,
    settings: SettingsDep,
) -> SessionResponse:
    enforce_rate_limit(request, "login")
    user = authenticate(session, settings, email=body.email, password=body.password)
    token, row = create_session(session, settings, user)
    set_session_cookie(response, settings, token)
    return SessionResponse.from_model(user, row.expires_at)


@router.get("/me", response_model=UserResponse)
def me(user: UserDep) -> UserResponse:
    """The signed-in account, or 401. The client calls this to decide where to route."""
    return UserResponse.from_model(user)


@router.post("/logout", status_code=204)
def logout(request: Request, session: SessionDep, settings: SettingsDep) -> Response:
    """Sign out. Idempotent: an absent or unknown cookie still returns 204."""
    revoke_session(session, request.cookies.get(settings.auth_cookie_name))
    response = Response(status_code=204)
    clear_session_cookie(response, settings)
    return response


@router.post("/logout-all", status_code=204)
def logout_all(session: SessionDep, settings: SettingsDep, user: UserDep) -> Response:
    """Revoke every session for this account, including the current one."""
    session.execute(delete(SessionRow).where(SessionRow.user_id == user.id))
    session.commit()
    response = Response(status_code=204)
    clear_session_cookie(response, settings)
    return response
