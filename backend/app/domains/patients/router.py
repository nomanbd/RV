import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.domains.auth.models import User
from app.domains.patients.schemas import (
    AllergyCreate,
    AllergyResponse,
    DiagnosisCreate,
    DiagnosisResponse,
    PatientCreate,
    PatientDetailResponse,
    PatientResponse,
    PatientUpdate,
    TwoIdVerificationRequest,
    TwoIdVerificationResponse,
)
from app.domains.patients.service import PatientService

router = APIRouter(prefix="/patients", tags=["patients"])


@router.get("", response_model=list[PatientResponse])
async def list_patients(
    q: str | None = None,
    mrn: str | None = None,
    name: str | None = None,
    date_of_birth: date | None = None,
    is_active: bool | None = True,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = PatientService(db)
    return await service.search_patients(
        q=q, mrn=mrn, name=name, date_of_birth=date_of_birth, is_active=is_active, skip=skip, limit=limit
    )


@router.post("", response_model=PatientDetailResponse, status_code=201)
async def create_patient(
    data: PatientCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = PatientService(db)
    return await service.create_patient(data)


@router.get("/{patient_id}", response_model=PatientDetailResponse)
async def get_patient(
    patient_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = PatientService(db)
    return await service.get_patient(patient_id)


@router.put("/{patient_id}", response_model=PatientDetailResponse)
async def update_patient(
    patient_id: uuid.UUID,
    data: PatientUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = PatientService(db)
    return await service.update_patient(patient_id, data)


@router.post("/{patient_id}/verify", response_model=TwoIdVerificationResponse)
async def verify_patient(
    patient_id: uuid.UUID,
    data: TwoIdVerificationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = PatientService(db)
    return await service.verify_two_id(patient_id, data)


@router.post("/{patient_id}/diagnoses", response_model=DiagnosisResponse, status_code=201)
async def add_diagnosis(
    patient_id: uuid.UUID,
    data: DiagnosisCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = PatientService(db)
    return await service.add_diagnosis(patient_id, data)


@router.post("/{patient_id}/allergies", response_model=AllergyResponse, status_code=201)
async def add_allergy(
    patient_id: uuid.UUID,
    data: AllergyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = PatientService(db)
    return await service.add_allergy(patient_id, data)
