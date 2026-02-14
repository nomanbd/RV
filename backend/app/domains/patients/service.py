import uuid
from datetime import date

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ConflictError, NotFoundError
from app.domains.patients.models import Patient, PatientAllergy, PatientDiagnosis
from app.domains.patients.schemas import (
    AllergyCreate,
    DiagnosisCreate,
    PatientCreate,
    PatientUpdate,
    TwoIdVerificationRequest,
    TwoIdVerificationResponse,
)


class PatientService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_patient(self, data: PatientCreate) -> Patient:
        # Check MRN uniqueness
        existing = await self.db.execute(select(Patient).where(Patient.mrn == data.mrn))
        if existing.scalar_one_or_none():
            raise ConflictError(f"Patient with MRN '{data.mrn}' already exists")

        patient = Patient(**data.model_dump())
        self.db.add(patient)
        await self.db.flush()
        return patient

    async def get_patient(self, patient_id: uuid.UUID) -> Patient:
        result = await self.db.execute(
            select(Patient)
            .options(
                selectinload(Patient.diagnoses),
                selectinload(Patient.allergies),
                selectinload(Patient.identifiers),
            )
            .where(Patient.id == patient_id)
        )
        patient = result.scalar_one_or_none()
        if patient is None:
            raise NotFoundError("Patient not found")
        return patient

    async def search_patients(
        self,
        q: str | None = None,
        mrn: str | None = None,
        name: str | None = None,
        date_of_birth: date | None = None,
        is_active: bool | None = True,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Patient]:
        query = select(Patient)

        if is_active is not None:
            query = query.where(Patient.is_active == is_active)

        if mrn:
            query = query.where(Patient.mrn.ilike(f"%{mrn}%"))

        if name:
            name_filter = f"%{name}%"
            query = query.where(
                or_(
                    Patient.first_name.ilike(name_filter),
                    Patient.last_name.ilike(name_filter),
                )
            )

        if date_of_birth:
            query = query.where(Patient.date_of_birth == date_of_birth)

        if q:
            q_filter = f"%{q}%"
            query = query.where(
                or_(
                    Patient.mrn.ilike(q_filter),
                    Patient.first_name.ilike(q_filter),
                    Patient.last_name.ilike(q_filter),
                    Patient.dicom_patient_id.ilike(q_filter),
                )
            )

        query = query.order_by(Patient.last_name, Patient.first_name).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_patient(self, patient_id: uuid.UUID, data: PatientUpdate) -> Patient:
        patient = await self.get_patient(patient_id)
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(patient, field, value)
        await self.db.flush()
        return patient

    async def verify_two_id(self, patient_id: uuid.UUID, data: TwoIdVerificationRequest) -> TwoIdVerificationResponse:
        """Two-identifier patient verification for treatment safety."""
        patient = await self.get_patient(patient_id)

        checks = {
            data.identifier1_type: data.identifier1_value,
            data.identifier2_type: data.identifier2_value,
        }

        if len(checks) < 2:
            return TwoIdVerificationResponse(
                verified=False, message="Two different identifier types are required"
            )

        verified = True
        for id_type, id_value in checks.items():
            if id_type == "mrn":
                if patient.mrn.lower() != id_value.lower():
                    verified = False
                    break
            elif id_type == "date_of_birth":
                try:
                    dob = date.fromisoformat(id_value)
                    if patient.date_of_birth != dob:
                        verified = False
                        break
                except ValueError:
                    verified = False
                    break
            elif id_type == "full_name":
                if patient.full_name.lower() != id_value.lower():
                    verified = False
                    break
            else:
                # Check patient_identifiers table
                found = False
                for identifier in patient.identifiers:
                    if identifier.identifier_type == id_type and identifier.identifier_value == id_value:
                        found = True
                        break
                if not found:
                    verified = False
                    break

        return TwoIdVerificationResponse(
            verified=verified,
            patient_id=patient.id if verified else None,
            patient_name=patient.full_name if verified else None,
            message="Patient identity verified" if verified else "Verification failed - identifiers do not match",
        )

    async def add_diagnosis(self, patient_id: uuid.UUID, data: DiagnosisCreate) -> PatientDiagnosis:
        await self.get_patient(patient_id)  # Verify patient exists
        diagnosis = PatientDiagnosis(patient_id=patient_id, **data.model_dump())
        self.db.add(diagnosis)
        await self.db.flush()
        return diagnosis

    async def add_allergy(self, patient_id: uuid.UUID, data: AllergyCreate) -> PatientAllergy:
        await self.get_patient(patient_id)  # Verify patient exists
        allergy = PatientAllergy(patient_id=patient_id, **data.model_dump())
        self.db.add(allergy)
        await self.db.flush()
        return allergy
