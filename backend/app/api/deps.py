from __future__ import annotations

import hmac
from typing import Annotated

from fastapi import Depends, Header, Request
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import AuthenticationError
from app.db.models import User
from app.db.session import get_session
from app.services.auth import user_for_token
from app.services.classification.base import Classifier
from app.services.extraction.base import MetadataExtractor
from app.services.jobs import JobRunner
from app.services.pipeline import PipelineContext
from app.services.storage import Storage


SessionDep = Annotated[Session, Depends(get_session)]


def get_current_owner(
    request: Request,
    session: SessionDep,
    api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> str:
    """Resolve the owner id for this request.

    Two credentials are accepted. A session cookie is what the browser sends, and
    its user id becomes the owner. The static API key stays for scripts, curl
    and the documented `curl` demos, and keeps resolving to the configured
    owner id.
    """
    settings: Settings = request.app.state.settings
    user = user_for_token(session, request.cookies.get(settings.auth_cookie_name))
    if user is not None:
        return user.id

    configured = settings.api_key
    if (
        configured is not None
        and api_key is not None
        and hmac.compare_digest(
            api_key.encode("utf-8"), configured.get_secret_value().encode("utf-8")
        )
    ):
        return settings.api_key_owner_id
    raise AuthenticationError()


OwnerDep = Annotated[str, Depends(get_current_owner)]


def get_current_user(request: Request, session: SessionDep) -> User:
    """The signed-in account. Unlike `get_current_owner` there is no key fallback.

    `/auth/me` and logout describe a browser session specifically, so an API-key
    caller has no account to report and is refused instead of being faked.
    """
    settings: Settings = request.app.state.settings
    user = user_for_token(session, request.cookies.get(settings.auth_cookie_name))
    if user is None:
        raise AuthenticationError()
    return user


UserDep = Annotated[User, Depends(get_current_user)]


def get_settings_dep(request: Request) -> Settings:
    return request.app.state.settings


def get_extractor(request: Request) -> MetadataExtractor:
    return request.app.state.extractor


def get_storage(request: Request) -> Storage:
    return request.app.state.storage


def get_job_runner(request: Request) -> JobRunner:
    return request.app.state.job_runner


def get_classifier(request: Request) -> Classifier | None:
    return request.app.state.classifier


def get_pipeline_context(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings_dep)],
    extractor: Annotated[MetadataExtractor, Depends(get_extractor)],
    storage: Annotated[Storage, Depends(get_storage)],
    classifier: Annotated[Classifier | None, Depends(get_classifier)],
) -> PipelineContext:
    return PipelineContext(
        settings=settings,
        extractor=extractor,
        storage=storage,
        session_factory=request.app.state.session_factory,
        classifier=classifier,
    )
