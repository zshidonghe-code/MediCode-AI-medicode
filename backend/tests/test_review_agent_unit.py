from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timezone

import pytest

from src.services.review_agent.contracts import (
    CreateReviewRequest,
    RedactionReceipt,
    ReviewDecisionRequest,
    ReviewDocument,
)
from src.services.review_agent.orchestrator import ReviewAccessDeniedError, ReviewAgent
from src.services.review_agent.evidence import extract_laterality_evidence, find_laterality_conflicts
from src.services.review_agent.redaction import RedactionViolationError, ensure_documents_are_redacted
from src.services.review_agent.repository import (
    ReviewNotFoundError,
    ReviewVersionConflictError,
    StoredEvent,
    StoredReview,
)


class MemoryReviewStore:
    def __init__(self):
        self.reviews: dict[str, StoredReview] = {}
        self.review_events: dict[str, list[StoredEvent]] = {}

    async def create(self, review, event_type, phase, payload):
        self.reviews[review.id] = review
        self.review_events[review.id] = [
            StoredEvent(1, event_type, phase, payload, datetime.now(timezone.utc))
        ]
        return review

    async def get(self, review_id):
        if review_id not in self.reviews:
            raise ReviewNotFoundError(review_id)
        return self.reviews[review_id]

    async def transition(
        self,
        review_id,
        expected_version,
        *,
        status,
        mode,
        analysis,
        pending_actions,
        event_type,
        phase,
        payload,
    ):
        current = await self.get(review_id)
        if current.version != expected_version:
            raise ReviewVersionConflictError(review_id)
        updated = replace(
            current,
            status=status,
            mode=mode,
            analysis=deepcopy(analysis),
            pending_actions=deepcopy(pending_actions),
            version=current.version + 1,
            updated_at=datetime.now(timezone.utc),
        )
        self.reviews[review_id] = updated
        sequence = len(self.review_events[review_id]) + 1
        self.review_events[review_id].append(
            StoredEvent(sequence, event_type, phase, payload, updated.updated_at)
        )
        return updated

    async def events(self, review_id, after_sequence=0):
        await self.get(review_id)
        return [event for event in self.review_events[review_id] if event.sequence > after_sequence]


class DeterministicTools:
    async def extract(self, documents):
        return {
            "diagnoses": ["left femoral neck fracture"],
            "surgeries": ["right total hip replacement"],
            "summary": "synthetic demo record",
            "document_count": len(documents),
        }

    async def code(self, extracted, preferred_mode):
        return {
            "primary_diagnosis": {"code": "S72.000", "confidence": 0.91},
            "secondary_diagnoses": [],
            "procedures": [{"code": "81.5100", "confidence": 0.87}],
            "total_confidence": 0.91,
            "mode": "rule_based",
        }

    async def quality_check(self, documents, coding, mode):
        return {"issues": [], "total_issues": 0, "critical_count": 0}

    def evidence(self, documents):
        return {
            "items": [],
            "conflicts": [
                {
                    "id": "AGENT-CROSSDOC-LATERALITY-hip",
                    "summary": "Conflicting laterality evidence requires human source confirmation.",
                    "evidence": [
                        {"document_id": "admission", "laterality": "left"},
                        {"document_id": "surgery", "laterality": "right"},
                    ],
                }
            ],
        }


OPERATOR = {"username": "demo_coder"}


def request() -> CreateReviewRequest:
    return CreateReviewRequest(
        documents=[
            ReviewDocument(
                id="admission",
                title="admission note",
                record_type="admission",
                content="left femoral neck fracture after a fall.",
            ),
            ReviewDocument(
                id="surgery",
                title="surgery note",
                record_type="surgery",
                content="right total hip replacement was performed.",
            ),
        ],
        redaction_receipt=RedactionReceipt(
            redacted_count=2, categories=["name", "phone"], content_hash="a" * 64
        ),
    )


@pytest.mark.asyncio
async def test_conflict_requires_human_confirmation_then_recalculates():
    agent = ReviewAgent(MemoryReviewStore(), DeterministicTools())
    review = await agent.create(request(), OPERATOR)

    for expected_status in ("extracted", "coded", "checked", "waiting_for_human"):
        review = await agent.advance(review.id, review.version, OPERATOR)
        assert review.status == expected_status

    issue = review.pending_actions[0]
    review = await agent.decide(
        review.id,
        ReviewDecisionRequest(
            expected_version=review.version,
            action="confirm_source",
            issue_id=issue["id"],
            selected_document_id="admission",
            note="admission source confirmed by coder",
        ), OPERATOR,
    )
    assert review.status == "recalculate"
    assert review.pending_actions[0]["status"] == "resolved"

    review = await agent.advance(review.id, review.version, OPERATOR)
    assert review.status == "ready_for_confirmation"
    review = await agent.decide(
        review.id,
        ReviewDecisionRequest(expected_version=review.version, action="confirm_review"), OPERATOR,
    )
    assert review.status == "completed"

    report = await agent.report(review.id, OPERATOR)
    assert report["coding"]["primary_diagnosis"]["code"] == "S72.000"
    assert report["timeline"][-1]["event_type"] == "review_completed"


@pytest.mark.asyncio
async def test_pending_evidence_can_complete_with_a_visible_unresolved_action():
    agent = ReviewAgent(MemoryReviewStore(), DeterministicTools())
    review = await agent.create(request(), OPERATOR)

    for expected_status in ("extracted", "coded", "checked", "waiting_for_human"):
        review = await agent.advance(review.id, review.version, OPERATOR)
        assert review.status == expected_status

    issue = review.pending_actions[0]
    review = await agent.decide(
        review.id,
        ReviewDecisionRequest(
            expected_version=review.version,
            action="mark_pending",
            issue_id=issue["id"],
            note="source document is required before final coding confirmation",
        ),
        OPERATOR,
    )
    assert review.status == "ready_for_confirmation"
    assert review.pending_actions[0]["status"] == "pending_evidence"

    review = await agent.decide(
        review.id,
        ReviewDecisionRequest(expected_version=review.version, action="confirm_review"),
        OPERATOR,
    )
    assert review.status == "completed_with_pending"

    report = await agent.report(review.id, OPERATOR)
    assert report["unresolved_actions"][0]["status"] == "pending_evidence"


@pytest.mark.asyncio
async def test_stale_version_cannot_advance_a_review():
    agent = ReviewAgent(MemoryReviewStore(), DeterministicTools())
    review = await agent.create(request(), OPERATOR)
    await agent.advance(review.id, review.version, OPERATOR)

    with pytest.raises(ReviewVersionConflictError):
        await agent.advance(review.id, review.version, OPERATOR)


@pytest.mark.asyncio
async def test_other_operator_cannot_read_review_task():
    agent = ReviewAgent(MemoryReviewStore(), DeterministicTools())
    review = await agent.create(request(), OPERATOR)

    with pytest.raises(ReviewAccessDeniedError):
        await agent.get(review.id, {"username": "another_coder"})


def test_privacy_gate_rejects_raw_phone_number():
    document = ReviewDocument(
        id="discharge",
        title="discharge note",
        record_type="discharge",
        content="Please call 13812345678 after discharge.",
    )

    with pytest.raises(RedactionViolationError, match="phone"):
        ensure_documents_are_redacted([document])


def test_cross_document_laterality_conflict_uses_raw_evidence_locations():
    documents = [
        ReviewDocument(
            id="admission",
            title="admission note",
            record_type="admission",
            content="\u60a3\u8005\u644a\u5012\u540e\u5165\u9662\uff0c\u5de6\u4fa7\u80a1\u9aa8\u9888\u9aa8\u6298\u3002",
        ),
        ReviewDocument(
            id="surgery",
            title="surgery note",
            record_type="surgery",
            content="\u672f\u4e2d\u8bb0\u5f55\uff1a\u53f3\u4fa7\u5168\u9acb\u5173\u8282\u7f6e\u6362\u672f\u5df2\u5b8c\u6210\u3002",
        ),
    ]

    evidence = extract_laterality_evidence(documents)
    conflicts = find_laterality_conflicts(evidence)

    assert {item["laterality"] for item in evidence} == {"left", "right"}
    assert conflicts[0]["id"] == "AGENT-CROSSDOC-LATERALITY-hip"
