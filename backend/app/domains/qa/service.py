import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.domains.qa.models import QAChecklist, QARecord
from app.domains.qa.schemas import QAChecklistCreate, QARecordCreate


class QAService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Checklists ────────────────────────────────────────────────

    async def create_checklist(
        self, data: QAChecklistCreate, created_by_id: uuid.UUID
    ) -> QAChecklist:
        checklist = QAChecklist(
            **data.model_dump(), created_by_id=created_by_id
        )
        self.db.add(checklist)
        await self.db.flush()
        return checklist

    async def get_checklist(self, checklist_id: uuid.UUID) -> QAChecklist:
        result = await self.db.execute(
            select(QAChecklist).where(QAChecklist.id == checklist_id)
        )
        checklist = result.scalar_one_or_none()
        if checklist is None:
            raise NotFoundError("QA checklist not found")
        return checklist

    async def list_checklists(
        self,
        checklist_type: str | None = None,
        machine_id: uuid.UUID | None = None,
        active_only: bool = True,
    ) -> list[QAChecklist]:
        query = select(QAChecklist)

        if active_only:
            query = query.where(QAChecklist.is_active.is_(True))
        if checklist_type is not None:
            query = query.where(QAChecklist.checklist_type == checklist_type)
        if machine_id is not None:
            query = query.where(QAChecklist.machine_id == machine_id)

        query = query.order_by(QAChecklist.name)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_checklist(
        self, checklist_id: uuid.UUID, data: QAChecklistCreate
    ) -> QAChecklist:
        checklist = await self.get_checklist(checklist_id)
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(checklist, field, value)
        checklist.version += 1
        await self.db.flush()
        return checklist

    # ── Records ───────────────────────────────────────────────────

    async def submit_record(
        self, data: QARecordCreate, performed_by_id: uuid.UUID
    ) -> QARecord:
        # Verify checklist exists
        await self.get_checklist(data.checklist_id)

        record = QARecord(
            **data.model_dump(),
            performed_by_id=performed_by_id,
            performed_at=datetime.now(timezone.utc),
        )
        self.db.add(record)
        await self.db.flush()
        return record

    async def get_record(self, record_id: uuid.UUID) -> QARecord:
        result = await self.db.execute(
            select(QARecord).where(QARecord.id == record_id)
        )
        record = result.scalar_one_or_none()
        if record is None:
            raise NotFoundError("QA record not found")
        return record

    async def list_records(
        self,
        machine_id: uuid.UUID | None = None,
        checklist_type: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[QARecord]:
        query = select(QARecord)

        if machine_id is not None:
            query = query.where(QARecord.machine_id == machine_id)
        if checklist_type is not None:
            query = query.join(QAChecklist).where(
                QAChecklist.checklist_type == checklist_type
            )
        if date_from is not None:
            query = query.where(QARecord.performed_at >= date_from)
        if date_to is not None:
            query = query.where(QARecord.performed_at <= date_to)

        query = (
            query.order_by(QARecord.performed_at.desc()).offset(skip).limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def review_record(
        self,
        record_id: uuid.UUID,
        reviewer_id: uuid.UUID,
        signature_id: uuid.UUID,
    ) -> QARecord:
        record = await self.get_record(record_id)
        record.reviewed_by_id = reviewer_id
        record.reviewed_at = datetime.now(timezone.utc)
        record.review_signature_id = signature_id
        await self.db.flush()
        return record
