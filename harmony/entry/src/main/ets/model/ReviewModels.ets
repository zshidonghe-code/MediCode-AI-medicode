export type RecordType = 'admission' | 'course' | 'surgery' | 'discharge' | 'consultation' | 'exam' | 'lab';

export interface ReviewDocument {
  id: string;
  title: string;
  record_type: RecordType;
  content: string;
  recorded_at?: string;
}

export interface RedactionReceipt {
  redacted_count: number;
  categories: string[];
  content_hash: string;
}

export interface ReviewSnapshot {
  id: string;
  status: string;
  mode: string;
  version: number;
  documents: ReviewDocument[];
  redaction_receipt: RedactionReceipt;
  analysis: Record<string, Object>;
  pending_actions: Array<Record<string, Object>>;
  created_at: string;
  updated_at: string;
}

export interface ReviewEvent {
  sequence: number;
  event_type: string;
  phase: string;
  payload: Record<string, Object>;
  created_at: string;
}

export interface ContinuationPayload {
  reviewId: string;
  version: number;
  status: string;
  createdAt: string;
}
