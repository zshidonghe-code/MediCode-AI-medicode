from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from sqlalchemy import func, select

from src.models.database import async_session
from src.models.review_agent import ReviewEvent, ReviewSession


class ReviewNotFoundError(LookupError):
    pass


class ReviewVersionConflictError(RuntimeError):
    pass


@dataclass
class StoredReview:
    id: str
    operator_hash: str
    status: str
    mode: str
    preferred_mode: str
    documents: list[dict]
    patient_context: dict
    redaction_receipt: dict
    analysis: dict
    pending_actions: list[dict]
    version: int
    created_at: datetime
    updated_at: datetime


@dataclass
class StoredEvent:
    sequence: int
    event_type: str
    phase: str
    payload: dict
    created_at: datetime


class ReviewStore(Protocol):
    async def create(self, review: StoredReview, event_type: str, phase: str, payload: dict) -> StoredReview: ...

    async def get(self, review_id: str) -> StoredReview: ...

    async def transition(
        self,
        review_id: str,
        expected_version: int,
        *,
        status: str,
        mode: str,
        analysis: dict,
        pending_actions: list[dict],
        event_type: str,
        phase: str,
        payload: dict,
    ) -> StoredReview: ...

    async def events(self, review_id: str, after_sequence: int = 0) -> list[StoredEvent]: ...


def _stored_review(row: ReviewSession) -> StoredReview:
    return StoredReview(
        id=row.id,
        operator_hash=row.operator_hash,
        status=row.status,
        mode=row.mode,
        preferred_mode=row.preferred_mode,
        documents=row.documents or [],
        patient_context=row.patient_context or {},
        redaction_receipt=row.redaction_receipt or {},
        analysis=row.analysis or {},
        pending_actions=row.pending_actions or [],
        version=row.version,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class SqlReviewStore:
    async def create(self, review: StoredReview, event_type: str, phase: str, payload: dict) -> StoredReview:
        async with async_session() as db:
            row = ReviewSession(
                id=review.id,
                operator_hash=review.operator_hash,
                status=review.status,
                mode=review.mode,
                preferred_mode=review.preferred_mode,
                documents=review.documents,
                patient_context=review.patient_context,
                redaction_receipt=review.redaction_receipt,
                analysis=review.analysis,
                pending_actions=review.pending_actions,
                version=review.version,
            )
            db.add(row)
            db.add(ReviewEvent(
                review_id=review.id,
                sequence=1,
                event_type=event_type,
                phase=phase,
                payload=payload,
            ))
            await db.commit()
            await db.refresh(row)
            return _stored_review(row)

    async def get(self, review_id: str) -> StoredReview:
        async with async_session() as db:
            row = (await db.execute(
                select(ReviewSession).where(ReviewSession.id == review_id)
            )).scalar_one_or_none()
            if row is None:
                raise ReviewNotFoundError(review_id)
            return _stored_review(row)

    async def transition(
        self,
        review_id: str,
        expected_version: int,
        *,
        status: str,
        mode: str,
        analysis: dict,
        pending_actions: list[dict],
        event_type: str,
        phase: str,
        payload: dict,
    ) -> StoredReview:
        async with async_session() as db:
            row = (await db.execute(
                select(ReviewSession).where(ReviewSession.id == review_id)
            )).scalar_one_or_none()
            if row is None:
                raise ReviewNotFoundError(review_id)
            if row.version != expected_version:
                raise ReviewVersionConflictError(review_id)
            next_sequence = (await db.execute(
                select(func.coalesce(func.max(ReviewEvent.sequence), 0)).where(
                    ReviewEvent.review_id == review_id
                )
            )).scalar_one() + 1
            row.status = status
            row.mode = mode
            row.analysis = analysis
            row.pending_actions = pending_actions
            row.version += 1
            db.add(ReviewEvent(
                review_id=review_id,
                sequence=next_sequence,
                event_type=event_type,
                phase=phase,
                payload=payload,
            ))
            await db.commit()
            await db.refresh(row)
            return _stored_review(row)

    async def events(self, review_id: str, after_sequence: int = 0) -> list[StoredEvent]:
        async with async_session() as db:
            rows = (await db.execute(
                select(ReviewEvent)
                .where(ReviewEvent.review_id == review_id, ReviewEvent.sequence > after_sequence)
                .order_by(ReviewEvent.sequence)
            )).scalars().all()
            return [
                StoredEvent(
                    sequence=row.sequence,
                    event_type=row.event_type,
                    phase=row.phase,
                    payload=row.payload or {},
                    created_at=row.created_at,
                )
                for row in rows
            ]
