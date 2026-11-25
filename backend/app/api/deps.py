from __future__ import annotations

import hmac
from typing import Annotated
from uuid import uuid4

from clerk_backend_api.security import authenticate_request
from clerk_backend_api.security.types import AuthenticateRequestOptions
from fastapi import Depends, Header, Request
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import AuthenticationError
from app.db.models import User
from app.db.session import get_session
from app.services.auth import user_for_clerk_id, user_for_token
from app.services.classification.base import Classifier
from app.services.extraction.base import MetadataExtractor
from app.services.jobs import JobRunner
from app.services.pipeline import PipelineContext
from app.services.storage import Storage
from app.services.embeddings import EmbeddingProvider


SessionDep = Annotated[Session, Depends(get_session)]


def clerk_subject_from_request(request: Request, settings: Settings) -> str:
    authorization = request.headers.get("Authorization")
    if authorization is None:
        raise AuthenticationError()
    scheme, separator, token = authorization.partition(" ")
    if scheme != "Bearer" or not separator or not token or token.strip() != token:
        raise AuthenticationError()
    if not settings.clerk_jwt_key or not settings.allowed_origins:
        raise AuthenticationError()

    jwt_key = settings.clerk_jwt_key.replace("\\n", "\n")
    auth_state = authenticate_request(
        request,
        AuthenticateRequestOptions(
            jwt_key=jwt_key,
            authorized_parties=settings.allowed_origins,
            accepts_token=["session_token"],
        ),
    )
    if not auth_state.is_signed_in or not auth_state.payload:
        raise AuthenticationError()
    subject = auth_state.payload.get("sub")
    if not isinstance(subject, str) or not subject:
        raise AuthenticationError()
    return subject


def _user_from_request_credentials(
    request: Request, session: Session, settings: Settings
) -> User | None:
    if request.headers.get("Authorization") is not None:
        subject = clerk_subject_from_request(request, settings)
        user = user_for_clerk_id(session, subject)
        if user is None:
            user = User(
                id=str(uuid4()),
                email=f"{subject}@clerk.local",
                password_hash="clerk:" + subject,
                clerk_user_id=subject,
            )
            session.add(user)
            session.commit()
        return user
    return user_for_token(session, request.cookies.get(settings.auth_cookie_name))


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
    user = _user_from_request_credentials(request, session, settings)
    if user is not None:
        return user.id

    if request.headers.get("Authorization") is not None:
        raise AuthenticationError()

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
    user = _user_from_request_credentials(request, session, settings)
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


def get_embedding_provider(request: Request) -> EmbeddingProvider:
    return request.app.state.embedding_provider


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
        embedding_provider=request.app.state.embedding_provider,
    )
