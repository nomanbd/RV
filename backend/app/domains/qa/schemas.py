import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# --- QA Checklist ---


class QAChecklistCreate(BaseModel):
    name: str = Field(max_length=200)
    description: str | None = None
    checklist_type: str = Field(max_length=50)
    machine_id: uuid.UUID | None = None
    items: list[dict] = Field(
        ...,
        description=(
            "List of checklist items, each containing: "
            "id, label, expected_value, tolerance, unit, required"
        ),
    )


class QAChecklistResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    checklist_type: str
    machine_id: uuid.UUID | None
    items: list[dict]
    is_active: bool
    version: int
    created_by_id: uuid.UUID
    approved_by_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- QA Record ---


class QARecordCreate(BaseModel):
    checklist_id: uuid.UUID
    machine_id: uuid.UUID | None = None
    patient_id: uuid.UUID | None = None
    plan_id: uuid.UUID | None = None
    results: list[dict] = Field(
        ...,
        description=(
            "List of result entries, each containing: "
            "item_id, measured_value, pass, notes"
        ),
    )
    overall_pass: bool
    comments: str | None = None


class QARecordResponse(BaseModel):
    id: uuid.UUID
    checklist_id: uuid.UUID
    machine_id: uuid.UUID | None
    patient_id: uuid.UUID | None
    plan_id: uuid.UUID | None
    performed_by_id: uuid.UUID
    performed_at: datetime
    results: list[dict]
    overall_pass: bool
    reviewed_by_id: uuid.UUID | None
    reviewed_at: datetime | None
    review_signature_id: uuid.UUID | None
    comments: str | None
    attachments: dict | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- QA Review ---


class QAReviewRequest(BaseModel):
    signature_id: uuid.UUID
