from typing import Literal

from pydantic import BaseModel, Field, model_validator


DocumentType = Literal[
    "admission",
    "course",
    "surgery",
    "discharge",
    "consultation",
    "exam",
    "lab",
]


class ReviewDocument(BaseModel):
    id: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=128)
    record_type: DocumentType
    content: str = Field(min_length=10, max_length=50_000)
    recorded_at: str | None = Field(default=None, max_length=64)


class RedactionReceipt(BaseModel):
    redacted_count: int = Field(ge=0, le=100)
    categories: list[str] = Field(default_factory=list, max_length=10)
    content_hash: str = Field(min_length=16, max_length=128)


class CreateReviewRequest(BaseModel):
    documents: list[ReviewDocument] = Field(min_length=1, max_length=8)
    redaction_receipt: RedactionReceipt
    patient_context: dict[str, str | int | float | bool | None] = Field(default_factory=dict)
    preferred_mode: Literal["auto", "rules"] = "auto"


class ExpectedVersionRequest(BaseModel):
    expected_version: int = Field(ge=1)


class ReviewDecisionRequest(ExpectedVersionRequest):
    action: Literal["confirm_source", "mark_pending", "confirm_review"]
    issue_id: str | None = Field(default=None, max_length=128)
    selected_document_id: str | None = Field(default=None, max_length=64)
    note: str = Field(default="", max_length=500)

    @model_validator(mode="after")
    def validate_decision(self):
        if self.action in {"confirm_source", "mark_pending"} and not self.issue_id:
            raise ValueError("issue_id is required for this action")
        if self.action == "confirm_source" and not self.selected_document_id:
            raise ValueError("selected_document_id is required when confirming a source")
        return self


class ReviewEventOut(BaseModel):
    sequence: int
    event_type: str
    phase: str
    payload: dict
    created_at: str


class ReviewSnapshot(BaseModel):
    id: str
    status: str
    mode: str
    version: int
    documents: list[ReviewDocument]
    redaction_receipt: RedactionReceipt
    analysis: dict
    pending_actions: list[dict]
    created_at: str
    updated_at: str
