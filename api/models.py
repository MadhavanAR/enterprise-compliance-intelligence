"""
API Data Models and Typed Response Contracts for Enterprise Compliance Intelligence.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class QueryRequest(BaseModel):
    """User query request with validation and optional metadata filtering."""

    question: str = Field(
        ...,
        min_length=3,
        max_length=2000,
        description="The compliance inquiry to evaluate against the knowledge base.",
        examples=["Which compliance programs does AWS maintain to satisfy regulatory requirements?"],
    )
    metadata_filters: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional whitelisted document metadata filters (e.g. {'vendor': 'AWS'}).",
    )

    @field_validator("question")
    @classmethod
    def sanitize_question(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Question cannot be empty or whitespace only.")
        return cleaned

    @field_validator("metadata_filters")
    @classmethod
    def validate_metadata_filters(cls, v: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if v is None:
            return None
        allowed_keys = {
            "vendor",
            "document_id",
            "author",
            "source",
            "document_type",
            "jurisdiction",
            "version",
        }
        for key, val in v.items():
            if key not in allowed_keys:
                raise ValueError(
                    f"Unsupported metadata filter '{key}'. Allowed fields: {sorted(allowed_keys)}"
                )
            if not isinstance(val, (str, int, float, bool)):
                raise ValueError(
                    f"Filter value for '{key}' must be a scalar (str, int, float, bool)."
                )
        return v


class ClaimModel(BaseModel):
    """Individual assertion synthesized by the grounded generator."""

    text: str = Field(..., description="Fact or policy claim synthesized from retrieved evidence.")
    source_doc: Optional[str] = Field(
        default=None,
        description="Identifier of the supporting source document reference (e.g. 'Doc 1').",
    )


class SourceReference(BaseModel):
    """Sanitized source citation reference for public inspection."""

    id: str = Field(..., description="Reference tag (e.g. 'Doc 1').")
    document_id: str = Field(..., description="Document identifier.")
    title: Optional[str] = Field(default=None, description="Document title if known.")
    author: Optional[str] = Field(default=None, description="Document author or issuing body.")
    vendor: Optional[str] = Field(default=None, description="Vendor or organization.")
    document_type: Optional[str] = Field(default=None, description="Category of compliance doc.")
    jurisdiction: Optional[str] = Field(default=None, description="Applicable jurisdiction.")
    version: Optional[str] = Field(default=None, description="Document version or publication date.")
    url: Optional[str] = Field(default=None, description="Public URL to canonical reference if available.")
    snippet: str = Field(..., description="Extracted context snippet supporting the answer.")
    score: Optional[float] = Field(default=None, description="Retrieval similarity score.")


class QueryResponse(BaseModel):
    """Stable, typed enterprise compliance response payload."""

    answer: str = Field(..., description="Synthesized answer grounded in retrieved evidence.")
    claims: List[ClaimModel] = Field(
        default_factory=list,
        description="List of verifiable claims extracted from the answer.",
    )
    sources: List[SourceReference] = Field(
        default_factory=list,
        description="Normalized source document citations with evidence snippets.",
    )
    sources_used: List[str] = Field(
        default_factory=list,
        description="Raw list of source document labels referenced by generation.",
    )
    decision_path: str = Field(
        ...,
        description="Audit trail of supervisory and routing decisions (e.g. 'query_router -> rag -> rag').",
    )
    confidence: Optional[float] = Field(
        default=None,
        description="System-derived confidence estimate between 0.0 and 1.0 (uncalibrated heuristic).",
    )
    confidence_reason: Optional[str] = Field(
        default=None,
        description="Explanation of the confidence score assignment.",
    )
    intent: str = Field(..., description="Classified query intent ('factual', 'analytical', 'opinion', etc.).")
    refusal_reason: Optional[str] = Field(
        default=None,
        description="Explicit reason if the query was refused by policy or lack of evidence.",
    )
    is_refusal: bool = Field(
        ...,
        description="True if the query resulted in a hard refusal or lack-of-evidence response.",
    )
    unverified: bool = Field(
        default=False,
        description="True if the response contains claims that could not be fully verified.",
    )
    trace_id: str = Field(..., description="Unique UUID for end-to-end audit tracing.")
    question: str = Field(..., description="The query that produced this result.")


class DocumentMetadata(BaseModel):
    """Safe document metadata descriptor (no proprietary content or filesystem paths)."""

    document_id: str
    title: Optional[str] = None
    author: Optional[str] = None
    vendor: Optional[str] = None
    document_type: Optional[str] = None
    jurisdiction: Optional[str] = None
    version: Optional[str] = None
    url: Optional[str] = None
    chunks_count: int = 1


class DocumentListResponse(BaseModel):
    """Catalog of documents currently indexed in the compliance vector store."""

    total_documents: int
    total_chunks: int
    collection_name: str
    documents: List[DocumentMetadata]


class HealthLiveResponse(BaseModel):
    """Liveness probe status."""

    status: str = "live"
    service: str = "enterprise-compliance-intelligence"
    uptime_seconds: float


class DependencyStatus(BaseModel):
    """Individual dependency health check status."""

    status: str = Field(..., description="'ok', 'degraded', or 'error'")
    details: Optional[str] = None


class HealthReadyResponse(BaseModel):
    """Readiness probe status."""

    status: str = Field(..., description="'ready', 'degraded', or 'not_ready'")
    service: str = "enterprise-compliance-intelligence"
    dependencies: Dict[str, DependencyStatus]
    read_only_mode: bool
