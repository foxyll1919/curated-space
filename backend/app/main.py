import logging
import asyncio
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.cors import CORSMiddleware

from sqlalchemy import inspect

from app.api.routes.auth import router as auth_router
from app.api.routes.health import router as health_router
from app.api.routes.items import router as items_router
from app.api.routes.usage import router as usage_router
from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.core.logging import configure_logging
from app.core.middleware import RequestSecurityMiddleware
from app.db.session import create_database_engine, create_session_factory
from app.services.auth import purge_expired_sessions
from app.services.classification.base import Classifier
from app.services.classification.sklearn_svc import (
    ClassifierLoadError,
    SklearnSvcClassifier,
    UnavailableClassifier,
)
from app.services.extraction.base import MetadataExtractor
from app.services.extraction.gemini import GeminiExtractor
from app.services.jobs import (
    BackgroundJobRunner,
    purge_expired_items,
    recover_interrupted_items,
    retain_task,
)
from app.services.pipeline import PipelineContext
from app.services.rate_limit import FixedWindowRateLimiter
from app.services.storage import LocalDiskStorage, Storage


PRODUCTION_ENVIRONMENTS = frozenset({"production", "prod"})


def build_classifier(settings: Settings) -> Classifier:
    """Load the classifier once at startup.

    A missing artifact is fatal in production and a loud warning in development,
    so a misconfigured deploy cannot silently serve items with no labels.
    """
    strict = settings.environment.lower() in PRODUCTION_ENVIRONMENTS
    classifier = SklearnSvcClassifier(settings.classifier_artifact, strict_version=strict)
    try:
        classifier.load()
    except ClassifierLoadError as exc:
        if settings.classifier_required and strict:
            raise
        logging.getLogger(__name__).warning("classifier_unavailable", extra={"stage": "startup"})
        return UnavailableClassifier(str(exc))
    return classifier


def create_app(
    settings: Settings | None = None,
    *,
    extractor: MetadataExtractor | None = None,
    storage: Storage | None = None,
    classifier: Classifier | None = None,
) -> FastAPI:
    app_settings = settings or get_settings()
    configure_logging(app_settings.log_level)
    engine = create_database_engine(app_settings)
    app_extractor = extractor or GeminiExtractor(app_settings)
    app_storage = storage or LocalDiskStorage(app_settings.storage_path)
    app_classifier = classifier or build_classifier(app_settings)
    pipeline_context = PipelineContext(
        settings=app_settings,
        extractor=app_extractor,
        storage=app_storage,
        session_factory=create_session_factory(engine),
        classifier=app_classifier,
    )
    job_runner = BackgroundJobRunner(app_settings.max_concurrent_analyses)
    recovery_tasks: set[asyncio.Task[None]] = set()

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        with pipeline_context.session_factory() as startup_session:
            if inspect(startup_session.get_bind()).has_table("sessions"):
                expired_sessions = purge_expired_sessions(startup_session)
                if expired_sessions:
                    logging.getLogger(__name__).info(
                        "expired_sessions_purged",
                        extra={"stage": "auth", "session_count": expired_sessions},
                    )
        expired = purge_expired_items(
            pipeline_context.session_factory,
            app_storage,
            retention_days=app_settings.item_retention_days,
        )
        if expired:
            logging.getLogger(__name__).info(
                "expired_items_purged", extra={"stage": "retention", "item_count": expired}
            )
        pending_ids = recover_interrupted_items(
            pipeline_context.session_factory,
            stuck_after_minutes=app_settings.stuck_job_timeout_minutes,
        )
        for item_id in pending_ids:
            task = asyncio.create_task(job_runner.run_recovered(item_id, pipeline_context))
            retain_task(task, recovery_tasks)
        try:
            yield
        finally:
            if recovery_tasks:
                await asyncio.gather(*tuple(recovery_tasks), return_exceptions=True)
            engine.dispose()

    app = FastAPI(
        title="Curated Space API",
        description="Backend for the Curated Space screenshot library",
        version="2.0.0",
        lifespan=lifespan,
    )
    app.state.settings = app_settings
    app.state.database_engine = engine
    app.state.session_factory = pipeline_context.session_factory
    # All three are swappable so tests inject fakes and never touch a real
    # provider, a real uploads directory or the real model artifact.
    app.state.extractor = app_extractor
    app.state.storage = app_storage
    app.state.classifier = app_classifier
    app.state.pipeline_context = pipeline_context
    app.state.job_runner = job_runner
    app.state.recovery_tasks = recovery_tasks
    app.state.rate_limiter = FixedWindowRateLimiter()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.allowed_origins,
        # The session cookie is the app's credential, so a configured origin
        # list must be allowed to send it. Wildcards are rejected by settings.
        allow_credentials=bool(app_settings.allowed_origins),
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "X-API-Key", "X-Request-ID"],
    )
    app.add_middleware(
        RequestSecurityMiddleware, max_body_bytes=app_settings.max_request_body_bytes
    )
    app.include_router(health_router, prefix="/api/v1")
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(items_router, prefix="/api/v1")
    app.include_router(usage_router, prefix="/api/v1")

    @app.exception_handler(AppError)
    async def handle_app_error(_request: Request, exc: AppError) -> JSONResponse:
        """One error envelope for the whole API. Detail goes to the log only."""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.public_message,
                    "request_id": getattr(_request.state, "request_id", None),
                }
            },
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, _exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "code": "bad_request",
                    "message": "The request could not be processed.",
                    "request_id": getattr(request.state, "request_id", None),
                }
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = "not_found" if exc.status_code == 404 else "http_error"
        message = (
            "The requested resource does not exist."
            if exc.status_code == 404
            else "The request could not be processed."
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": code,
                    "message": message,
                    "request_id": getattr(request.state, "request_id", None),
                }
            },
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, _exc: Exception) -> JSONResponse:
        logging.getLogger(__name__).exception(
            "unhandled_api_error",
            extra={"request_id": getattr(request.state, "request_id", None), "stage": "api"},
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "internal_error",
                    "message": "An unexpected error occurred.",
                    "request_id": getattr(request.state, "request_id", None),
                }
            },
        )

    @app.get("/", include_in_schema=False)
    def home() -> dict[str, str]:
        return {"message": "Curated Space API is running"}

    @app.get("/api/health", include_in_schema=False)
    def legacy_health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
