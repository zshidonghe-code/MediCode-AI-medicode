import http from '@ohos.net.http';
import { RedactionReceipt, ReviewDocument, ReviewEvent, ReviewSnapshot } from '../model/ReviewModels';

export class ReviewGateway {
  constructor(private baseUrl: string, private token: string) {}

  async create(documents: ReviewDocument[], receipt: RedactionReceipt): Promise<ReviewSnapshot> {
    return this.request<ReviewSnapshot>('/api/v1/agent/reviews', http.RequestMethod.POST, {
      documents: documents,
      redaction_receipt: receipt,
      patient_context: {},
      preferred_mode: 'auto'
    });
  }

  async advance(review: ReviewSnapshot): Promise<ReviewSnapshot> {
    return this.request<ReviewSnapshot>(`/api/v1/agent/reviews/${review.id}/advance`, http.RequestMethod.POST, {
      expected_version: review.version
    });
  }

  async confirmSource(review: ReviewSnapshot, issueId: string, documentId: string, note: string): Promise<ReviewSnapshot> {
    return this.request<ReviewSnapshot>(`/api/v1/agent/reviews/${review.id}/decisions`, http.RequestMethod.POST, {
      expected_version: review.version,
      action: 'confirm_source',
      issue_id: issueId,
      selected_document_id: documentId,
      note: note
    });
  }

  async markPending(review: ReviewSnapshot, issueId: string, note: string): Promise<ReviewSnapshot> {
    return this.request<ReviewSnapshot>(`/api/v1/agent/reviews/${review.id}/decisions`, http.RequestMethod.POST, {
      expected_version: review.version,
      action: 'mark_pending',
      issue_id: issueId,
      note: note
    });
  }

  async complete(review: ReviewSnapshot): Promise<ReviewSnapshot> {
    return this.request<ReviewSnapshot>(`/api/v1/agent/reviews/${review.id}/decisions`, http.RequestMethod.POST, {
      expected_version: review.version,
      action: 'confirm_review'
    });
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
        readTimeout: 20000
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
