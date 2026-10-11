from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.routes.health import router as health_router
from app.api.routes.items import router as items_router
from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.core.logging import configure_logging
from app.db.session import create_database_engine, create_session_factory
from app.services.extraction.base import MetadataExtractor
from app.services.extraction.gemini import GeminiExtractor
from app.services.storage import LocalDiskStorage, Storage


def create_app(
    settings: Settings | None = None,
    *,
    extractor: MetadataExtractor | None = None,
    storage: Storage | None = None,
) -> FastAPI:
    app_settings = settings or get_settings()
    configure_logging(app_settings.log_level)
    engine = create_database_engine(app_settings)

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        yield
        engine.dispose()

    app = FastAPI(
        title="Curated Space API",
        description="Backend for the Curated Space screenshot library",
        version="2.0.0",
        lifespan=lifespan,
    )
    app.state.settings = app_settings
    app.state.database_engine = engine
    app.state.session_factory = create_session_factory(engine)
    # Both are swappable so tests inject fakes and never touch a real provider
    # or the real uploads directory.
    app.state.extractor = extractor or GeminiExtractor(app_settings)
    app.state.storage = storage or LocalDiskStorage(app_settings.storage_path)
    app.include_router(health_router, prefix="/api/v1")
    app.include_router(items_router, prefix="/api/v1")

    @app.exception_handler(AppError)
    async def handle_app_error(_request: Request, exc: AppError) -> JSONResponse:
        """One error envelope for the whole API. Detail goes to the log only."""
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.public_message}},
        )

    @app.get("/", include_in_schema=False)
    def home() -> dict[str, str]:
        return {"message": "Curated Space API is running"}

    @app.get("/api/health", include_in_schema=False)
    def legacy_health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
