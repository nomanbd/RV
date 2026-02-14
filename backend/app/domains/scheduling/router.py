import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.domains.auth.models import User
from app.domains.scheduling.schemas import (
    AppointmentCreate,
    AppointmentResponse,
    AppointmentUpdate,
    NotificationResponse,
    RecurringAppointmentCreate,
    ResourceCreate,
    ResourceResponse,
    WorkflowTaskCreate,
    WorkflowTaskResponse,
    WorkflowTaskUpdate,
)
from app.domains.scheduling.service import SchedulingService

router = APIRouter(prefix="/scheduling", tags=["scheduling"])


# ── Appointments ──────────────────────────────────────────────────


@router.post("/appointments", response_model=AppointmentResponse, status_code=201)
async def create_appointment(
    data: AppointmentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = SchedulingService(db)
    return await service.create_appointment(data, created_by_id=current_user.id)


@router.get("/appointments", response_model=list[AppointmentResponse])
async def list_appointments(
    patient_id: uuid.UUID | None = None,
    resource_id: uuid.UUID | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    status: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = SchedulingService(db)
    return await service.list_appointments(
        patient_id=patient_id,
        resource_id=resource_id,
        date_from=date_from,
        date_to=date_to,
        status=status,
        skip=skip,
        limit=limit,
    )


@router.get("/appointments/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment(
    appointment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = SchedulingService(db)
    return await service.get_appointment(appointment_id)


@router.put("/appointments/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(
    appointment_id: uuid.UUID,
    data: AppointmentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = SchedulingService(db)
    return await service.update_appointment(appointment_id, data)


class CancelRequest(BaseModel):
    reason: str


@router.delete("/appointments/{appointment_id}", response_model=AppointmentResponse)
async def cancel_appointment(
    appointment_id: uuid.UUID,
    body: CancelRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = SchedulingService(db)
    return await service.cancel_appointment(
        appointment_id,
        cancelled_by_id=current_user.id,
        reason=body.reason,
    )


@router.post(
    "/appointments/recurring",
    response_model=list[AppointmentResponse],
    status_code=201,
)
async def create_recurring_appointments(
    data: RecurringAppointmentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = SchedulingService(db)
    return await service.create_recurring(
        data,
        created_by_id=current_user.id,
        num_occurrences=data.num_occurrences,
        frequency=data.frequency,
    )


# ── Resources ─────────────────────────────────────────────────────


@router.get("/resources", response_model=list[ResourceResponse])
async def list_resources(
    resource_type: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = SchedulingService(db)
    return await service.list_resources(resource_type=resource_type)


@router.post("/resources", response_model=ResourceResponse, status_code=201)
async def create_resource(
    data: ResourceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = SchedulingService(db)
    return await service.create_resource(data)


# ── Workflow Tasks ────────────────────────────────────────────────


@router.post("/tasks", response_model=WorkflowTaskResponse, status_code=201)
async def create_task(
    data: WorkflowTaskCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = SchedulingService(db)
    return await service.create_task(data)


@router.get("/tasks", response_model=list[WorkflowTaskResponse])
async def list_tasks(
    patient_id: uuid.UUID | None = None,
    assigned_to_id: uuid.UUID | None = None,
    status: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = SchedulingService(db)
    return await service.list_tasks(
        patient_id=patient_id,
        assigned_to_id=assigned_to_id,
        status=status,
        skip=skip,
        limit=limit,
    )


@router.patch("/tasks/{task_id}", response_model=WorkflowTaskResponse)
async def update_task(
    task_id: uuid.UUID,
    data: WorkflowTaskUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = SchedulingService(db)
    return await service.update_task(task_id, data, user_id=current_user.id)


# ── Notifications ─────────────────────────────────────────────────


@router.get("/notifications", response_model=list[NotificationResponse])
async def get_notifications(
    unread_only: bool = True,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = SchedulingService(db)
    return await service.get_notifications(
        user_id=current_user.id, unread_only=unread_only
    )


@router.patch(
    "/notifications/{notification_id}/read",
    response_model=NotificationResponse,
)
async def mark_notification_read(
    notification_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = SchedulingService(db)
    return await service.mark_notification_read(notification_id)
