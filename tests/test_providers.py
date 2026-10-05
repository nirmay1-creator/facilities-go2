"""
Tests for the deterministic MockProvider and scenario fixtures.

Tests covered:
  6.  Six scenario fixtures classified correctly by mock provider
  7.  MockProvider implements AnalysisProvider interface
  8.  Fake HTTP transport (via httpx.MockTransport)
  9.  LM Studio timeout
  10. Malformed JSON response
  11. Unknown category in model output
  12. Invalid priority in model output
"""
from __future__ import annotations

import json

import httpx
import pytest

from facilities.models import AnalysisRequest, AnalysisResult
from facilities.providers.base import AnalysisProvider
from facilities.providers.mock_provider import MockProvider
from facilities.providers.lmstudio_provider import LmStudioProvider


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _req(subject: str, text: str) -> AnalysisRequest:
    return AnalysisRequest(subject=subject, request_text=text)


# ---------------------------------------------------------------------------
# Test 7: MockProvider is an AnalysisProvider
# ---------------------------------------------------------------------------
def test_mock_provider_is_analysis_provider() -> None:
    assert isinstance(MockProvider(), AnalysisProvider)


# ---------------------------------------------------------------------------
# Test 6: Six scenario fixtures
# ---------------------------------------------------------------------------
FIXTURES = [
    # (subject, request_text, expected_category)
    (
        "Meeting room lights fail",
        "The lights in meeting room B3 stopped working completely. The room has been dark since yesterday morning.",
        "electrical",
    ),
    (
        "Power outlet sparking in lab",
        "A power socket in the computer lab on floor 2 is sparking when a plug is inserted.",
        "electrical",
    ),
    (
        "Water leak in corridor",
        "There is a visible water leak coming from the ceiling pipe in the main corridor near room 105.",
        "plumbing",
    ),
    (
        "Blocked sink in staff kitchen",
        "The sink drain in the staff kitchen on level 3 is completely blocked and the sink is overflowing.",
        "plumbing",
    ),
    (
        "Radiator stays cold",
        "The radiator in office 204 has not been working for two weeks. The room temperature is very low.",
        "heating",
    ),
    (
        "Boiler making loud noise",
        "The boiler in the basement plant room is making a loud banging noise every time heating starts.",
        "heating",
    ),
]


@pytest.mark.parametrize("subject,text,expected_category", FIXTURES)
def test_fixture_classification(
    subject: str, text: str, expected_category: str
) -> None:
    provider = MockProvider()
    result = provider.analyze(_req(subject, text))
    assert result.category == expected_category, (
        f"Expected {expected_category!r} for '{subject}', got {result.category!r}"
    )
    assert result.requires_review is True
    assert result.priority in ("low", "medium", "high")
    assert len(result.summary) >= 10
    assert len(result.next_action) >= 10


# ---------------------------------------------------------------------------
# Test 8: Fake HTTP transport (LmStudioProvider with mock transport)
# ---------------------------------------------------------------------------
def _make_mock_transport(json_body: dict | str, status_code: int = 200):
    """Return an httpx.MockTransport that replies with the given body."""
    if isinstance(json_body, dict):
        body_bytes = json.dumps(json_body).encode()
    else:
        body_bytes = json_body.encode()

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=status_code,
            content=body_bytes,
            headers={"Content-Type": "application/json"},
        )

    return httpx.MockTransport(handler)


def _lm_response(content: str) -> dict:
    """Build a minimal LM Studio chat-completions response envelope."""
    return {
        "choices": [
            {"message": {"role": "assistant", "content": content}}
        ]
    }


VALID_PAYLOAD = json.dumps(
    {
        "summary": "Lights in meeting room B3 are not working.",
        "next_action": "Route to electrical maintenance team for inspection.",
        "category": "electrical",
        "priority": "high",
        "requires_review": True,
    }
)


def test_fake_http_transport_valid() -> None:
    """LmStudioProvider correctly parses a valid mock HTTP response."""
    transport = _make_mock_transport(_lm_response(VALID_PAYLOAD))
    client = httpx.Client(transport=transport)
    provider = LmStudioProvider(http_client=client)
    result = provider.analyze(_req("Meeting room lights fail", "The lights stopped working completely."))
    assert result.category == "electrical"
    assert result.requires_review is True


# ---------------------------------------------------------------------------
# Test 9: LM Studio timeout
# ---------------------------------------------------------------------------
def test_lmstudio_timeout() -> None:
    """LmStudioProvider raises on timeout."""

    def slow_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("Timed out", request=request)

    transport = httpx.MockTransport(slow_handler)
    client = httpx.Client(transport=transport)
    provider = LmStudioProvider(http_client=client, timeout=1)

    with pytest.raises(httpx.ReadTimeout):
        provider.analyze(_req("Test timeout", "This should trigger a timeout from the provider."))


# ---------------------------------------------------------------------------
# Test 10: Malformed JSON
# ---------------------------------------------------------------------------
def test_malformed_json_raises() -> None:
    bad_content = "This is not JSON at all, just text."
    transport = _make_mock_transport(_lm_response(bad_content))
    client = httpx.Client(transport=transport)
    provider = LmStudioProvider(http_client=client)

    with pytest.raises(ValueError, match="malformed JSON"):
        provider.analyze(_req("Broken light", "The light in the hallway stopped working."))


# ---------------------------------------------------------------------------
# Test 11: Unknown category
# ---------------------------------------------------------------------------
def test_unknown_category_raises() -> None:
    bad_payload = json.dumps(
        {
            "summary": "Something happened to a widget in the building.",
            "next_action": "Please fix the widget as soon as possible.",
            "category": "approved",   # ← not a valid category
            "priority": "high",
            "requires_review": True,
        }
    )
    transport = _make_mock_transport(_lm_response(bad_payload))
    client = httpx.Client(transport=transport)
    provider = LmStudioProvider(http_client=client)

    with pytest.raises(ValueError, match="validation"):
        provider.analyze(_req("Widget issue", "The widget in the building is broken and needs attention."))


# ---------------------------------------------------------------------------
# Test 12: Invalid priority
# ---------------------------------------------------------------------------
def test_invalid_priority_raises() -> None:
    bad_payload = json.dumps(
        {
            "summary": "Pipe is dripping water in the corridor near room 105.",
            "next_action": "Route to plumbing team for immediate inspection.",
            "category": "plumbing",
            "priority": "done",     # ← not a valid priority
            "requires_review": True,
        }
    )
    transport = _make_mock_transport(_lm_response(bad_payload))
    client = httpx.Client(transport=transport)
    provider = LmStudioProvider(http_client=client)

    with pytest.raises(ValueError, match="validation"):
        provider.analyze(_req("Water leak", "There is a visible water leak in the corridor near room 105."))
