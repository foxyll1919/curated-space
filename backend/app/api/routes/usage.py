"""Cost and token visibility for development (brief section 7.7).

Read-only, derived entirely from `llm_usage`. It exposes counts, token totals
and estimated cost; no user content and no provider text.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import OwnerDep, SessionDep
from app.schemas.usage import UsageResponse, UsageWindow
from app.services.usage import summarize_usage, usage_windows


router = APIRouter(prefix="/usage", tags=["usage"])


@router.get("", response_model=UsageResponse)
def get_usage(session: SessionDep, _owner_id: OwnerDep) -> UsageResponse:
    windows = usage_windows()
    return UsageResponse(
        today=UsageWindow.from_bucket(summarize_usage(session, since=windows["today"])),
        last_7_days=UsageWindow.from_bucket(summarize_usage(session, since=windows["last_7_days"])),
    )
