"""
Pydantic models for the Facilities Request Triage application.

- AnalysisRequest  : validated input coming from the user / API
- AnalysisResult   : validated output from the AI provider
- HistoryRecord    : row returned by GET /api/history
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Allowed enum literals (kept as type aliases for reuse in validation)
# ---------------------------------------------------------------------------
CategoryType = Literal["electrical", "plumbing", "heating"]
PriorityType = Literal["low", "medium", "high"]


# ---------------------------------------------------------------------------
# API input
# ---------------------------------------------------------------------------
class AnalysisRequest(BaseModel):
    """Input submitted by the user through the Streamlit UI / API."""

    subject: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Short title for the facilities request.",
    )
    request_text: str = Field(
        ...,
        min_length=10,
        max_length=4000,
        description="Full description of the problem.",
    )


# ---------------------------------------------------------------------------
# Provider / AI output
# ---------------------------------------------------------------------------
class AnalysisResult(BaseModel):
    """Validated structured result returned by the AI provider."""

    summary: str = Field(
        ...,
        min_length=10,
        max_length=240,
        description="Brief summary of the request (10–240 chars).",
    )
    next_action: str = Field(
        ...,
        min_length=10,
        max_length=240,
        description="Recommended next action for the facilities team (10–240 chars).",
    )
    category: CategoryType = Field(
        ...,
        description="One of: electrical, plumbing, heating.",
    )
    priority: PriorityType = Field(
        ...,
        description="One of: low, medium, high.",
    )
    requires_review: bool = Field(
        ...,
        description="Must always be True – every AI result requires human review.",
    )

    @field_validator("requires_review")
    @classmethod
    def must_require_review(cls, v: bool) -> bool:
        if v is not True:
            raise ValueError("requires_review must always be True")
        return v


# ---------------------------------------------------------------------------
# History record (API response row)
# ---------------------------------------------------------------------------
class HistoryRecord(BaseModel):
    """A previously analysed and saved request, returned by GET /api/history."""

    id: int
    subject: str
    request_text: str
    summary: str
    next_action: str
    category: CategoryType
    priority: PriorityType
    requires_review: bool
    created_at: datetime
