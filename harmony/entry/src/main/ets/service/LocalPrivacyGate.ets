import { RedactionReceipt, ReviewDocument } from '../model/ReviewModels';

interface PrivacyRedactionResult {
  documents: ReviewDocument[];
  receipt: RedactionReceipt;
}

const PHONE_PATTERN = /(?<!\d)1[3-9]\d{9}(?!\d)/g;
const ID_PATTERN = /(?<!\d)\d{17}[\dXx](?!\d)/g;
const LABEL_PATTERN = /(?:\u59d3\u540d|\u4f4f\u9662\u53f7|\u75c5\u6848\u53f7|\u8eab\u4efd\u8bc1\u53f7|\u8054\u7cfb\u7535\u8bdd|\u624b\u673a\u53f7)\s*[:\uff1a]\s*[^\s,\uff0c;\uff1b]{2,}/g;

export class LocalPrivacyGate {
  redact(documents: ReviewDocument[]): PrivacyRedactionResult {
    let count = 0;
    const categories: string[] = [];
    const redacted: ReviewDocument[] = documents.map((document: ReviewDocument) => {
      let content = document.content;
      content = this.replace(content, PHONE_PATTERN, '[PHONE]', 'phone', categories, () => count++);
      content = this.replace(content, ID_PATTERN, '[ID_CARD]', 'id_card', categories, () => count++);
      content = this.replace(content, LABEL_PATTERN, '[IDENTITY_REDACTED]', 'labeled_identity', categories, () => count++);
      const redactedDocument: ReviewDocument = {
        id: document.id,
        title: document.title,
        record_type: document.record_type,
        content: content,
        recorded_at: document.recorded_at
      };
      return redactedDocument;
    });
    return {
      documents: redacted,
      receipt: { redacted_count: count, categories: categories, content_hash: this.hash(redacted) }
    };
  }

  private replace(content: string, pattern: RegExp, value: string, category: string, categories: string[], onReplace: () => void): string {
    pattern.lastIndex = 0;
    return content.replace(pattern, () => {
      if (!categories.includes(category)) {
        categories.push(category);
      }
      onReplace();
      return value;
    });
  }

  private hash(documents: ReviewDocument[]): string {
    let value = 2166136261;
    for (const document of documents) {
      const source = document.id + document.content;
      for (let index = 0; index < source.length; index++) {
        value ^= source.charCodeAt(index);
        value = Math.imul(value, 16777619);
      }
    }
    return (value >>> 0).toString(16).padStart(16, '0');
  }
}
