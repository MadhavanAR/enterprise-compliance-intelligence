"""
FastAPI application for Enterprise Compliance Intelligence.

Exposes production-ready compliance RAG endpoints:
- GET  /health/live
- GET  /health/ready
- POST /api/v1/query
- GET  /api/v1/documents
- POST /api/v1/documents/ingest (Admin only)
"""

from __future__ import annotations

import os
import sys
import tempfile
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from fastapi import (
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Ensure root workspace is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api.models import (
    ClaimModel,
    DependencyStatus,
    DocumentListResponse,
    DocumentMetadata,
    HealthLiveResponse,
    HealthReadyResponse,
    QueryRequest,
    QueryResponse,
    SourceReference,
)
from api.security import check_rate_limit, verify_admin_key
from rag.config import (
    COLLECTION_NAME,
    OLLAMA_HEADERS,
    OLLAMA_MODEL,
    OLLAMA_URL,
    READ_ONLY_MODE,
)
from rag.engine import run_enterprise_query
from rag.logger import get_logger
from rag.qdrant import get_qdrant_client

_START_TIME = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    root_logger = get_logger("system-startup")
    root_logger.info(
        "Enterprise Compliance Intelligence API starting up",
        read_only_mode=READ_ONLY_MODE,
        collection=COLLECTION_NAME,
        ollama_model=OLLAMA_MODEL,
    )
    yield
    root_logger.info("Enterprise Compliance Intelligence API shutting down")


app = FastAPI(
    title="Enterprise Compliance Intelligence API",
    description="FAANG-grade audit-ready RAG API for regulatory compliance evaluation.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration
raw_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000",
)
allowed_origins = [o.strip() for o in raw_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if allowed_origins else ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


# Global Exception Handler to prevent secret and stack-trace leakage
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    trace_id = str(uuid.uuid4())
    logger = get_logger(trace_id)
    logger.error("Unhandled API exception", error_type=type(exc).__name__, error=str(exc))
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred while processing the compliance query.",
            "trace_id": trace_id,
        },
    )


@app.get("/health/live", response_model=HealthLiveResponse, tags=["Health"])
def health_live():
    """
    Liveness probe: returns 200 if the API process is alive and responsive.
    Does not expose sensitive credentials or configuration.
    """
    return HealthLiveResponse(
        status="live",
        service="enterprise-compliance-intelligence",
        uptime_seconds=round(time.time() - _START_TIME, 2),
    )


@app.get("/health/ready", response_model=HealthReadyResponse, tags=["Health"])
def health_ready():
    """
    Readiness probe: validates availability of vector database, LLM inference, and embeddings.
    Distinguishes a live process from a fully ready query-answering service.
    """
    dependencies: Dict[str, DependencyStatus] = {}
    is_ready = True

    # 1. Check Qdrant
    try:
        q_client = get_qdrant_client()
        collections_info = q_client.get_collections()
        col_names = [c.name for c in collections_info.collections]
        has_collection = COLLECTION_NAME in col_names
        dependencies["qdrant"] = DependencyStatus(
            status="ok" if has_collection else "degraded",
            details=f"Collection '{COLLECTION_NAME}' {'present' if has_collection else 'missing'}",
        )
        if not has_collection:
            is_ready = False
    except Exception as e:
        is_ready = False
        dependencies["qdrant"] = DependencyStatus(
            status="error",
            details=f"Connection failure: {type(e).__name__}",
        )

    # 2. Check Ollama LLM endpoint
    try:
        check_url = OLLAMA_URL
        if check_url.endswith("/api/generate"):
            check_url = check_url.replace("/api/generate", "/api/tags")
        resp = requests.get(check_url, headers=OLLAMA_HEADERS, timeout=3)
        if resp.status_code == 200:
            dependencies["ollama"] = DependencyStatus(
                status="ok",
                details=f"Connected (Model: {OLLAMA_MODEL})",
            )
        else:
            is_ready = False
            dependencies["ollama"] = DependencyStatus(
                status="degraded",
                details=f"HTTP status {resp.status_code}",
            )
    except Exception as e:
        is_ready = False
        dependencies["ollama"] = DependencyStatus(
            status="error",
            details=f"Inference endpoint unreachable: {type(e).__name__}",
        )

    # 3. Check Embeddings
    try:
        from rag.embeddings import get_embedding_model
        _ = get_embedding_model()
        dependencies["embeddings"] = DependencyStatus(
            status="ok",
            details="SentenceTransformers loaded",
        )
    except Exception as e:
        is_ready = False
        dependencies["embeddings"] = DependencyStatus(
            status="error",
            details=f"Embedding model error: {type(e).__name__}",
        )

    overall_status = "ready" if is_ready else "degraded"
    return HealthReadyResponse(
        status=overall_status,
        service="enterprise-compliance-intelligence",
        dependencies=dependencies,
        read_only_mode=READ_ONLY_MODE,
    )


@app.post(
    "/api/v1/query",
    response_model=QueryResponse,
    dependencies=[Depends(check_rate_limit)],
    tags=["Query"],
)
def run_query(request: QueryRequest):
    """
    Canonical Compliance Query Endpoint.

    Executes query through the canonical RAG engine:
    - Analyzes intent and enforces policy guardrails.
    - Performs hybrid dense/BM25 retrieval.
    - Enforces fail-closed grounded claim generation.
    - Computes uncalibrated risk and confidence estimates.
    - Returns structured claims, source citations, decision paths, and trace ID.
    """
    req_trace_id = str(uuid.uuid4())
    logger = get_logger(req_trace_id)
    logger.info("API received compliance query", question=request.question[:80])

    try:
        raw_result = run_enterprise_query(
            question=request.question,
            metadata_filters=request.metadata_filters,
            trace_id=req_trace_id,
        )
    except Exception as e:
        logger.error("Canonical engine execution raised an unhandled error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "engine_failure",
                "message": "Engine failed to process the compliance query.",
                "trace_id": req_trace_id,
            },
        )

    # Detect upstream inference failures
    if raw_result.get("generation_error") == "llm_unavailable":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "llm_unavailable",
                "message": "The compliance inference engine is currently unreachable. Please verify Ollama or hosted model availability.",
                "trace_id": req_trace_id,
            },
        )

    answer = raw_result.get("answer", "")
    decision_path = raw_result.get("decision_path", "unknown")
    refusal_reason = raw_result.get("refusal_reason")
    raw_claims = raw_result.get("claims", []) or []
    raw_docs = raw_result.get("documents", []) or []
    sources_used = raw_result.get("sources_used", []) or []

    # Map raw claims into typed ClaimModel
    claims: List[ClaimModel] = []
    for c in raw_claims:
        if isinstance(c, dict):
            claims.append(
                ClaimModel(
                    text=c.get("text", ""),
                    source_doc=c.get("source_doc"),
                )
            )
        elif isinstance(c, str):
            claims.append(ClaimModel(text=c, source_doc=None))

    # Normalize source citations
    sources: List[SourceReference] = []
    for idx, doc in enumerate(raw_docs):
        doc_tag = f"Doc {idx + 1}"
        doc_payload = doc if isinstance(doc, dict) else {}
        text_content = doc_payload.get("text", "")
        # Create a readable excerpt snippet
        snippet = text_content[:400] + ("..." if len(text_content) > 400 else "")
        sources.append(
            SourceReference(
                id=doc_tag,
                document_id=doc_payload.get("document_id") or f"doc_{idx+1}",
                title=doc_payload.get("title") or doc_payload.get("document_id") or f"Document {idx+1}",
                author=doc_payload.get("author"),
                vendor=doc_payload.get("vendor"),
                document_type=doc_payload.get("document_type"),
                jurisdiction=doc_payload.get("jurisdiction"),
                version=doc_payload.get("version"),
                url=doc_payload.get("url"),
                snippet=snippet,
                score=doc_payload.get("score"),
            )
        )

    # Strict refusal determination
    is_refusal = bool(
        refusal_reason
        or "refuse" in decision_path.lower()
        or (isinstance(answer, str) and "i don't know" in answer.lower())
    )

    return QueryResponse(
        answer=answer,
        claims=claims,
        sources=sources,
        sources_used=sources_used,
        decision_path=decision_path,
        confidence=raw_result.get("confidence"),
        confidence_reason=raw_result.get("confidence_reason"),
        intent=raw_result.get("intent", "unknown"),
        refusal_reason=refusal_reason,
        is_refusal=is_refusal,
        unverified=bool(raw_result.get("unverified", False)),
        trace_id=raw_result.get("trace_id") or req_trace_id,
        question=request.question,
    )


@app.get("/api/v1/documents", response_model=DocumentListResponse, tags=["Documents"])
def list_documents():
    """
    List safe metadata for documents currently indexed in the compliance vector store.
    Never exposes raw chunk text, file paths, or private configuration.
    """
    try:
        q_client = get_qdrant_client()
        points_batch, _ = q_client.scroll(
            collection_name=COLLECTION_NAME,
            limit=1000,
            with_payload=[
                "document_id",
                "title",
                "author",
                "vendor",
                "document_type",
                "jurisdiction",
                "version",
                "url",
            ],
            with_vectors=False,
        )
    except Exception as e:
        logger = get_logger("list-documents")
        logger.error("Failed to query Qdrant for documents", error=str(e))
        return DocumentListResponse(
            total_documents=0,
            total_chunks=0,
            collection_name=COLLECTION_NAME,
            documents=[],
        )

    # Group chunks by document_id
    doc_groups: Dict[str, DocumentMetadata] = {}
    for point in points_batch:
        payload = point.payload or {}
        doc_id = payload.get("document_id") or f"doc_{point.id}"
        if doc_id in doc_groups:
            doc_groups[doc_id].chunks_count += 1
        else:
            doc_groups[doc_id] = DocumentMetadata(
                document_id=doc_id,
                title=payload.get("title") or doc_id.replace("_", " ").title(),
                author=payload.get("author"),
                vendor=payload.get("vendor"),
                document_type=payload.get("document_type"),
                jurisdiction=payload.get("jurisdiction"),
                version=payload.get("version"),
                url=payload.get("url"),
                chunks_count=1,
            )

    doc_list = sorted(doc_groups.values(), key=lambda d: d.document_id)
    return DocumentListResponse(
        total_documents=len(doc_list),
        total_chunks=len(points_batch),
        collection_name=COLLECTION_NAME,
        documents=doc_list,
    )


@app.post(
    "/api/v1/documents/ingest",
    dependencies=[Depends(verify_admin_key)],
    tags=["Ingestion"],
)
async def ingest_documents(
    file: Optional[UploadFile] = File(None),
    author: Optional[str] = Form(None),
    vendor: Optional[str] = Form(None),
    document_id: Optional[str] = Form(None),
):
    """
    Administrative Document Ingestion Endpoint.

    Strict security controls:
    - Protected by X-Admin-Key header matching ADMIN_API_KEY.
    - Blocked when READ_ONLY_MODE=true.
    - Strict file size limit (500KB) and allowed formats (.txt, .md).
    - If no file provided, re-ingests canonical standard baseline documents.
    """
    if READ_ONLY_MODE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "read_only_mode",
                "message": "Corpus ingestion is disabled when READ_ONLY_MODE is active.",
            },
        )

    from rag.ingest import load_and_chunk
    from rag.store import store_chunks

    all_chunks = []

    if file is None:
        # Re-index standard sample repository documents
        data_dir = Path(__file__).resolve().parent.parent / "data"
        aws_doc = data_dir / "aws_compliance.txt"
        sample_doc = data_dir / "sample_doc.txt"

        if aws_doc.exists():
            all_chunks.extend(
                load_and_chunk(
                    file_path=str(aws_doc),
                    author="Amazon Web Services",
                    source="aws_compliance_programs",
                    document_id="aws_compliance",
                )
            )
        if sample_doc.exists():
            all_chunks.extend(
                load_and_chunk(
                    file_path=str(sample_doc),
                    author="Internal AI Platform Team",
                    source="rag_best_practices",
                    document_id="rag_best_practices",
                )
            )

        if not all_chunks:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "no_documents", "message": "No sample documents found in data directory."},
            )

        store_chunks(all_chunks)
        return {
            "status": "success",
            "message": f"Successfully ingested canonical baseline documents ({len(all_chunks)} chunks).",
            "chunks_ingested": len(all_chunks),
        }

    # Custom file upload handling with strict validation
    allowed_extensions = {".txt", ".md"}
    file_ext = Path(file.filename or "").suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "unsupported_file_type",
                "message": f"Unsupported file extension '{file_ext}'. Allowed: {sorted(allowed_extensions)}",
            },
        )

    content = await file.read()
    if len(content) > 500 * 1024:  # 500 KB limit
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={
                "error": "file_too_large",
                "message": "File exceeds maximum permitted size of 500KB.",
            },
        )

    with tempfile.NamedTemporaryFile("wb", suffix=file_ext, delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        doc_ident = document_id or Path(file.filename or "uploaded_doc").stem
        uploaded_chunks = load_and_chunk(
            file_path=tmp_path,
            author=author or "Compliance Administrator",
            source=doc_ident,
            document_id=doc_ident,
        )
        if vendor:
            for _, meta in uploaded_chunks:
                meta["vendor"] = vendor

        # Store with existing chunks or recreate
        store_chunks(uploaded_chunks)
        return {
            "status": "success",
            "document_id": doc_ident,
            "chunks_ingested": len(uploaded_chunks),
        }
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
