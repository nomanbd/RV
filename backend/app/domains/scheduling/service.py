import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.domains.scheduling.models import Appointment, Notification, Resource, WorkflowTask
from app.domains.scheduling.schemas import (
    AppointmentCreate,
    AppointmentUpdate,
    ResourceCreate,
    WorkflowTaskCreate,
    WorkflowTaskUpdate,
)


class SchedulingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Appointments ──────────────────────────────────────────────

    async def create_appointment(
        self, data: AppointmentCreate, created_by_id: uuid.UUID
    ) -> Appointment:
        if data.resource_id is not None:
            has_conflict = await self.check_conflicts(
                data.resource_id, data.scheduled_start, data.scheduled_end
            )
            if has_conflict:
                raise ConflictError(
                    "Resource has a scheduling conflict for the requested time slot"
                )

        appointment = Appointment(
            **data.model_dump(), created_by_id=created_by_id
        )
        self.db.add(appointment)
        await self.db.flush()
        return appointment

    async def get_appointment(self, appointment_id: uuid.UUID) -> Appointment:
        result = await self.db.execute(
            select(Appointment).where(Appointment.id == appointment_id)
        )
        appointment = result.scalar_one_or_none()
        if appointment is None:
            raise NotFoundError("Appointment not found")
        return appointment

    async def list_appointments(
        self,
        patient_id: uuid.UUID | None = None,
        resource_id: uuid.UUID | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        status: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Appointment]:
        query = select(Appointment)

        if patient_id is not None:
            query = query.where(Appointment.patient_id == patient_id)
        if resource_id is not None:
            query = query.where(Appointment.resource_id == resource_id)
        if date_from is not None:
            query = query.where(Appointment.scheduled_start >= date_from)
        if date_to is not None:
            query = query.where(Appointment.scheduled_start <= date_to)
        if status is not None:
            query = query.where(Appointment.status == status)

        query = query.order_by(Appointment.scheduled_start).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_appointment(
        self, appointment_id: uuid.UUID, data: AppointmentUpdate
    ) -> Appointment:
        appointment = await self.get_appointment(appointment_id)
        update_data = data.model_dump(exclude_unset=True)

        # If rescheduling, check for conflicts
        new_start = update_data.get("scheduled_start", appointment.scheduled_start)
        new_end = update_data.get("scheduled_end", appointment.scheduled_end)
        resource_id = update_data.get("resource_id", appointment.resource_id)

        if resource_id is not None and (
            "scheduled_start" in update_data
            or "scheduled_end" in update_data
            or "resource_id" in update_data
        ):
            has_conflict = await self.check_conflicts(
                resource_id, new_start, new_end, exclude_id=appointment_id
            )
            if has_conflict:
                raise ConflictError(
                    "Resource has a scheduling conflict for the requested time slot"
                )

        for field, value in update_data.items():
            setattr(appointment, field, value)

        await self.db.flush()
        return appointment

    async def cancel_appointment(
        self,
        appointment_id: uuid.UUID,
        cancelled_by_id: uuid.UUID,
        reason: str,
    ) -> Appointment:
        appointment = await self.get_appointment(appointment_id)
        appointment.status = "cancelled"
        appointment.cancelled_by_id = cancelled_by_id
        appointment.cancellation_reason = reason
        await self.db.flush()
        return appointment

    async def create_recurring(
        self,
        data: AppointmentCreate,
        created_by_id: uuid.UUID,
        num_occurrences: int,
        frequency: str = "daily",
    ) -> list[Appointment]:
        frequency_deltas = {
            "daily": timedelta(days=1),
            "weekly": timedelta(weeks=1),
            "biweekly": timedelta(weeks=2),
        }
        delta = frequency_deltas.get(frequency, timedelta(days=1))
        recurring_group_id = uuid.uuid4()

        appointments: list[Appointment] = []
        for i in range(num_occurrences):
            offset = delta * i
            appt_data = data.model_dump()
            appt_data["scheduled_start"] = data.scheduled_start + offset
            appt_data["scheduled_end"] = data.scheduled_end + offset
            appointment = Appointment(
                **appt_data,
                created_by_id=created_by_id,
                recurring_group_id=recurring_group_id,
            )
            self.db.add(appointment)
            appointments.append(appointment)

        await self.db.flush()
        return appointments

    async def check_conflicts(
        self,
        resource_id: uuid.UUID,
        start: datetime,
        end: datetime,
        exclude_id: uuid.UUID | None = None,
    ) -> bool:
        query = select(Appointment).where(
            and_(
                Appointment.resource_id == resource_id,
                Appointment.status != "cancelled",
                Appointment.scheduled_start < end,
                Appointment.scheduled_end > start,
            )
        )
        if exclude_id is not None:
            query = query.where(Appointment.id != exclude_id)

        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None

    # ── Resources ─────────────────────────────────────────────────

    async def create_resource(self, data: ResourceCreate) -> Resource:
        resource = Resource(**data.model_dump())
        self.db.add(resource)
        await self.db.flush()
        return resource

    async def list_resources(
        self, resource_type: str | None = None
    ) -> list[Resource]:
        query = select(Resource).where(Resource.is_active.is_(True))
        if resource_type is not None:
            query = query.where(Resource.resource_type == resource_type)
        query = query.order_by(Resource.name)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    # ── Workflow Tasks ────────────────────────────────────────────

    async def create_task(self, data: WorkflowTaskCreate) -> WorkflowTask:
        task = WorkflowTask(**data.model_dump())
        self.db.add(task)
        await self.db.flush()
        return task

    async def get_task(self, task_id: uuid.UUID) -> WorkflowTask:
        result = await self.db.execute(
            select(WorkflowTask).where(WorkflowTask.id == task_id)
        )
        task = result.scalar_one_or_none()
        if task is None:
            raise NotFoundError("Workflow task not found")
        return task

    async def list_tasks(
        self,
        patient_id: uuid.UUID | None = None,
        assigned_to_id: uuid.UUID | None = None,
        status: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[WorkflowTask]:
        query = select(WorkflowTask)

        if patient_id is not None:
            query = query.where(WorkflowTask.patient_id == patient_id)
        if assigned_to_id is not None:
            query = query.where(WorkflowTask.assigned_to_id == assigned_to_id)
        if status is not None:
            query = query.where(WorkflowTask.status == status)

        query = query.order_by(WorkflowTask.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_task(
        self,
        task_id: uuid.UUID,
        data: WorkflowTaskUpdate,
        user_id: uuid.UUID,
    ) -> WorkflowTask:
        task = await self.get_task(task_id)
        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(task, field, value)

        # Handle completion
        if update_data.get("status") == "completed":
            task.completed_at = datetime.now(timezone.utc)
            task.completed_by_id = user_id

        await self.db.flush()
        return task

    # ── Notifications ─────────────────────────────────────────────

    async def get_notifications(
        self, user_id: uuid.UUID, unread_only: bool = True
    ) -> list[Notification]:
        query = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            query = query.where(Notification.is_read.is_(False))
        query = query.order_by(Notification.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def mark_notification_read(
        self, notification_id: uuid.UUID
    ) -> Notification:
        result = await self.db.execute(
            select(Notification).where(Notification.id == notification_id)
        )
        notification = result.scalar_one_or_none()
        if notification is None:
            raise NotFoundError("Notification not found")

        notification.is_read = True
        notification.read_at = datetime.now(timezone.utc)
        await self.db.flush()
        return notification

    async def create_notification(
        self,
        user_id: uuid.UUID,
        title: str,
        message: str,
        notification_type: str,
        entity_type: str | None = None,
        entity_id: uuid.UUID | None = None,
    ) -> Notification:
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            entity_type=entity_type,
            entity_id=entity_id,
        )
        self.db.add(notification)
        await self.db.flush()
        return notification
