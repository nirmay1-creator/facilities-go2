"""
AnalysisService – orchestrates provider selection and result validation.

Acts as the business-logic layer between the FastAPI layer and the providers.
Ensures that:
  - Only validated results reach the database.
  - The provider is selected based on PROVIDER_MODE env var.
  - Errors are propagated as plain Python exceptions (FastAPI converts them).
"""
from __future__ import annotations

from facilities.config import settings
from facilities.models import AnalysisRequest, AnalysisResult
from facilities.providers.base import AnalysisProvider


class AnalysisService:
    """Runs analysis via the configured provider."""

    def __init__(self, provider: AnalysisProvider | None = None) -> None:
        if provider is not None:
            self._provider = provider
        else:
            self._provider = _default_provider()

    def analyze(self, request: AnalysisRequest) -> AnalysisResult:
        """
        Delegate to the provider and return a validated AnalysisResult.

        Raises an exception if the provider fails for any reason.
        The caller (FastAPI endpoint) must NOT persist failed results.
        """
        return self._provider.analyze(request)


def _default_provider() -> AnalysisProvider:
    """Return the provider specified by PROVIDER_MODE."""
    mode = settings.provider_mode.lower()
    if mode == "mock":
        from facilities.providers.mock_provider import MockProvider
        return MockProvider()
    # Default: lmstudio
    from facilities.providers.lmstudio_provider import LmStudioProvider
    return LmStudioProvider()
