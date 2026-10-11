'use client';

import React, { useState, useEffect, useCallback } from 'react';
import {
  QueryResponse,
  DocumentMetadata,
  HealthReadyResponse,
} from '@/types/compliance';
import {
  submitComplianceQuery,
  fetchDocuments,
  fetchHealth,
  ApiError,
} from '@/lib/api';

const EXAMPLE_QUESTIONS = [
  {
    tag: 'grounded',
    tagLabel: 'Grounded',
    question: 'Which compliance programs does AWS maintain to satisfy regulatory requirements?',
  },
  {
    tag: 'grounded',
    tagLabel: 'Grounded',
    question: 'How do customers access AWS compliance reports and independent audit certifications?',
  },
  {
    tag: 'grounded',
    tagLabel: 'Grounded',
    question: 'Explain BM25 keyword search in RAG systems',
  },
  {
    tag: 'refusal',
    tagLabel: 'Evidence Refusal',
    question: 'What is the AWS data retention period for deleted S3 objects?',
  },
  {
    tag: 'policy',
    tagLabel: 'Policy Refusal',
    question: 'What do you think about AI safety?',
  },
];

export default function ComplianceApp() {
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState(1);
  const [filterVendor, setFilterVendor] = useState(false);

  // Results
  const [result, setResult] = useState<QueryResponse | null>(null);
  const [errorState, setErrorState] = useState<{
    message: string;
    status?: number;
    details?: string;
  } | null>(null);

  // System status
  const [health, setHealth] = useState<HealthReadyResponse | null>(null);
  const [healthLoading, setHealthLoading] = useState(true);

  // Documents modal
  const [docsModalOpen, setDocsModalOpen] = useState(false);
  const [documents, setDocuments] = useState<DocumentMetadata[]>([]);
  const [docsLoading, setDocsLoading] = useState(false);

  // Audit panel toggle
  const [auditOpen, setAuditOpen] = useState(true);
  const [copiedTrace, setCopiedTrace] = useState(false);

  // Load health check on mount
  useEffect(() => {
    let ignore = false;
    fetchHealth()
      .then((data) => {
        if (!ignore) {
          setHealth(data);
          setHealthLoading(false);
        }
      })
      .catch(() => {
        if (!ignore) {
          setHealth(null);
          setHealthLoading(false);
        }
      });
    return () => {
      ignore = true;
    };
  }, []);

  const loadDocuments = async () => {
    setDocsLoading(true);
    setDocsModalOpen(true);
    try {
      const data = await fetchDocuments();
      setDocuments(data.documents);
    } catch (e) {
      console.error('Failed to load documents catalog', e);
    } finally {
      setDocsLoading(false);
    }
  };

  const handleSelectExample = (q: string) => {
    setQuestion(q);
  };

  // Submit query
  const handleQuery = useCallback(async () => {
    const trimmed = question.trim();
    if (!trimmed || loading) return;

    setLoading(true);
    setErrorState(null);
    setResult(null);
    setLoadingStep(1);

    // Simulated progress indicators for UX
    const t1 = setTimeout(() => setLoadingStep(2), 600);
    const t2 = setTimeout(() => setLoadingStep(3), 1600);
    const t3 = setTimeout(() => setLoadingStep(4), 2800);

    try {
      const filters = filterVendor ? { vendor: 'AWS' } : undefined;
      const res = await submitComplianceQuery(trimmed, filters);
      setResult(res);
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setErrorState({
          message: err.message,
          status: err.statusCode,
          details: JSON.stringify(err.errorPayload || {}),
        });
      } else if (err instanceof Error) {
        setErrorState({ message: err.message });
      } else {
        setErrorState({ message: 'An unknown connection failure occurred.' });
      }
    } finally {
      clearTimeout(t1);
      clearTimeout(t2);
      clearTimeout(t3);
      setLoading(false);
    }
  }, [question, loading, filterVendor]);

  const copyTraceId = (traceId: string) => {
    navigator.clipboard.writeText(traceId);
    setCopiedTrace(true);
    setTimeout(() => setCopiedTrace(false), 2000);
  };

  const isDegraded = health?.status === 'degraded';
  const isHealthy = health?.status === 'ready';

  return (
    <div className="app-container">
      {/* Header */}
      <header className="app-header">
        <div className="brand">
          <div className="brand-icon">§</div>
          <div>
            <h1 className="brand-title">Enterprise Compliance Intelligence</h1>
            <div className="brand-subtitle">Auditable Regulatory RAG Architecture</div>
          </div>
        </div>

        <div className="header-actions">
          <button
            type="button"
            className="btn btn-secondary"
            onClick={loadDocuments}
            title="Inspect documents currently indexed in vector store"
          >
            <span>📚 Catalog</span>
          </button>

          <div
            className="status-pill"
            title={
              healthLoading
                ? 'Probing dependencies...'
                : health
                ? `Dependencies: Qdrant=${health.dependencies.qdrant?.status}, Ollama=${health.dependencies.ollama?.status}`
                : 'Backend unreachable on port 8000'
            }
          >
            <span
              className={`status-dot ${
                healthLoading ? 'degraded' : isHealthy ? 'ready' : isDegraded ? 'degraded' : 'error'
              }`}
            />
            <span>
              {healthLoading
                ? 'Probing'
                : isHealthy
                ? 'Live & Ready'
                : isDegraded
                ? 'Degraded'
                : 'Offline'}
            </span>
          </div>
        </div>
      </header>

      {/* Hero Explanation */}
      <section className="hero">
        <h2 className="hero-headline">Verifiable Evidence. Zero Hallucination.</h2>
        <p className="hero-desc">
          Evaluates compliance inquiries against ingested regulatory documentation. Every synthesized claim
          is mapped to verifiable citations. If evidence is missing or violates policy guardrails, the engine
          strictly refuses instead of fabricating answers.
        </p>
      </section>

      {/* Example Prompt Chips */}
      <section className="examples-bar">
        <div className="examples-label">Sample Compliance Inquiries:</div>
        <div className="chips-container">
          {EXAMPLE_QUESTIONS.map((ex, idx) => (
            <button
              key={idx}
              type="button"
              className="example-chip"
              onClick={() => handleSelectExample(ex.question)}
            >
              <span className={`chip-tag ${ex.tag}`}>{ex.tagLabel}</span>
              <span>{ex.question}</span>
            </button>
          ))}
        </div>
      </section>

      {/* Query Input Card */}
      <section className="query-card">
        <textarea
          className="query-textarea"
          placeholder="Ask a compliance or audit question against indexed evidence (e.g., Which compliance programs does AWS maintain?)"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
              e.preventDefault();
              handleQuery();
            }
          }}
          disabled={loading}
          rows={3}
        />

        <div className="query-controls">
          <div className="query-hints">
            <span>{question.length}/2000 chars</span>
            <span>•</span>
            <label style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={filterVendor}
                onChange={(e) => setFilterVendor(e.target.checked)}
              />
              <span className="filter-badge">Filter: Vendor = AWS</span>
            </label>
            <span>•</span>
            <span style={{ opacity: 0.7 }}>Cmd+Enter to submit</span>
          </div>

          <div style={{ display: 'flex', gap: '0.5rem' }}>
            {question && (
              <button
                type="button"
                className="btn btn-ghost"
                onClick={() => setQuestion('')}
                disabled={loading}
              >
                Clear
              </button>
            )}
            <button
              type="button"
              className="btn btn-primary"
              onClick={handleQuery}
              disabled={loading || question.trim().length < 3}
            >
              {loading ? 'Evaluating...' : 'Audit Query →'}
            </button>
          </div>
        </div>
      </section>

      {/* Loading Progress State */}
      {loading && (
        <section className="loading-card">
          <div className="spinner" />
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '0.5rem' }}>
            Executing Compliance Pipeline
          </h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
            Enforcing multi-agent router, policy gates, and hybrid dense/sparse retrieval...
          </p>
          <div className="loading-steps">
            <div className={`step-item ${loadingStep >= 1 ? 'active' : ''}`}>
              <span>{loadingStep > 1 ? '✓' : '1.'}</span> Router & Policy
            </div>
            <div className={`step-item ${loadingStep >= 2 ? 'active' : ''}`}>
              <span>{loadingStep > 2 ? '✓' : '2.'}</span> Hybrid Retrieval
            </div>
            <div className={`step-item ${loadingStep >= 3 ? 'active' : ''}`}>
              <span>{loadingStep > 3 ? '✓' : '3.'}</span> Grounded Synthesis
            </div>
            <div className={`step-item ${loadingStep >= 4 ? 'active' : ''}`}>
              <span>{loadingStep > 4 ? '✓' : '4.'}</span> Confidence Scoring
            </div>
          </div>
        </section>
      )}

      {/* Error State: Service Outage / Infrastructure Failure */}
      {errorState && (
        <section className="outcome-banner error">
          <div className="banner-icon">⚠️</div>
          <div style={{ flex: 1 }}>
            <div className="banner-title">
              Service Unavailable {errorState.status ? `(HTTP ${errorState.status})` : ''}
            </div>
            <div className="banner-desc">{errorState.message}</div>
            <div style={{ marginTop: '0.75rem', fontSize: '0.8rem', opacity: 0.85 }}>
              Troubleshooting advice: Verify that the FastAPI backend is running on port 8000 and that Ollama or your hosted inference provider is reachable.
            </div>
            <div style={{ marginTop: '0.75rem' }}>
              <button
                type="button"
                className="btn btn-secondary"
                style={{ padding: '0.35rem 0.75rem', fontSize: '0.8rem' }}
                onClick={handleQuery}
              >
                Retry Request
              </button>
            </div>
          </div>
        </section>
      )}

      {/* Results Presentation */}
      {result && (
        <div className="result-container">
          {/* Outcome Distinction Banner */}
          {result.is_refusal ? (
            <section className="outcome-banner refusal">
              <div className="banner-icon">🛑</div>
              <div>
                <div className="banner-title">Compliance Inquiry Refused (Fail-Closed Guardrail)</div>
                <div className="banner-desc">
                  {result.refusal_reason ||
                    'The system refused this query because it is either speculative, violates policy, or lacks sufficient supporting evidence in the indexed compliance documents.'}
                </div>
              </div>
            </section>
          ) : (
            <section className="outcome-banner grounded">
              <div className="banner-icon">🛡️</div>
              <div>
                <div className="banner-title">Grounded Compliance Evaluation</div>
                <div className="banner-desc">
                  This answer is strictly derived from retrieved evidence. All asserted claims are
                  cross-referenced with the citations listed below.
                </div>
              </div>
            </section>
          )}

          {/* Structured Answer Card */}
          <article className="answer-card">
            <div className="answer-header">
              <div className="answer-badge-group">
                <span className={`badge ${result.is_refusal ? 'refusal' : 'grounded'}`}>
                  {result.is_refusal ? 'Refusal / No Evidence' : 'Evidence-Grounded'}
                </span>
                <span className="badge neutral">Intent: {result.intent}</span>
                {result.confidence !== null && result.confidence !== undefined && (
                  <span className="badge neutral">
                    Confidence: {(result.confidence * 100).toFixed(0)}%
                  </span>
                )}
              </div>
            </div>

            <div className="answer-body">{result.answer}</div>

            {/* Verifiable Claims */}
            {result.claims && result.claims.length > 0 && (
              <section className="claims-section">
                <div className="section-title">
                  <span>✓</span> Verifiable Grounded Claims ({result.claims.length})
                </div>
                <div>
                  {result.claims.map((claim, idx) => (
                    <div key={idx} className="claim-card">
                      <span className="claim-icon">●</span>
                      <div className="claim-text">{claim.text}</div>
                      {claim.source_doc && (
                        <span className="claim-source-tag">{claim.source_doc}</span>
                      )}
                    </div>
                  ))}
                </div>
              </section>
            )}

            {/* Source Citations */}
            {result.sources && result.sources.length > 0 && (
              <section className="claims-section">
                <div className="section-title">
                  <span>📑</span> Retrieved Document Citations ({result.sources.length})
                </div>
                <div className="sources-grid">
                  {result.sources.map((src, idx) => (
                    <div key={idx} className="source-card">
                      <div className="source-card-header">
                        <span className="source-tag">{src.id}</span>
                        {src.vendor && <span className="source-meta-vendor">{src.vendor}</span>}
                      </div>
                      <div className="source-title">{src.title || src.document_id}</div>
                      <div className="source-snippet">&ldquo;{src.snippet}&rdquo;</div>
                      {src.url && (
                        <a
                          href={src.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="source-link"
                        >
                          View Official Document ↗
                        </a>
                      )}
                    </div>
                  ))}
                </div>
              </section>
            )}
          </article>

          {/* Expandable Audit Panel */}
          <section className="audit-panel">
            <div
              className="audit-toggle"
              onClick={() => setAuditOpen(!auditOpen)}
              role="button"
              tabIndex={0}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                <span style={{ fontSize: '1.1rem' }}>🔍</span>
                <span style={{ fontWeight: 700, fontSize: '0.95rem' }}>Audit Trail & Execution Telemetry</span>
              </div>
              <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                {auditOpen ? 'Collapse ▲' : 'Expand ▼'}
              </span>
            </div>

            {auditOpen && (
              <div className="audit-content">
                <div className="audit-metrics-grid">
                  <div className="metric-card">
                    <div className="metric-label">Decision Path</div>
                    <div className="metric-value" style={{ fontSize: '0.85rem' }}>
                      {result.decision_path}
                    </div>
                  </div>
                  <div className="metric-card">
                    <div className="metric-label">System Confidence</div>
                    <div className="metric-value">
                      {result.confidence !== null && result.confidence !== undefined
                        ? `${(result.confidence * 100).toFixed(0)}%`
                        : 'N/A'}
                    </div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                      Heuristic estimate (uncalibrated)
                    </div>
                  </div>
                  <div className="metric-card">
                    <div className="metric-label">Confidence Rationale</div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                      {result.confidence_reason || 'Standard policy match'}
                    </div>
                  </div>
                </div>

                <div className="trace-box">
                  <span>Trace ID: {result.trace_id}</span>
                  <button
                    type="button"
                    className="btn btn-ghost"
                    style={{ padding: '0.2rem 0.5rem', fontSize: '0.75rem' }}
                    onClick={() => copyTraceId(result.trace_id)}
                  >
                    {copiedTrace ? 'Copied!' : 'Copy Trace'}
                  </button>
                </div>
              </div>
            )}
          </section>
        </div>
      )}

      {/* Document Catalog Modal */}
      {docsModalOpen && (
        <div className="modal-overlay" onClick={() => setDocsModalOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">Indexed Compliance Knowledge Base</h3>
              <button
                type="button"
                className="btn btn-ghost"
                onClick={() => setDocsModalOpen(false)}
              >
                ✕
              </button>
            </div>

            {docsLoading ? (
              <div style={{ textAlign: 'center', padding: '2rem' }}>Loading documents...</div>
            ) : documents.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                No documents found in vector collection.
              </div>
            ) : (
              <table className="doc-table">
                <thead>
                  <tr>
                    <th>Document</th>
                    <th>Vendor</th>
                    <th>Type</th>
                    <th>Jurisdiction</th>
                    <th>Chunks</th>
                  </tr>
                </thead>
                <tbody>
                  {documents.map((doc, i) => (
                    <tr key={i}>
                      <td>
                        <div style={{ fontWeight: 600, color: '#f1f5f9' }}>
                          {doc.title || doc.document_id}
                        </div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                          ID: {doc.document_id}
                        </div>
                      </td>
                      <td>{doc.vendor || '—'}</td>
                      <td>{doc.document_type || 'compliance'}</td>
                      <td>{doc.jurisdiction || 'global'}</td>
                      <td>{doc.chunks_count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
