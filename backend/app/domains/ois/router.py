import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.domains.auth.models import User
from app.domains.ois.schemas import (
    OISConnectionCreate,
    OISConnectionResponse,
    OISConnectionTestResult,
    OISConnectionUpdate,
    OISPatientImportResult,
    OISPatientLookupRequest,
    OISPatientResult,
    OISPlanResult,
    OISRecordExportRequest,
    OISRecordExportResult,
    OISScheduleSyncRequest,
    OISScheduleSyncResult,
    OISSyncLogResponse,
    OISSyncStatusResponse,
)
from app.domains.ois.service import OISService

router = APIRouter(prefix="/ois", tags=["ois"])


# ── Connection Management ─────────────────────────────────────────────

@router.get("/connections", response_model=list[OISConnectionResponse])
async def list_connections(
    active_only: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = OISService(db)
    return await service.list_connections(active_only=active_only)


@router.post("/connections", response_model=OISConnectionResponse, status_code=201)
async def create_connection(
    data: OISConnectionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = OISService(db)
    return await service.create_connection(data)


@router.get("/connections/{connection_id}", response_model=OISConnectionResponse)
async def get_connection(
    connection_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = OISService(db)
    return await service.get_connection(connection_id)


@router.put("/connections/{connection_id}", response_model=OISConnectionResponse)
async def update_connection(
    connection_id: uuid.UUID,
    data: OISConnectionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = OISService(db)
    return await service.update_connection(connection_id, data)


@router.delete("/connections/{connection_id}", status_code=204)
async def delete_connection(
    connection_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = OISService(db)
    await service.delete_connection(connection_id)


@router.post("/connections/{connection_id}/test", response_model=OISConnectionTestResult)
async def test_connection(
    connection_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = OISService(db)
    return await service.test_connection(connection_id)


# ── Patient Operations ────────────────────────────────────────────────

@router.post("/connections/{connection_id}/patients/lookup", response_model=list[OISPatientResult])
async def lookup_patients(
    connection_id: uuid.UUID,
    data: OISPatientLookupRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = OISService(db)
    return await service.lookup_patients(connection_id, data)


@router.post(
    "/connections/{connection_id}/patients/{external_id}/import",
    response_model=OISPatientImportResult,
)
async def import_patient(
    connection_id: uuid.UUID,
    external_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = OISService(db)
    return await service.import_patient(connection_id, external_id, user_id=current_user.id)


# ── Plan Operations ───────────────────────────────────────────────────

@router.get(
    "/connections/{connection_id}/patients/{external_patient_id}/plans",
    response_model=list[OISPlanResult],
)
async def get_patient_plans(
    connection_id: uuid.UUID,
    external_patient_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = OISService(db)
    return await service.get_patient_plans(connection_id, external_patient_id)


@router.get(
    "/connections/{connection_id}/patients/{external_patient_id}/plans/{external_plan_id}",
)
async def get_plan_details(
    connection_id: uuid.UUID,
    external_patient_id: str,
    external_plan_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = OISService(db)
    return await service.get_plan_details(connection_id, external_patient_id, external_plan_id)


# ── Schedule Sync ─────────────────────────────────────────────────────

@router.post("/schedule/sync", response_model=OISScheduleSyncResult)
async def sync_schedule(
    data: OISScheduleSyncRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = OISService(db)
    return await service.sync_schedule(
        connection_id=data.connection_id,
        date_from=data.date_from,
        date_to=data.date_to,
        machine_name=data.machine_name,
        user_id=current_user.id,
    )


# ── Treatment Record Export ───────────────────────────────────────────

@router.post("/records/export", response_model=OISRecordExportResult)
async def export_treatment_record(
    data: OISRecordExportRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = OISService(db)
    return await service.export_treatment_record(
        connection_id=data.connection_id,
        session_id=data.session_id,
        user_id=current_user.id,
    )


# ── Sync Status & Logs ───────────────────────────────────────────────

@router.get("/connections/{connection_id}/status", response_model=OISSyncStatusResponse)
async def get_sync_status(
    connection_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = OISService(db)
    return await service.get_sync_status(connection_id)


@router.get("/sync-logs", response_model=list[OISSyncLogResponse])
async def get_sync_logs(
    connection_id: uuid.UUID | None = None,
    operation: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = OISService(db)
    return await service.get_sync_logs(connection_id=connection_id, operation=operation, limit=limit)
