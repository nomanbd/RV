import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# --- Appointment ---


class AppointmentCreate(BaseModel):
    patient_id: uuid.UUID
    course_id: uuid.UUID | None = None
    fraction_id: uuid.UUID | None = None
    appointment_type: str = Field(
        pattern="^(treatment|simulation|consultation|follow_up|physics_qa|plan_review)$"
    )
    scheduled_start: datetime
    scheduled_end: datetime
    duration_minutes: int = Field(gt=0)
    resource_id: uuid.UUID | None = None
    assigned_therapist_id: uuid.UUID | None = None
    notes: str | None = None


class AppointmentUpdate(BaseModel):
    patient_id: uuid.UUID | None = None
    course_id: uuid.UUID | None = None
    fraction_id: uuid.UUID | None = None
    appointment_type: str | None = Field(
        None,
        pattern="^(treatment|simulation|consultation|follow_up|physics_qa|plan_review)$",
    )
    scheduled_start: datetime | None = None
    scheduled_end: datetime | None = None
    duration_minutes: int | None = Field(None, gt=0)
    resource_id: uuid.UUID | None = None
    assigned_therapist_id: uuid.UUID | None = None
    notes: str | None = None


class AppointmentResponse(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    course_id: uuid.UUID | None
    fraction_id: uuid.UUID | None
    appointment_type: str
    status: str
    scheduled_start: datetime
    scheduled_end: datetime
    actual_start: datetime | None
    actual_end: datetime | None
    duration_minutes: int
    resource_id: uuid.UUID | None
    assigned_therapist_id: uuid.UUID | None
    notes: str | None
    recurring_group_id: uuid.UUID | None
    created_by_id: uuid.UUID
    cancelled_by_id: uuid.UUID | None
    cancellation_reason: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RecurringAppointmentCreate(AppointmentCreate):
    num_occurrences: int = Field(gt=0, le=100)
    frequency: str = Field(default="daily", pattern="^(daily|weekly|biweekly)$")


# --- Resource ---


class ResourceCreate(BaseModel):
    name: str = Field(max_length=200)
    resource_type: str = Field(max_length=50)
    machine_id: uuid.UUID | None = None
    user_id: uuid.UUID | None = None
    color: str | None = Field(None, max_length=7)


class ResourceResponse(BaseModel):
    id: uuid.UUID
    name: str
    resource_type: str
    machine_id: uuid.UUID | None
    user_id: uuid.UUID | None
    is_active: bool
    color: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Workflow Task ---


class WorkflowTaskCreate(BaseModel):
    patient_id: uuid.UUID
    course_id: uuid.UUID | None = None
    task_type: str = Field(max_length=100)
    title: str = Field(max_length=255)
    description: str | None = None
    priority: str = Field(
        default="normal", pattern="^(low|normal|high|urgent)$"
    )
    assigned_to_id: uuid.UUID | None = None
    assigned_role_id: uuid.UUID | None = None
    due_date: datetime | None = None
    depends_on_task_id: uuid.UUID | None = None


class WorkflowTaskUpdate(BaseModel):
    status: str | None = Field(
        None,
        pattern="^(pending|assigned|in_progress|completed|blocked|cancelled)$",
    )
    assigned_to_id: uuid.UUID | None = None
    notes: str | None = None


class WorkflowTaskResponse(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    course_id: uuid.UUID | None
    task_type: str
    title: str
    description: str | None
    status: str
    priority: str
    assigned_to_id: uuid.UUID | None
    assigned_role_id: uuid.UUID | None
    due_date: datetime | None
    completed_at: datetime | None
    completed_by_id: uuid.UUID | None
    depends_on_task_id: uuid.UUID | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Notification ---


class NotificationResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    message: str
    notification_type: str
    entity_type: str | None
    entity_id: uuid.UUID | None
    is_read: bool
    read_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
