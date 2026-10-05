"""
Deterministic mock provider.

Used by pytest and Jenkins CI where LM Studio / GPU is unavailable.
Classifies requests using simple keyword matching – always deterministic.
Implements the same AnalysisProvider interface as LmStudioProvider.
"""
from __future__ import annotations

from facilities.models import AnalysisRequest, AnalysisResult
from facilities.providers.base import AnalysisProvider

# ---------------------------------------------------------------------------
# Keyword → category mapping (order matters: checked top-to-bottom)
# ---------------------------------------------------------------------------
_ELECTRICAL_KEYWORDS = (
    "light", "lights", "lighting", "power", "outlet", "socket",
    "circuit", "breaker", "fuse", "electrical", "electric",
    "bulb", "lamp", "switch", "wiring", "voltage",
)
_PLUMBING_KEYWORDS = (
    "water", "leak", "pipe", "drain", "toilet", "tap",
    "sink", "flood", "plumbing", "drip", "sewage", "bathroom",
)
_HEATING_KEYWORDS = (
    "heat", "heating", "radiator", "boiler", "thermostat",
    "cold", "warm", "temperature", "hvac", "furnace",
)


def _keyword_category(text: str) -> str:
    lower = text.lower()
    for kw in _ELECTRICAL_KEYWORDS:
        if kw in lower:
            return "electrical"
    for kw in _PLUMBING_KEYWORDS:
        if kw in lower:
            return "plumbing"
    for kw in _HEATING_KEYWORDS:
        if kw in lower:
            return "heating"
    # Deterministic fallback – keeps CI predictable
    return "electrical"


def _keyword_priority(text: str) -> str:
    lower = text.lower()
    if any(w in lower for w in ("urgent", "emergency", "flood", "danger", "fail", "no power", "sparking")):
        return "high"
    if any(w in lower for w in ("intermittent", "sometimes", "occasional", "slow")):
        return "medium"
    return "low"


class MockProvider(AnalysisProvider):
    """
    Deterministic mock provider for tests and CI.

    Classifies using keyword matching; produces stable, reproducible output.
    Does NOT call any external service.
    """

    def analyze(self, request: AnalysisRequest) -> AnalysisResult:
        combined = f"{request.subject} {request.request_text}"
        category = _keyword_category(combined)
        priority = _keyword_priority(combined)

        summary = (
            f"Facilities request received regarding {request.subject.lower()}. "
            f"Classified as {category} issue."
        )
        # Truncate to 240 chars (safety for edge cases)
        summary = summary[:240]

        next_action = (
            f"Route to the {category} maintenance team for assessment. "
            "Await supervisor review before any work begins."
        )
        next_action = next_action[:240]

        return AnalysisResult(
            summary=summary,
            next_action=next_action,
            category=category,  # type: ignore[arg-type]
            priority=priority,  # type: ignore[arg-type]
            requires_review=True,
        )
