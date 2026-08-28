"""Evidence extraction deliberately limited to the competition demo risk: laterality."""

import re

from src.services.review_agent.contracts import ReviewDocument

_SIDE = r"(?:\u5de6|\u53f3)"
_TERM = r"(?:\u80a1\u9aa8\u9888\u9aa8\u6298|\u4eba\u5de5\u5168\u9acb\u5173\u8282\u7f6e\u6362\u672f|\u5168\u9acb\u5173\u8282\u7f6e\u6362\u672f|\u9acb\u5173\u8282\u7f6e\u6362\u672f|\u9acb\u5173\u8282)"
_TARGET_PATTERN = re.compile(
    rf"(?:(?P<side_before>{_SIDE})[^\u3002\uff0c\uff1b\n]{{0,12}}(?P<term_before>{_TERM})|"
    rf"(?P<term_after>{_TERM})[^\u3002\uff0c\uff1b\n]{{0,12}}(?P<side_after>{_SIDE}))"
)


def _snippet(content: str, start: int, end: int) -> str:
    return content[max(0, start - 24) : min(len(content), end + 24)]


def extract_laterality_evidence(documents: list[ReviewDocument]) -> list[dict]:
    evidence: list[dict] = []
    for document in documents:
        for match in _TARGET_PATTERN.finditer(document.content):
            side = match.group("side_before") or match.group("side_after")
            term = match.group("term_before") or match.group("term_after")
            evidence.append(
                {
                    "document_id": document.id,
                    "document_title": document.title,
                    "record_type": document.record_type,
                    "start": match.start(),
                    "end": match.end(),
                    "laterality": "left" if side == "\u5de6" else "right",
                    "term": term,
                    "anatomy": "hip",
                    "snippet": _snippet(document.content, match.start(), match.end()),
                }
            )
    return evidence


def find_laterality_conflicts(evidence: list[dict]) -> list[dict]:
    by_anatomy: dict[str, list[dict]] = {}
    for item in evidence:
        by_anatomy.setdefault(item["anatomy"], []).append(item)

    conflicts: list[dict] = []
    for anatomy, items in by_anatomy.items():
        sides = {item["laterality"] for item in items}
        document_ids = {item["document_id"] for item in items}
        if len(sides) < 2 or len(document_ids) < 2:
            continue
        conflicts.append(
            {
                "id": f"AGENT-CROSSDOC-LATERALITY-{anatomy}",
                "severity": "critical",
                "title": "Cross-document laterality conflict",
                "summary": "Conflicting laterality evidence requires human source confirmation.",
                "requires_human": True,
                "evidence": items,
                "status": "open",
            }
        )
    return conflicts
