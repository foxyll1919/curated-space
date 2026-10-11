from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, Request, Response
from pydantic import BaseModel
from sqlalchemy import inspect, text


router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str


class ReadyResponse(BaseModel):
    status: str
    components: dict[str, str]


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


def _database_status(request: Request) -> str:
    engine = request.app.state.database_engine
    try:
        with engine.connect() as connection:
            if not inspect(connection).has_table("items"):
                return "schema_not_migrated"
            connection.execute(text("SELECT 1 FROM items LIMIT 1"))
        return "ok"
    except Exception:
        return "unavailable"


def _storage_status(storage_path: Path) -> str:
    try:
        storage_path.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile(prefix=".ready-", dir=storage_path, delete=True):
            pass
        return "ok"
    except OSError:
        return "unavailable"


@router.get("/ready", response_model=ReadyResponse)
def ready(request: Request, response: Response) -> ReadyResponse:
    components = {
        "database": _database_status(request),
        "storage": _storage_status(request.app.state.settings.storage_path),
        "classifier": "deferred_until_milestone_4",
    }
    extractor = request.app.state.extractor
    components["extractor"] = "ok" if getattr(extractor, "is_configured", True) else "no_api_key"
    is_ready = components["database"] == "ok" and components["storage"] == "ok"
    response.status_code = 200 if is_ready else 503
    return ReadyResponse(status="ready" if is_ready else "not_ready", components=components)
