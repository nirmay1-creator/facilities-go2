"""
AnalysisProvider abstract interface.

All providers (LM Studio, mock) must implement this interface.
Provider code must NOT be placed directly inside the Streamlit UI.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from facilities.models import AnalysisRequest, AnalysisResult


class AnalysisProvider(ABC):
    """Abstract base class for AI analysis providers."""

    @abstractmethod
    def analyze(self, request: AnalysisRequest) -> AnalysisResult:
        """
        Analyse the facilities request and return a validated AnalysisResult.

        Implementations must:
        - Return a fully-validated AnalysisResult (never raw LLM text).
        - Set requires_review=True unconditionally.
        - Raise an exception on any failure (timeout, bad JSON, invalid fields).
        """
        ...
