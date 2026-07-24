import { ContinuationPayload, ReviewSnapshot } from '../model/ReviewModels';

export class ContinuationState {
  static serialize(review: ReviewSnapshot): string {
    const payload: ContinuationPayload = {
      reviewId: review.id,
      version: review.version,
      status: review.status,
      createdAt: review.created_at
    };
    return JSON.stringify(payload);
  }

  static parse(serialized: string): ContinuationPayload | undefined {
    try {
      const value = JSON.parse(serialized) as ContinuationPayload;
      if (!value.reviewId || value.version < 1 || !value.status) {
        return undefined;
      }
      return value;
    } catch (_) {
      return undefined;
    }
  }
}
