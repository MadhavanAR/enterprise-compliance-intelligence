export interface ClaimModel {
  text: string;
  source_doc?: string | null;
}

export interface SourceReference {
  id: string;
  document_id: string;
  title?: string | null;
  author?: string | null;
  vendor?: string | null;
  document_type?: string | null;
  jurisdiction?: string | null;
  version?: string | null;
  url?: string | null;
  snippet: string;
  score?: number | null;
}

export interface QueryResponse {
  answer: string;
  claims: ClaimModel[];
  sources: SourceReference[];
  sources_used: string[];
  decision_path: string;
  confidence?: number | null;
  confidence_reason?: string | null;
  intent: string;
  refusal_reason?: string | null;
  is_refusal: boolean;
  unverified: boolean;
  trace_id: string;
  question: string;
}

export interface DocumentMetadata {
  document_id: string;
  title?: string | null;
  author?: string | null;
  vendor?: string | null;
  document_type?: string | null;
  jurisdiction?: string | null;
  version?: string | null;
  url?: string | null;
  chunks_count: number;
}

export interface DocumentListResponse {
  total_documents: number;
  total_chunks: number;
  collection_name: string;
  documents: DocumentMetadata[];
}

export interface DependencyStatus {
  status: 'ok' | 'degraded' | 'error';
  details?: string | null;
}

export interface HealthReadyResponse {
  status: 'ready' | 'degraded' | 'not_ready';
  service: string;
  dependencies: Record<string, DependencyStatus>;
  read_only_mode: boolean;
}
