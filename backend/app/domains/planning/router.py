import uuid

from fastapi import APIRouter, Depends, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.domains.auth.models import User
from app.domains.planning.schemas import (
    BeamControlPointResponse,
    PlanApprovalRequest,
    PlanBeamResponse,
    PlanImportResponse,
    PrescriptionCreate,
    PrescriptionResponse,
    TreatmentCourseCreate,
    TreatmentCourseResponse,
    TreatmentPlanResponse,
)
from app.domains.planning.service import PlanningService

router = APIRouter(prefix="/plans", tags=["planning"])


# ---- Treatment Courses ----


@router.post("/courses", response_model=TreatmentCourseResponse, status_code=201)
async def create_course(
    data: TreatmentCourseCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = PlanningService(db)
    course = await service.create_course(
        patient_id=data.patient_id,
        data=data.model_dump(exclude={"patient_id"}),
    )
    return course


@router.get("/courses", response_model=list[TreatmentCourseResponse])
async def list_courses(
    patient_id: uuid.UUID | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = PlanningService(db)
    return await service.list_courses(patient_id=patient_id, skip=skip, limit=limit)


@router.get("/courses/{course_id}", response_model=TreatmentCourseResponse)
async def get_course(
    course_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = PlanningService(db)
    return await service.get_course(course_id)


# ---- Prescriptions ----


@router.post("/prescriptions", response_model=PrescriptionResponse, status_code=201)
async def create_prescription(
    data: PrescriptionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = PlanningService(db)
    return await service.create_prescription(data.model_dump())


@router.post(
    "/prescriptions/{prescription_id}/approve",
    response_model=PrescriptionResponse,
)
async def approve_prescription(
    prescription_id: uuid.UUID,
    data: PlanApprovalRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = PlanningService(db)
    return await service.approve_prescription(
        prescription_id=prescription_id,
        user_id=current_user.id,
        signature_id=data.signature_id,
    )


# ---- Treatment Plans ----


@router.post("/plans/import", response_model=PlanImportResponse, status_code=201)
async def import_plan(
    file: UploadFile,
    course_id: uuid.UUID = Query(...),
    prescription_id: uuid.UUID = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    file_bytes = await file.read()
    service = PlanningService(db)
    return await service.import_plan(
        file_bytes=file_bytes,
        filename=file.filename or "unknown.dcm",
        course_id=course_id,
        prescription_id=prescription_id,
        created_by_id=current_user.id,
    )


@router.get("/plans", response_model=list[TreatmentPlanResponse])
async def list_plans(
    patient_id: uuid.UUID | None = None,
    status: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = PlanningService(db)
    return await service.list_plans(
        patient_id=patient_id, status=status, skip=skip, limit=limit
    )


@router.get("/plans/{plan_id}", response_model=TreatmentPlanResponse)
async def get_plan(
    plan_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = PlanningService(db)
    return await service.get_plan(plan_id)


@router.get("/plans/{plan_id}/beams", response_model=list[PlanBeamResponse])
async def get_plan_beams(
    plan_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = PlanningService(db)
    return await service.get_plan_beams(plan_id)


@router.get(
    "/plans/{plan_id}/beams/{beam_id}/control-points",
    response_model=list[BeamControlPointResponse],
)
async def get_beam_control_points(
    plan_id: uuid.UUID,
    beam_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = PlanningService(db)
    return await service.get_beam_control_points(beam_id)


# ---- Plan Workflow ----


@router.post(
    "/plans/{plan_id}/submit-for-review",
    response_model=TreatmentPlanResponse,
)
async def submit_for_review(
    plan_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = PlanningService(db)
    return await service.submit_for_review(plan_id)


@router.post("/plans/{plan_id}/review", response_model=TreatmentPlanResponse)
async def review_plan(
    plan_id: uuid.UUID,
    data: PlanApprovalRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = PlanningService(db)
    return await service.review_plan(
        plan_id=plan_id,
        reviewer_id=current_user.id,
        signature_id=data.signature_id,
    )


@router.post("/plans/{plan_id}/approve", response_model=TreatmentPlanResponse)
async def approve_plan(
    plan_id: uuid.UUID,
    data: PlanApprovalRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = PlanningService(db)
    return await service.approve_plan(
        plan_id=plan_id,
        approver_id=current_user.id,
        signature_id=data.signature_id,
    )


@router.post(
    "/plans/{plan_id}/physics-approve",
    response_model=TreatmentPlanResponse,
)
async def physics_approve_plan(
    plan_id: uuid.UUID,
    data: PlanApprovalRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = PlanningService(db)
    return await service.physics_approve_plan(
        plan_id=plan_id,
        approver_id=current_user.id,
        signature_id=data.signature_id,
    )
