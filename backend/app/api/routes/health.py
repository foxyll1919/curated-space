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


def _classifier_status(request: Request) -> str:
    classifier = request.app.state.classifier
    if classifier.is_ready:
        return "ok"
    status = getattr(classifier, "status", None)
    return getattr(status, "name", "unavailable")


def _auth_status(request: Request) -> tuple[str, str]:
    """Report both credential paths. Either one alone can guard the API."""
    settings = request.app.state.settings
    api_key = "ok" if settings.api_key is not None else "unconfigured"
    try:
        with request.app.state.database_engine.connect() as connection:
            if not inspect(connection).has_table("users"):
                return api_key, "schema_not_migrated"
            user_count = connection.execute(text("SELECT COUNT(*) FROM users")).scalar_one()
    except Exception:
        return api_key, "unavailable"
    if user_count:
        return api_key, "ok"
    # No account yet: the first registration is open, so this is not a fault.
    return api_key, "no_users_yet"


@router.get("/ready", response_model=ReadyResponse)
def ready(request: Request, response: Response) -> ReadyResponse:
    api_auth, session_auth = _auth_status(request)
    components = {
        "database": _database_status(request),
        "storage": _storage_status(request.app.state.settings.storage_path),
        "classifier": _classifier_status(request),
        "api_auth": api_auth,
        "session_auth": session_auth,
    }
    extractor = request.app.state.extractor
    components["extractor"] = "ok" if getattr(extractor, "is_configured", True) else "no_api_key"
    # The classifier is a challenger, not a dependency: a missing artifact is
    # reported but does not make the service unready. The same is true of either
    # credential path alone, so one working path is enough.
    auth_ready = {api_auth, session_auth} & {"ok", "no_users_yet"}
    is_ready = components["database"] == "ok" and components["storage"] == "ok" and bool(auth_ready)
    response.status_code = 200 if is_ready else 503
    return ReadyResponse(status="ready" if is_ready else "not_ready", components=components)
