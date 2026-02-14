import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


# --- Patient ---
class PatientCreate(BaseModel):
    mrn: str = Field(max_length=50)
    first_name: str = Field(max_length=100)
    middle_name: str | None = None
    last_name: str = Field(max_length=100)
    date_of_birth: date
    sex: str = Field(pattern="^(male|female|other|unknown)$")
    phone_primary: str | None = None
    phone_secondary: str | None = None
    email: str | None = None
    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    country: str = "US"
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None
    primary_oncologist_id: uuid.UUID | None = None
    dicom_patient_id: str | None = None
    notes: str | None = None


class PatientUpdate(BaseModel):
    first_name: str | None = None
    middle_name: str | None = None
    last_name: str | None = None
    phone_primary: str | None = None
    phone_secondary: str | None = None
    email: str | None = None
    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None
    primary_oncologist_id: uuid.UUID | None = None
    notes: str | None = None


class PatientResponse(BaseModel):
    id: uuid.UUID
    mrn: str
    first_name: str
    middle_name: str | None
    last_name: str
    date_of_birth: date
    sex: str
    phone_primary: str | None
    email: str | None
    address_line1: str | None
    city: str | None
    state: str | None
    postal_code: str | None
    country: str
    primary_oncologist_id: uuid.UUID | None
    is_active: bool
    dicom_patient_id: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class PatientDetailResponse(PatientResponse):
    middle_name: str | None
    phone_secondary: str | None
    address_line2: str | None
    emergency_contact_name: str | None
    emergency_contact_phone: str | None
    photo_path: str | None
    notes: str | None
    diagnoses: list["DiagnosisResponse"] = []
    allergies: list["AllergyResponse"] = []

    model_config = {"from_attributes": True}


class PatientSearchParams(BaseModel):
    q: str | None = None
    mrn: str | None = None
    name: str | None = None
    date_of_birth: date | None = None
    is_active: bool | None = True


# --- Two-ID Verification ---
class TwoIdVerificationRequest(BaseModel):
    identifier1_type: str  # 'mrn', 'date_of_birth', 'full_name', 'photo_id'
    identifier1_value: str
    identifier2_type: str
    identifier2_value: str


class TwoIdVerificationResponse(BaseModel):
    verified: bool
    patient_id: uuid.UUID | None = None
    patient_name: str | None = None
    message: str


# --- Diagnosis ---
class DiagnosisCreate(BaseModel):
    icd10_code: str = Field(max_length=20)
    description: str
    diagnosis_date: date | None = None
    site: str | None = None
    laterality: str | None = Field(None, pattern="^(left|right|bilateral)?$")
    is_primary: bool = False


class DiagnosisResponse(BaseModel):
    id: uuid.UUID
    icd10_code: str
    description: str
    diagnosis_date: date | None
    site: str | None
    laterality: str | None
    is_primary: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Allergy ---
class AllergyCreate(BaseModel):
    allergen: str = Field(max_length=200)
    reaction: str | None = None
    severity: str | None = None


class AllergyResponse(BaseModel):
    id: uuid.UUID
    allergen: str
    reaction: str | None
    severity: str | None

    model_config = {"from_attributes": True}
