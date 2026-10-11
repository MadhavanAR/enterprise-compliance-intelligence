"""
Security Hardening and Regression Test Suite.
Verifies rate limiting, input limits, fail-closed access controls, and refusal logic.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.main import app
import api.security as sec


@pytest.fixture
def client():
    return TestClient(app)


def test_input_length_boundary_rejection(client):
    """Questions exceeding 2000 characters must be rejected with HTTP 422."""
    giant_question = "A" * 2001
    resp = client.post("/api/v1/query", json={"question": giant_question})
    assert resp.status_code == 422


def test_rate_limiting_enforcement(client, monkeypatch):
    """Exceeding request rate limit must return HTTP 429."""
    # Temporarily set limit low for testing
    monkeypatch.setattr(sec, "RATE_LIMIT_PER_MINUTE", 3)
    sec._request_records.clear()

    # First 3 requests should pass input validation (or 422, but not 429)
    for _ in range(3):
        r = client.post("/api/v1/query", json={"question": "ab"})  # fast 422 check
        assert r.status_code != 429

    # 4th request must trigger 429
    r_blocked = client.post("/api/v1/query", json={"question": "ab"})
    assert r_blocked.status_code == 429
    assert "rate_limit_exceeded" in r_blocked.json()["detail"]["error"]

    # Reset
    sec._request_records.clear()


def test_read_only_mode_blocks_ingestion(client, monkeypatch):
    """When READ_ONLY_MODE=true, ingestion must return HTTP 403 even with valid admin key."""
    import api.main as api_mod
    monkeypatch.setattr(sec, "ADMIN_API_KEY", "super_secret_admin_key")
    monkeypatch.setattr(api_mod, "READ_ONLY_MODE", True)

    resp = client.post(
        "/api/v1/documents/ingest",
        headers={"X-Admin-Key": "super_secret_admin_key"},
    )
    assert resp.status_code == 403
    assert resp.json()["detail"]["error"] == "read_only_mode"


def test_global_exception_handler_sanitizes_errors(client, monkeypatch):
    """Unhandled exceptions must never leak stack traces or secrets to the caller."""
    import api.main as api_mod

    def broken_engine(*args, **kwargs):
        raise RuntimeError("Secret database password db_pass_12345 in internal code!")

    monkeypatch.setattr(api_mod, "run_enterprise_query", broken_engine)

    resp = client.post("/api/v1/query", json={"question": "What are AWS policies?"})
    assert resp.status_code == 500
    data = resp.json()
    err_obj = data.get("detail", data)
    assert err_obj.get("error") in {"engine_failure", "internal_server_error"}
    assert "trace_id" in err_obj
    # Invariant: Exception text and secret password must NOT be in response
    assert "db_pass_12345" not in str(data)
    assert "Traceback" not in str(data)
