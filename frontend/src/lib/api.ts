/**
 * Typed API client for the Candidate Communication Platform.
 * All requests go to the Django backend at NEXT_PUBLIC_API_URL.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://127.0.0.1:8000/api/v1';

export interface Candidate {
  candidate_id: string;
  name: string;
  phone: string;
  email: string;
  last_message: string;   // 'DD-MM-YYYY' or 'NA'
  status: string;         // human label or 'NA'
  status_raw: string;     // raw status key or 'NA'
  latest_message_text: string;
  created_at: string;
}

export interface CandidatesResponse {
  count: number;
  page: number;
  page_size: number;
  total_pages: number;
  results: Candidate[];
}

export interface ApiError {
  error: {
    code: string;
    message: string;
    fields?: Record<string, string>;
  };
}

export interface MessageRecipient {
  id: string;
  candidate_id: string;
  candidate_name: string;
  status: string;
  status_raw: string;
  provider_message_id: string | null;
  error_code: string | null;
  friendly_message: string | null;
  retryable: boolean;
  attempt_count: number;
  message_body: string;
  sent_at: string | null;
  delivered_at: string | null;
  read_at: string | null;
  failed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface MessageHistoryItem {
  recipient_id: string;
  message_id: string;
  message_body: string;
  status: string;
  status_raw: string;
  error_code: string | null;
  friendly_message: string | null;
  retryable: boolean;
  attempt_count: number;
  created_at: string;
  updated_at: string;
}

export interface BulkSendResult {
  candidate_id: string;
  candidate_name: string;
  status: 'sent' | 'failed';
  error?: string;
  recipient_id?: string;
}

export interface BulkSendResponse {
  total: number;
  succeeded: number;
  failed: number;
  results: BulkSendResult[];
}

export interface ProviderHealth {
  status: 'operational' | 'degraded' | 'down';
  provider_reachable: boolean;
  sent: number;
  delivered: number;
  failed: number;
  success_rate: number | null;
  recent_failure_rate: number;
}

export async function fetchProviderHealth(): Promise<ProviderHealth> {
  const res = await fetch(`${API_BASE}/health/provider`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Provider health unavailable');
  return res.json();
}

// ─── Candidates ──────────────────────────────────────────────────────────────

export async function fetchCandidates(params: {
  search?: string;
  page?: number;
  page_size?: number;
  ordering?: string;
}): Promise<CandidatesResponse> {
  const qs = new URLSearchParams();
  if (params.search) qs.set('search', params.search);
  if (params.page) qs.set('page', String(params.page));
  if (params.page_size) qs.set('page_size', String(params.page_size));
  if (params.ordering) qs.set('ordering', params.ordering);

  const res = await fetch(`${API_BASE}/candidates?${qs}`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to load candidates');
  return res.json();
}

export async function createCandidate(data: {
  name: string;
  phone: string;
  email: string;
}): Promise<{ data?: Candidate; error?: ApiError }> {
  const res = await fetch(`${API_BASE}/candidates`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  const json = await res.json();
  if (!res.ok) return { error: json };
  return { data: json };
}

export async function deleteCandidate(candidateId: string): Promise<void> {
  await fetch(`${API_BASE}/candidates/${candidateId}`, { method: 'DELETE' });
}

export async function bulkDeleteCandidates(candidateIds: string[]): Promise<void> {
  const res = await fetch(`${API_BASE}/candidates/bulk-delete`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ candidate_ids: candidateIds }),
  });
  if (!res.ok) throw new Error('Failed to delete candidates');
}

// ─── Messages ────────────────────────────────────────────────────────────────

export async function sendMessage(data: {
  candidate_ids: string[];
  body: string;
}): Promise<{ data?: BulkSendResponse; error?: ApiError }> {
  const res = await fetch(`${API_BASE}/messages/bulk`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  const json = await res.json();
  if (!res.ok) return { error: json };
  return { data: json };
}

export async function sendSingleMessage(data: {
  candidate_id: string;
  body: string;
}): Promise<{ data?: BulkSendResult; error?: ApiError }> {
  const res = await fetch(`${API_BASE}/messages`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  const json = await res.json();
  if (!res.ok) return { error: json };
  return { data: json };
}

export async function fetchCandidateHistory(candidateId: string): Promise<MessageHistoryItem[]> {
  const res = await fetch(`${API_BASE}/candidates/${candidateId}/messages`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to load communication history');
  const json = await res.json();
  return json.results ?? json;
}

export async function retryMessage(recipientId: string): Promise<{ data?: MessageRecipient; error?: ApiError }> {
  const res = await fetch(`${API_BASE}/messages/${recipientId}/retry`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });
  const json = await res.json();
  if (!res.ok) return { error: json };
  return { data: json };
}
