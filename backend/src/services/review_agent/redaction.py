"""Local privacy gate for review documents before they leave the device."""

import re

from src.services.review_agent.contracts import ReviewDocument

_SENSITIVE_PATTERNS = {
    "phone": re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"),
    "id_card": re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)"),
    "labeled_identity": re.compile(
        r"(?:\u59d3\u540d|\u4f4f\u9662\u53f7|\u75c5\u6848\u53f7|\u8eab\u4efd\u8bc1\u53f7|"
        r"\u8054\u7cfb\u7535\u8bdd|\u624b\u673a\u53f7)\s*[:\uff1a]\s*(?!\[)[^\s,\uff0c;\uff1b]{2,}"
    ),
}


class RedactionViolationError(ValueError):
    """Raised when raw identity information remains in submitted content."""


def find_sensitive_values(content: str) -> list[str]:
    return [
        category for category, pattern in _SENSITIVE_PATTERNS.items() if pattern.search(content)
    ]


def ensure_documents_are_redacted(documents: list[ReviewDocument]) -> None:
    findings = {
        document.id: document_findings
        for document in documents
        if (document_findings := find_sensitive_values(document.content))
    }
    if findings:
        raise RedactionViolationError(f"sensitive values remain after redaction: {findings}")
