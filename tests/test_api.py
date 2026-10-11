"""
Automated Integration and Unit Tests for Enterprise Compliance Intelligence API.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.models import QueryResponse


@pytest.fixture
def client():
    return TestClient(app)


def test_health_live(client):
    """Liveness probe must return 200 and sanitized process info."""
    response = client.get("/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "live"
    assert data["service"] == "enterprise-compliance-intelligence"
    assert "uptime_seconds" in data
    # Ensure no secrets leaked
    assert "api_key" not in str(data).lower()
    assert "token" not in str(data).lower()


def test_health_ready(client):
    """Readiness probe must report dependency health without exposing credentials."""
    response = client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in {"ready", "degraded", "not_ready"}
    assert "dependencies" in data
    deps = data["dependencies"]
    assert "qdrant" in deps
    assert "ollama" in deps
    assert "embeddings" in deps


def test_query_validation_errors(client):
    """Input validation must reject malformed, empty, or disallowed requests."""
    # Too short
    resp_short = client.post("/api/v1/query", json={"question": "ab"})
    assert resp_short.status_code == 422

    # Whitespace only
    resp_empty = client.post("/api/v1/query", json={"question": "   "})
    assert resp_empty.status_code == 422

    # Disallowed metadata filter key
    resp_bad_filter = client.post(
        "/api/v1/query",
        json={
            "question": "What is the policy?",
            "metadata_filters": {"malicious_column_sql": "inject"},
        },
    )
    assert resp_bad_filter.status_code == 422

    # Non-scalar metadata filter value
    resp_bad_type = client.post(
        "/api/v1/query",
        json={
            "question": "What is the policy?",
            "metadata_filters": {"vendor": {"nested": "dict"}},
        },
    )
    assert resp_bad_type.status_code == 422


def test_documents_listing_sanitized(client):
    """Document listing must never expose raw document chunk text or file system paths."""
    response = client.get("/api/v1/documents")
    assert response.status_code == 200
    data = response.json()
    assert "total_documents" in data
    assert "documents" in data
    for doc in data["documents"]:
        assert "document_id" in doc
        # Verify text and filepath are not leaked
        assert "text" not in doc
        assert "path" not in doc
        assert "/" not in doc.get("document_id", "")


def test_ingestion_admin_authentication(client):
    """Corpus ingestion must strictly reject anonymous and unauthenticated callers."""
    # No header provided
    resp_anon = client.post("/api/v1/documents/ingest")
    assert resp_anon.status_code in {401, 403}

    # Invalid admin key
    resp_invalid = client.post(
        "/api/v1/documents/ingest",
        headers={"X-Admin-Key": "completely_wrong_key"},
    )
    assert resp_invalid.status_code in {401, 403}


def test_query_schema_and_refusal_behavior(client, monkeypatch):
    """
    Test that queries invoke canonical logic and response contracts are strictly validated.
    """
    # Test refusal query: opinion
    resp = client.post("/api/v1/query", json={"question": "What do you think about AI safety?"})
    assert resp.status_code == 200
    data = resp.json()

    # Must validate against Pydantic model
    validated = QueryResponse(**data)
    assert validated.trace_id
    assert validated.is_refusal is True
    assert validated.refusal_reason is not None
    assert "refuse" in validated.decision_path.lower()


def test_grounded_query_success(client):
    """
    Test positive flow: query against ingested document produces grounded answer with sources and claims.
    """
    resp = client.post(
        "/api/v1/query",
        json={"question": "Which compliance programs does AWS maintain to help customers satisfy regulatory requirements?"},
    )
    assert resp.status_code == 200
    data = resp.json()
    validated = QueryResponse(**data)
    assert validated.is_refusal is False
    assert len(validated.sources) >= 1
    assert any("SOC" in validated.answer or "ISO" in validated.answer or "compliance" in validated.answer.lower() for _ in [1])
    assert validated.confidence is not None
    assert validated.trace_id


def test_llm_outage_error_handling(client, monkeypatch):
    """
    If the LLM inference provider is unreachable, API must return HTTP 503 instead of masking the error.
    """
    import api.main
    monkeypatch.setattr(
        api.main,
        "run_enterprise_query",
        lambda *args, **kwargs: {"generation_error": "llm_unavailable"},
    )
    resp = client.post(
        "/api/v1/query",
        json={"question": "What is the policy?"},
    )
    assert resp.status_code == 503
    data = resp.json()
    assert data["detail"]["error"] == "llm_unavailable"
