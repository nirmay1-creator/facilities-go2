"""
Tests for API endpoints:
  GET  /health
  POST /api/analyze  (valid + invalid input variants)
  GET  /api/history

Also tests:
  - failed inference does NOT create a history record (req 14)
"""
from __future__ import annotations

import json
import os

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Test 15: GET /health
# ---------------------------------------------------------------------------
def test_health(api_client: TestClient) -> None:
    resp = api_client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"


# ---------------------------------------------------------------------------
# Test 1: Valid input → 200 + valid HistoryRecord
# ---------------------------------------------------------------------------
def test_analyze_valid_input(api_client: TestClient) -> None:
    resp = api_client.post(
        "/api/analyze",
        json={
            "subject": "Meeting room lights fail",
            "request_text": "The lights in meeting room B3 stopped working completely.",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["category"] in ("electrical", "plumbing", "heating")
    assert data["priority"] in ("low", "medium", "high")
    assert data["requires_review"] is True
    assert len(data["summary"]) >= 10
    assert len(data["next_action"]) >= 10
    assert "id" in data


# ---------------------------------------------------------------------------
# Test 2: Subject too short
# ---------------------------------------------------------------------------
def test_analyze_subject_too_short(api_client: TestClient) -> None:
    resp = api_client.post(
        "/api/analyze",
        json={
            "subject": "AB",
            "request_text": "The lights in meeting room B3 stopped working.",
        },
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Test 3: Subject too long
# ---------------------------------------------------------------------------
def test_analyze_subject_too_long(api_client: TestClient) -> None:
    resp = api_client.post(
        "/api/analyze",
        json={
            "subject": "X" * 101,
            "request_text": "The lights in meeting room B3 stopped working.",
        },
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Test 4: Request text too short
# ---------------------------------------------------------------------------
def test_analyze_request_text_too_short(api_client: TestClient) -> None:
    resp = api_client.post(
        "/api/analyze",
        json={
            "subject": "Lights out",
            "request_text": "Short",
        },
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Test 5: Request text too long
# ---------------------------------------------------------------------------
def test_analyze_request_text_too_long(api_client: TestClient) -> None:
    resp = api_client.post(
        "/api/analyze",
        json={
            "subject": "Lights out",
            "request_text": "A" * 4001,
        },
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Test 16: POST /api/analyze endpoint shape
# ---------------------------------------------------------------------------
def test_analyze_endpoint_returns_history_record_shape(api_client: TestClient) -> None:
    resp = api_client.post(
        "/api/analyze",
        json={
            "subject": "Radiator stays cold",
            "request_text": "The radiator in office 204 has not worked for two weeks.",
        },
    )
    assert resp.status_code == 200
    keys = resp.json().keys()
    for expected in ("id", "subject", "request_text", "summary", "next_action",
                     "category", "priority", "requires_review", "created_at"):
        assert expected in keys


# ---------------------------------------------------------------------------
# Test 17: GET /api/history
# ---------------------------------------------------------------------------
def test_history_returns_list(api_client: TestClient) -> None:
    resp = api_client.get("/api/history")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


# ---------------------------------------------------------------------------
# Test 13 + 14: Failed inference → 502 and NO history record created
# ---------------------------------------------------------------------------
def test_failed_inference_returns_502(api_client: TestClient) -> None:
    """Force a provider error and verify 502 is returned."""
    from unittest.mock import patch

    with patch(
        "facilities.service.AnalysisService.analyze",
        side_effect=RuntimeError("Simulated inference failure"),
    ):
        resp = api_client.post(
            "/api/analyze",
            json={
                "subject": "Test failure",
                "request_text": "This request should trigger a provider failure.",
            },
        )
    assert resp.status_code == 502
    assert "Inference failed" in resp.json()["detail"]


def test_failed_inference_does_not_create_history(api_client: TestClient) -> None:
    """After a failed inference, history count must not increase."""
    from unittest.mock import patch
    from facilities.database import get_history

    before = len(get_history())

    with patch(
        "facilities.service.AnalysisService.analyze",
        side_effect=RuntimeError("Simulated inference failure"),
    ):
        api_client.post(
            "/api/analyze",
            json={
                "subject": "Test failure two",
                "request_text": "This request should NOT be stored anywhere.",
            },
        )

    after = len(get_history())
    assert after == before, (
        f"History grew from {before} to {after} despite inference failure"
    )
