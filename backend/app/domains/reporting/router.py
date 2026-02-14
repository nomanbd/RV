import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.domains.auth.models import User
from app.domains.reporting.schemas import (
    DashboardStats,
    DoseTrackingReport,
    MachineUtilizationReport,
    TreatmentSummaryReport,
)
from app.domains.reporting.service import ReportingService

router = APIRouter(tags=["reports"])


@router.get(
    "/reports/treatment-summary/{patient_id}",
    response_model=TreatmentSummaryReport,
)
async def get_treatment_summary(
    patient_id: uuid.UUID,
    course_id: uuid.UUID | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ReportingService(db)
    return await service.get_treatment_summary(
        patient_id=patient_id, course_id=course_id
    )


@router.get(
    "/reports/dose-tracking/{course_id}",
    response_model=DoseTrackingReport,
)
async def get_dose_tracking(
    course_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ReportingService(db)
    return await service.get_dose_tracking(course_id=course_id)


@router.get(
    "/reports/machine-utilization",
    response_model=list[MachineUtilizationReport],
)
async def get_machine_utilization(
    machine_id: uuid.UUID | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ReportingService(db)
    return await service.get_machine_utilization(
        machine_id=machine_id, date_from=date_from, date_to=date_to
    )


@router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ReportingService(db)
    return await service.get_dashboard_stats()
