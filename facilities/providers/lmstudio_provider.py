"""
LM Studio provider for Qwen3-VL-8B.

Sends a structured JSON prompt to the local LM Studio inference server
and validates the response using Pydantic before returning.

Configuration is read from environment variables (see config.py / .env).
Never hard-codes credentials, URLs, or model secrets.
Uses a finite HTTP timeout.
"""
from __future__ import annotations

import json

import httpx
from pydantic import ValidationError

from facilities.config import settings
from facilities.models import AnalysisRequest, AnalysisResult
from facilities.providers.base import AnalysisProvider

# ---------------------------------------------------------------------------
# Prompt template
# ---------------------------------------------------------------------------
_SYSTEM_PROMPT = """\
You are a facilities request triage assistant for a university campus.

Your task is to read a maintenance request and classify it.

RULES:
1. You MUST classify the request into EXACTLY ONE of these categories:
   - electrical
   - plumbing
   - heating
2. You MUST assign priority as EXACTLY ONE of: low, medium, high.
3. You MUST always set requires_review to true. No exceptions.
4. Do NOT give repair instructions.
5. Do NOT claim that any maintenance action has already happened.
6. If the request is ambiguous, still classify it and keep requires_review true.
7. Your response MUST be valid JSON only. No markdown, no code fences, no explanation.

OUTPUT FORMAT (exact JSON, nothing else):
{
  "summary": "<10 to 240 character summary of the request>",
  "next_action": "<10 to 240 character recommended next action for the team>",
  "category": "<electrical|plumbing|heating>",
  "priority": "<low|medium|high>",
  "requires_review": true
}
"""


def _build_user_message(request: AnalysisRequest) -> str:
    return (
        f"Subject: {request.subject}\n\n"
        f"Request description:\n{request.request_text}"
    )


class LmStudioProvider(AnalysisProvider):
    """
    Calls LM Studio's OpenAI-compatible chat completions endpoint.

    The model is Qwen3-VL-8B running locally via LM Studio.
    Validates the JSON output strictly before returning.
    """

    def __init__(
        self,
        base_url: str | None = None,
        model_name: str | None = None,
        timeout: int | None = None,
        max_tokens: int | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._base_url = (base_url or settings.lm_studio_url).rstrip("/")
        self._model_name = model_name or settings.model_name
        self._timeout = timeout or settings.request_timeout
        self._max_tokens = max_tokens or settings.max_tokens
        # Allow injection of a custom client (e.g. MockTransport in tests)
        self._http_client = http_client

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------
    def analyze(self, request: AnalysisRequest) -> AnalysisResult:
        payload = {
            "model": self._model_name,
            "messages": [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": _build_user_message(request)},
            ],
            "max_tokens": self._max_tokens,
            "temperature": 0.0,
        }

        raw_text = self._call_lm_studio(payload)
        return self._parse_and_validate(raw_text)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _call_lm_studio(self, payload: dict) -> str:
        url = f"{self._base_url}/chat/completions"

        if self._http_client is not None:
            # Injected client (e.g. test MockTransport)
            response = self._http_client.post(
                url,
                json=payload,
                timeout=self._timeout,
            )
        else:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.post(url, json=payload)

        response.raise_for_status()
        data = response.json()

        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError(
                f"Unexpected LM Studio response structure: {data}"
            ) from exc

        return content.strip()

    @staticmethod
    def _parse_and_validate(raw_text: str) -> AnalysisResult:
        """
        Parse and Pydantic-validate the model output.

        Raises ValueError for:
        - malformed JSON
        - missing / invalid fields
        - wrong category or priority values
        - requires_review not True
        - string length violations
        """
        # Strip accidental markdown fences if present
        text = raw_text
        if text.startswith("```"):
            lines = text.splitlines()
            # Remove first and last fence lines
            text = "\n".join(
                line for line in lines
                if not line.startswith("```")
            ).strip()

        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Model returned malformed JSON: {exc}\nRaw output: {raw_text!r}"
            ) from exc

        try:
            result = AnalysisResult(**data)
        except ValidationError as exc:
            raise ValueError(
                f"Model output failed Pydantic validation: {exc}\nRaw data: {data}"
            ) from exc

        return result
