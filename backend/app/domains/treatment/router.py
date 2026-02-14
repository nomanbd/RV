import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.domains.auth.models import User
from app.domains.treatment.schemas import (
    AuthorizeBeamRequest,
    DeliveryRecordResponse,
    DoseSummaryResponse,
    FractionResponse,
    OverrideRequest,
    RecordDeliveryRequest,
    SessionCreate,
    SessionResponse,
    SessionStatusUpdate,
    VerifyBeamRequest,
    VerifyBeamResponse,
    VerifyPatientRequest,
)
from app.domains.treatment.service import TreatmentService

router = APIRouter(prefix="/treatment", tags=["treatment"])


# --- Sessions ---

@router.post("/sessions", response_model=SessionResponse, status_code=201)
async def create_session(
    data: SessionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = TreatmentService(db)
    return await service.create_session(data)


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = TreatmentService(db)
    return await service.get_session(session_id)


@router.patch("/sessions/{session_id}/status", response_model=SessionResponse)
async def update_session_status(
    session_id: uuid.UUID,
    data: SessionStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = TreatmentService(db)
    return await service.update_session_status(session_id, data.status, current_user.id)


@router.post("/sessions/{session_id}/verify-patient", response_model=SessionResponse)
async def verify_patient(
    session_id: uuid.UUID,
    data: VerifyPatientRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = TreatmentService(db)
    return await service.verify_patient(session_id, data, current_user.id)


@router.post("/sessions/{session_id}/verify-beam", response_model=VerifyBeamResponse)
async def verify_beam(
    session_id: uuid.UUID,
    data: VerifyBeamRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = TreatmentService(db)
    result = await service.verify_beam(session_id, data)
    return result.to_dict()


@router.post("/sessions/{session_id}/authorize-beam", response_model=DeliveryRecordResponse)
async def authorize_beam(
    session_id: uuid.UUID,
    data: AuthorizeBeamRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = TreatmentService(db)
    return await service.authorize_beam(session_id, data.beam_number, current_user.id)


@router.post("/sessions/{session_id}/record-delivery", response_model=DeliveryRecordResponse)
async def record_delivery(
    session_id: uuid.UUID,
    data: RecordDeliveryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = TreatmentService(db)
    return await service.record_delivery(session_id, data)


@router.post("/sessions/{session_id}/override", response_model=DeliveryRecordResponse)
async def override_verification(
    session_id: uuid.UUID,
    data: OverrideRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = TreatmentService(db)
    return await service.override_verification(
        session_id, data.beam_number, data.reason, current_user.id, data.signature_id
    )


@router.post("/sessions/{session_id}/complete", response_model=SessionResponse)
async def complete_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = TreatmentService(db)
    return await service.complete_session(session_id, current_user.id)


@router.get(
    "/sessions/{session_id}/delivery-records",
    response_model=list[DeliveryRecordResponse],
)
async def list_delivery_records(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = TreatmentService(db)
    session = await service.get_session(session_id)
    return session.delivery_records


# --- Fractions ---

@router.get("/fractions/{fraction_id}", response_model=FractionResponse)
async def get_fraction(
    fraction_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select
    from app.domains.treatment.models import Fraction
    from app.core.exceptions import NotFoundError

    result = await db.execute(
        select(Fraction).where(Fraction.id == fraction_id)
    )
    fraction = result.scalar_one_or_none()
    if fraction is None:
        raise NotFoundError("Fraction not found")
    return fraction


# --- Dose Summary ---

@router.get("/patients/{patient_id}/dose-summary", response_model=DoseSummaryResponse)
async def get_dose_summary(
    patient_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = TreatmentService(db)
    return await service.get_dose_summary(patient_id)
