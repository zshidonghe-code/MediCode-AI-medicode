"""Creates the compact audit package exported after human confirmation."""

from .contracts import ReviewEventOut, ReviewSnapshot


def build_review_report(review: ReviewSnapshot, events: list[ReviewEventOut]) -> dict:
    return {
        "review_id": review.id,
        "status": review.status,
        "mode": review.mode,
        "coding": review.analysis.get("coding", {}),
        "quality": review.analysis.get("quality", {}),
        "evidence": review.analysis.get("evidence", {}),
        "decisions": review.analysis.get("decisions", []),
        "unresolved_actions": [
            action for action in review.pending_actions if action.get("status") != "resolved"
        ],
        "redaction_receipt": review.redaction_receipt.model_dump(),
        "timeline": [event.model_dump() for event in events],
        "created_at": review.created_at,
        "completed_at": review.updated_at,
    }
