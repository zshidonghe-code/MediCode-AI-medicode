"""HTTP boundary for the discharge coding review Agent."""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.api.v1.endpoints.auth import get_current_user
from src.services.review_agent import (
    RedactionViolationError,
    ReviewAccessDeniedError,
    ReviewAgent,
    ReviewInvalidStateError,
    ReviewNotFoundError,
    ReviewVersionConflictError,
)
from src.services.review_agent.contracts import (
    CreateReviewRequest,
    ExpectedVersionRequest,
    ReviewDecisionRequest,
    ReviewEventOut,
    ReviewSnapshot,
)
from src.services.review_agent.repository import SqlReviewStore

router = APIRouter()


def get_review_agent() -> ReviewAgent:
    return ReviewAgent(SqlReviewStore())


def _raise_review_error(error: Exception) -> None:
    if isinstance(error, ReviewNotFoundError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    if isinstance(error, ReviewVersionConflictError):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    if isinstance(error, ReviewAccessDeniedError):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(error)) from error
    if isinstance(error, (ReviewInvalidStateError, RedactionViolationError)):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)
        ) from error
    raise error


@router.post("", response_model=ReviewSnapshot, status_code=status.HTTP_201_CREATED)
async def create_review(
    request: CreateReviewRequest,
    user: dict = Depends(get_current_user),
    agent: ReviewAgent = Depends(get_review_agent),
):
    try:
        return await agent.create(request, user)
    except (ReviewInvalidStateError, RedactionViolationError) as error:
        _raise_review_error(error)


@router.get("/{review_id}", response_model=ReviewSnapshot)
async def get_review(
    review_id: str,
    user: dict = Depends(get_current_user),
    agent: ReviewAgent = Depends(get_review_agent),
):
    try:
        return await agent.get(review_id, user)
    except (ReviewNotFoundError, ReviewAccessDeniedError) as error:
        _raise_review_error(error)


@router.post("/{review_id}/advance", response_model=ReviewSnapshot)
async def advance_review(
    review_id: str,
    request: ExpectedVersionRequest,
    user: dict = Depends(get_current_user),
    agent: ReviewAgent = Depends(get_review_agent),
):
    try:
        return await agent.advance(review_id, request.expected_version, user)
    except (
        ReviewNotFoundError,
        ReviewVersionConflictError,
        ReviewInvalidStateError,
        ReviewAccessDeniedError,
    ) as error:
        _raise_review_error(error)


@router.post("/{review_id}/decisions", response_model=ReviewSnapshot)
async def decide_review(
    review_id: str,
    request: ReviewDecisionRequest,
    user: dict = Depends(get_current_user),
    agent: ReviewAgent = Depends(get_review_agent),
):
    try:
        return await agent.decide(review_id, request, user)
    except (
        ReviewNotFoundError,
        ReviewVersionConflictError,
        ReviewInvalidStateError,
        ReviewAccessDeniedError,
    ) as error:
        _raise_review_error(error)


@router.get("/{review_id}/events", response_model=list[ReviewEventOut])
async def get_review_events(
    review_id: str,
    after_sequence: int = Query(default=0, ge=0),
    user: dict = Depends(get_current_user),
    agent: ReviewAgent = Depends(get_review_agent),
):
    try:
        return await agent.events(review_id, user, after_sequence)
    except (ReviewNotFoundError, ReviewAccessDeniedError) as error:
        _raise_review_error(error)


@router.get("/{review_id}/report")
async def get_review_report(
    review_id: str,
    user: dict = Depends(get_current_user),
    agent: ReviewAgent = Depends(get_review_agent),
):
    try:
        return await agent.report(review_id, user)
    except (ReviewNotFoundError, ReviewInvalidStateError, ReviewAccessDeniedError) as error:
        _raise_review_error(error)
