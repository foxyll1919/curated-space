from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.db.session import get_session
from app.services.extraction.base import MetadataExtractor
from app.services.pipeline import PipelineContext
from app.services.storage import Storage


SessionDep = Annotated[Session, Depends(get_session)]


def get_settings_dep(request: Request) -> Settings:
    return request.app.state.settings


def get_extractor(request: Request) -> MetadataExtractor:
    return request.app.state.extractor


def get_storage(request: Request) -> Storage:
    return request.app.state.storage


def get_pipeline_context(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings_dep)],
    extractor: Annotated[MetadataExtractor, Depends(get_extractor)],
    storage: Annotated[Storage, Depends(get_storage)],
) -> PipelineContext:
    return PipelineContext(
        settings=settings,
        extractor=extractor,
        storage=storage,
        session_factory=request.app.state.session_factory,
    )
