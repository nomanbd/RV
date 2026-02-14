import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.domains.auth.models import User
from app.domains.qa.schemas import (
    QAChecklistCreate,
    QAChecklistResponse,
    QARecordCreate,
    QARecordResponse,
    QAReviewRequest,
)
from app.domains.qa.service import QAService

router = APIRouter(prefix="/qa", tags=["qa"])


# ── Checklists ────────────────────────────────────────────────────


@router.post("/checklists", response_model=QAChecklistResponse, status_code=201)
async def create_checklist(
    data: QAChecklistCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = QAService(db)
    return await service.create_checklist(data, created_by_id=current_user.id)


@router.get("/checklists", response_model=list[QAChecklistResponse])
async def list_checklists(
    checklist_type: str | None = None,
    machine_id: uuid.UUID | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = QAService(db)
    return await service.list_checklists(
        checklist_type=checklist_type, machine_id=machine_id
    )


@router.get("/checklists/{checklist_id}", response_model=QAChecklistResponse)
async def get_checklist(
    checklist_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = QAService(db)
    return await service.get_checklist(checklist_id)


@router.put("/checklists/{checklist_id}", response_model=QAChecklistResponse)
async def update_checklist(
    checklist_id: uuid.UUID,
    data: QAChecklistCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = QAService(db)
    return await service.update_checklist(checklist_id, data)


# ── Records ───────────────────────────────────────────────────────


@router.post("/records", response_model=QARecordResponse, status_code=201)
async def submit_record(
    data: QARecordCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = QAService(db)
    return await service.submit_record(data, performed_by_id=current_user.id)


@router.get("/records", response_model=list[QARecordResponse])
async def list_records(
    machine_id: uuid.UUID | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = QAService(db)
    return await service.list_records(
        machine_id=machine_id,
        date_from=date_from,
        date_to=date_to,
        skip=skip,
        limit=limit,
    )


@router.get("/records/{record_id}", response_model=QARecordResponse)
async def get_record(
    record_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = QAService(db)
    return await service.get_record(record_id)


@router.post("/records/{record_id}/review", response_model=QARecordResponse)
async def review_record(
    record_id: uuid.UUID,
    data: QAReviewRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = QAService(db)
    return await service.review_record(
        record_id,
        reviewer_id=current_user.id,
        signature_id=data.signature_id,
    )
