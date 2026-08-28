"""Auditable orchestration for the discharge coding review Agent."""

from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
from hashlib import sha256
from uuid import uuid4

from .contracts import (
    CreateReviewRequest,
    RedactionReceipt,
    ReviewDecisionRequest,
    ReviewDocument,
    ReviewEventOut,
    ReviewSnapshot,
)
from .redaction import RedactionViolationError, ensure_documents_are_redacted
from .report import build_review_report
from .repository import (
    ReviewNotFoundError,
    ReviewStore,
    ReviewVersionConflictError,
    StoredEvent,
    StoredReview,
)
from .tools import ReviewTools


class ReviewInvalidStateError(ValueError):
    """Raised when an operator action does not fit the current workflow state."""


class ReviewAccessDeniedError(PermissionError):
    """Raised when an operator tries to access another operator's review task."""


class ReviewAgent:
    """Coordinates observable review steps without exposing model reasoning."""

    def __init__(self, store: ReviewStore, tools: ReviewTools | None = None):
        self.store = store
        self.tools = tools or ReviewTools()

    async def create(self, request: CreateReviewRequest, operator: dict) -> ReviewSnapshot:
        ensure_documents_are_redacted(request.documents)
        documents = [document.model_dump() for document in request.documents]
        operator_name = str(operator.get("username", "anonymous"))
        review = StoredReview(
            id=str(uuid4()),
            status="created",
            mode="pending",
            preferred_mode=request.preferred_mode,
            version=1,
            documents=documents,
            patient_context=request.patient_context,
            redaction_receipt=request.redaction_receipt.model_dump(),
            analysis={},
            pending_actions=[],
            operator_hash=sha256(operator_name.encode("utf-8")).hexdigest(),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        created = await self.store.create(
            review,
            event_type="review_created",
            phase="privacy",
            payload={
                "document_count": len(documents),
                "redaction_receipt": request.redaction_receipt.model_dump(),
            },
        )
        return self._snapshot(created)

    async def get(self, review_id: str, operator: dict) -> ReviewSnapshot:
        review = await self.store.get(review_id)
        self._assert_operator(review, operator)
        return self._snapshot(review)

    async def advance(
        self, review_id: str, expected_version: int, operator: dict
    ) -> ReviewSnapshot:
        review = await self.store.get(review_id)
        self._assert_operator(review, operator)
        self._assert_version(review, expected_version)
        analysis = deepcopy(review.analysis)

        if review.status == "created":
            analysis["extraction"] = await self.tools.extract(self._documents(review))
            return await self._transition(
                review,
                status="extracted",
                analysis=analysis,
                event_type="documents_extracted",
                phase="extraction",
                payload={"document_count": len(review.documents)},
            )

        if review.status in {"extracted", "recalculate"}:
            coding = await self.tools.code(analysis.get("extraction", {}), review.preferred_mode)
            analysis["coding"] = coding
            is_recalculation = review.status == "recalculate"
            return await self._transition(
                review,
                status="ready_for_confirmation" if is_recalculation else "coded",
                mode=str(coding.get("mode", "rule_based")),
                analysis=analysis,
                event_type="coding_recalculated" if is_recalculation else "coding_generated",
                phase="coding",
                payload={"mode": coding.get("mode", "rule_based")},
            )

        if review.status == "coded":
            quality = await self.tools.quality_check(
                self._documents(review), analysis.get("coding", {}), review.mode
            )
            analysis["quality"] = quality
            return await self._transition(
                review,
                status="checked",
                analysis=analysis,
                event_type="quality_checked",
                phase="quality",
                payload={"issue_count": len(quality.get("issues", []))},
            )

        if review.status == "checked":
            evidence = self.tools.evidence(self._documents(review))
            analysis["evidence"] = evidence
            pending_actions = [
                {
                    "id": conflict["id"],
                    "type": "source_confirmation",
                    "status": "open",
                    "summary": conflict["summary"],
                    "evidence": conflict["evidence"],
                }
                for conflict in evidence.get("conflicts", [])
            ]
            requires_confirmation = bool(pending_actions)
            return await self._transition(
                review,
                status="waiting_for_human" if requires_confirmation else "ready_for_confirmation",
                analysis=analysis,
                pending_actions=pending_actions,
                event_type="human_confirmation_required"
                if requires_confirmation
                else "evidence_verified",
                phase="evidence",
                payload={"conflict_count": len(pending_actions)},
            )

        raise ReviewInvalidStateError(f"review cannot advance from status '{review.status}'")

    async def decide(
        self, review_id: str, decision: ReviewDecisionRequest, operator: dict
    ) -> ReviewSnapshot:
        review = await self.store.get(review_id)
        self._assert_operator(review, operator)
        self._assert_version(review, decision.expected_version)
        if decision.action == "confirm_source":
            return await self._confirm_source(review, decision)
        if decision.action == "mark_pending":
            return await self._mark_pending(review, decision)
        return await self._complete_review(review, decision)

    async def events(
        self, review_id: str, operator: dict, after_sequence: int = 0
    ) -> list[ReviewEventOut]:
        review = await self.store.get(review_id)
        self._assert_operator(review, operator)
        events = await self.store.events(review_id, after_sequence)
        return [self._event(event) for event in events]

    async def report(self, review_id: str, operator: dict) -> dict:
        review = await self.store.get(review_id)
        self._assert_operator(review, operator)
        if review.status not in {"completed", "completed_with_pending"}:
            raise ReviewInvalidStateError("review must be completed before exporting a report")
        events = await self.store.events(review_id)
        return build_review_report(self._snapshot(review), [self._event(event) for event in events])

    async def _confirm_source(
        self, review: StoredReview, decision: ReviewDecisionRequest
    ) -> ReviewSnapshot:
        if review.status != "waiting_for_human":
            raise ReviewInvalidStateError("source confirmation is not expected at this stage")
        actions = deepcopy(review.pending_actions)
        action = self._find_action(actions, decision.issue_id or "")
        evidence_documents = {item["document_id"] for item in action.get("evidence", [])}
        if decision.selected_document_id not in evidence_documents:
            raise ReviewInvalidStateError("selected document is not evidence for this conflict")
        action["status"] = "resolved"
        action["selected_document_id"] = decision.selected_document_id
        action["note"] = decision.note
        return await self._transition(
            review,
            status="recalculate",
            analysis=self._append_decision(review.analysis, decision),
            pending_actions=actions,
            event_type="source_confirmed",
            phase="human_decision",
            payload={"issue_id": decision.issue_id, "document_id": decision.selected_document_id},
        )

    async def _mark_pending(
        self, review: StoredReview, decision: ReviewDecisionRequest
    ) -> ReviewSnapshot:
        if review.status not in {"waiting_for_human", "ready_for_confirmation"}:
            raise ReviewInvalidStateError("evidence cannot be deferred at this stage")
        actions = deepcopy(review.pending_actions)
        action = self._find_action(actions, decision.issue_id or "")
        action["status"] = "pending_evidence"
        action["note"] = decision.note
        return await self._transition(
            review,
            status="ready_for_confirmation",
            analysis=self._append_decision(review.analysis, decision),
            pending_actions=actions,
            event_type="evidence_marked_pending",
            phase="human_decision",
            payload={"issue_id": decision.issue_id},
        )

    async def _complete_review(
        self, review: StoredReview, decision: ReviewDecisionRequest
    ) -> ReviewSnapshot:
        if review.status != "ready_for_confirmation":
            raise ReviewInvalidStateError("review is not ready for final confirmation")
        has_pending = any(
            action.get("status") == "pending_evidence" for action in review.pending_actions
        )
        return await self._transition(
            review,
            status="completed_with_pending" if has_pending else "completed",
            analysis=self._append_decision(review.analysis, decision),
            event_type="review_completed",
            phase="completion",
            payload={"has_pending_evidence": has_pending},
        )

    async def _transition(self, review: StoredReview, **changes) -> ReviewSnapshot:
        event_type = changes.pop("event_type")
        phase = changes.pop("phase")
        payload = changes.pop("payload")
        updated = await self.store.transition(
            review.id,
            review.version,
            status=changes["status"],
            mode=changes.get("mode", review.mode),
            analysis=changes.get("analysis", review.analysis),
            pending_actions=changes.get("pending_actions", review.pending_actions),
            event_type=event_type,
            phase=phase,
            payload=payload,
        )
        return self._snapshot(updated)

    @staticmethod
    def _find_action(actions: list[dict], issue_id: str) -> dict:
        for action in actions:
            if action.get("id") == issue_id:
                return action
        raise ReviewInvalidStateError("review issue does not exist")

    @staticmethod
    def _append_decision(analysis: dict, decision: ReviewDecisionRequest) -> dict:
        updated = deepcopy(analysis)
        updated.setdefault("decisions", []).append(
            {
                "action": decision.action,
                "issue_id": decision.issue_id,
                "selected_document_id": decision.selected_document_id,
                "note": decision.note,
            }
        )
        return updated

    @staticmethod
    def _assert_version(review: StoredReview, expected_version: int) -> None:
        if review.version != expected_version:
            raise ReviewVersionConflictError("review state has changed; refresh before continuing")

    @staticmethod
    def _assert_operator(review: StoredReview, operator: dict) -> None:
        operator_name = str(operator.get("username", "anonymous"))
        operator_hash = sha256(operator_name.encode("utf-8")).hexdigest()
        if review.operator_hash != operator_hash:
            raise ReviewAccessDeniedError("review task is owned by another operator")

    @staticmethod
    def _snapshot(review: StoredReview) -> ReviewSnapshot:
        return ReviewSnapshot(
            id=review.id,
            status=review.status,
            mode=review.mode,
            version=review.version,
            documents=[ReviewDocument.model_validate(item) for item in review.documents],
            redaction_receipt=RedactionReceipt.model_validate(review.redaction_receipt),
            analysis=review.analysis,
            pending_actions=review.pending_actions,
            created_at=review.created_at.isoformat(),
            updated_at=review.updated_at.isoformat(),
        )

    @staticmethod
    def _documents(review: StoredReview) -> list[ReviewDocument]:
        return [ReviewDocument.model_validate(item) for item in review.documents]

    @staticmethod
    def _event(event: StoredEvent) -> ReviewEventOut:
        return ReviewEventOut(
            sequence=event.sequence,
            event_type=event.event_type,
            phase=event.phase,
            payload=event.payload,
            created_at=event.created_at.isoformat(),
        )


__all__ = [
    "RedactionViolationError",
    "ReviewAccessDeniedError",
    "ReviewAgent",
    "ReviewInvalidStateError",
    "ReviewNotFoundError",
    "ReviewVersionConflictError",
]
