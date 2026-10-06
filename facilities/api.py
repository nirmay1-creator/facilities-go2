"""
FastAPI application – Facilities Request Triage API.

Endpoints:
  GET  /health           – liveness check
  POST /api/analyze      – validate input, run provider, save to DB, return result
  GET  /api/history      – return previous validated records from SQLite
"""
from __future__ import annotations

from fastapi import FastAPI, HTTPException

from facilities.database import get_history, init_db, save_analysis
from facilities.models import AnalysisRequest, AnalysisResult, HistoryRecord
from facilities.service import AnalysisService

app = FastAPI(
    title="Facilities Request Triage",
    description="AI-powered campus facilities request triage using Qwen3-VL-8B via LM Studio.",
    version="1.0.0",
)


# Initialise DB and service on startup
@app.on_event("startup")
def on_startup() -> None:
    init_db()


# ---------------------------------------------------------------------------
# Dependency: AnalysisService instance (allows override in tests)
# ---------------------------------------------------------------------------
def get_service() -> AnalysisService:
    return AnalysisService()


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------
@app.get("/health", tags=["ops"])
def health() -> dict:
    """Liveness probe."""
    return {"status": "ok", "service": "facilities-triage"}


# ---------------------------------------------------------------------------
# POST /api/analyze
# ---------------------------------------------------------------------------
@app.post(
    "/api/analyze",
    response_model=HistoryRecord,
    tags=["triage"],
    summary="Submit a facilities request for AI triage",
)
def analyze(body: AnalysisRequest) -> HistoryRecord:
    """
    1. Validate input (Pydantic – 422 on failure).
    2. Call AnalysisService → AnalysisProvider.
    3. Validate provider output (Pydantic).
    4. Persist only validated result to SQLite.
    5. Return the persisted HistoryRecord.

    If inference fails for any reason, returns 502 and does NOT save a record.
    """
    service = get_service()

    try:
        result: AnalysisResult = service.analyze(body)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Inference failed: {exc}",
        ) from exc

    # Persist the validated result
    record = save_analysis(
        subject=body.subject,
        request_text=body.request_text,
        result=result,
    )
    return record


# ---------------------------------------------------------------------------
# GET /api/history
# ---------------------------------------------------------------------------
@app.get(
    "/api/history",
    response_model=list[HistoryRecord],
    tags=["triage"],
    summary="Retrieve previous triage records",
)
def history() -> list[HistoryRecord]:
    """Return the most recent validated analysis records from SQLite."""
    return get_history()
