import http from '@ohos.net.http';
import { RedactionReceipt, ReviewDocument, ReviewEvent, ReviewSnapshot } from '../model/ReviewModels';

interface CreateReviewBody {
  documents: ReviewDocument[];
  redaction_receipt: RedactionReceipt;
  patient_context: Record<string, Object>;
  preferred_mode: string;
}

interface AdvanceBody {
  expected_version: number;
}

interface ConfirmSourceBody {
  expected_version: number;
  action: string;
  issue_id: string;
  selected_document_id: string;
  note: string;
}

interface PendingBody {
  expected_version: number;
  action: string;
  issue_id: string;
  note: string;
}

interface CompleteBody {
  expected_version: number;
  action: string;
}

export class ReviewGateway {
  private baseUrl: string;
  private token: string;

  constructor(baseUrl: string, token: string) {
    this.baseUrl = baseUrl.endsWith('/') ? baseUrl.slice(0, -1) : baseUrl;
    this.token = token;
  }

  async create(documents: ReviewDocument[], receipt: RedactionReceipt): Promise<ReviewSnapshot> {
    const patientContext: Record<string, Object> = {};
    const body: CreateReviewBody = {
      documents: documents,
      redaction_receipt: receipt,
      patient_context: patientContext,
      preferred_mode: 'auto'
    };
    return this.request<ReviewSnapshot>('/api/v1/agent/reviews', http.RequestMethod.POST, body);
  }

  async advance(review: ReviewSnapshot): Promise<ReviewSnapshot> {
    const body: AdvanceBody = {
      expected_version: review.version
    };
    return this.request<ReviewSnapshot>(`/api/v1/agent/reviews/${review.id}/advance`, http.RequestMethod.POST, body);
  }

  async get(reviewId: string): Promise<ReviewSnapshot> {
    return this.request<ReviewSnapshot>(`/api/v1/agent/reviews/${reviewId}`, http.RequestMethod.GET);
  }

  async confirmSource(review: ReviewSnapshot, issueId: string, documentId: string, note: string): Promise<ReviewSnapshot> {
    const body: ConfirmSourceBody = {
      expected_version: review.version,
      action: 'confirm_source',
      issue_id: issueId,
      selected_document_id: documentId,
      note: note
    };
    return this.request<ReviewSnapshot>(`/api/v1/agent/reviews/${review.id}/decisions`, http.RequestMethod.POST, body);
  }

  async markPending(review: ReviewSnapshot, issueId: string, note: string): Promise<ReviewSnapshot> {
    const body: PendingBody = {
      expected_version: review.version,
      action: 'mark_pending',
      issue_id: issueId,
      note: note
    };
    return this.request<ReviewSnapshot>(`/api/v1/agent/reviews/${review.id}/decisions`, http.RequestMethod.POST, body);
  }

  async complete(review: ReviewSnapshot): Promise<ReviewSnapshot> {
    const body: CompleteBody = {
      expected_version: review.version,
      action: 'confirm_review'
    };
    return this.request<ReviewSnapshot>(`/api/v1/agent/reviews/${review.id}/decisions`, http.RequestMethod.POST, body);
  }

  async events(review: ReviewSnapshot): Promise<ReviewEvent[]> {
    return this.request<ReviewEvent[]>(`/api/v1/agent/reviews/${review.id}/events`, http.RequestMethod.GET);
  }

  async report(review: ReviewSnapshot): Promise<Record<string, Object>> {
    return this.request<Record<string, Object>>(`/api/v1/agent/reviews/${review.id}/report`, http.RequestMethod.GET);
  }

  private async request<T>(path: string, method: http.RequestMethod, body?: Object): Promise<T> {
    const client = http.createHttp();
    try {
      const response = await client.request(`${this.baseUrl}${path}`, {
        method: method,
        header: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.token}`
        },
        extraData: body === undefined ? undefined : JSON.stringify(body),
        expectDataType: http.HttpDataType.STRING,
        connectTimeout: 8000,
        readTimeout: 130000
      });
      const text = response.result.toString();
      if (response.responseCode < 200 || response.responseCode >= 300) {
        throw new Error(`review request failed (${response.responseCode}): ${text}`);
      }
      return JSON.parse(text) as T;
    } finally {
      client.destroy();
    }
  }
}
