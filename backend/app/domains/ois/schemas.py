import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# --- OIS Connection ---
class OISConnectionCreate(BaseModel):
    name: str = Field(max_length=200)
    ois_type: str = Field(pattern="^(aria|raycare|generic_fhir)$")
    base_url: str = Field(max_length=500)
    auth_type: str = Field(default="oauth2", pattern="^(basic|oauth2|api_key|certificate)$")
    client_id: str | None = None
    client_secret: str | None = None
    api_key: str | None = None
    username: str | None = None
    password: str | None = None
    certificate_path: str | None = None
    fhir_base_url: str | None = None
    dicom_ae_title: str | None = None
    dicom_host: str | None = None
    dicom_port: int | None = None
    is_primary: bool = False
    settings: dict | None = None


class OISConnectionUpdate(BaseModel):
    name: str | None = None
    base_url: str | None = None
    auth_type: str | None = None
    client_id: str | None = None
    client_secret: str | None = None
    api_key: str | None = None
    username: str | None = None
    password: str | None = None
    certificate_path: str | None = None
    fhir_base_url: str | None = None
    dicom_ae_title: str | None = None
    dicom_host: str | None = None
    dicom_port: int | None = None
    is_active: bool | None = None
    is_primary: bool | None = None
    settings: dict | None = None


class OISConnectionResponse(BaseModel):
    id: uuid.UUID
    name: str
    ois_type: str
    base_url: str
    auth_type: str
    fhir_base_url: str | None
    dicom_ae_title: str | None
    dicom_host: str | None
    dicom_port: int | None
    is_active: bool
    is_primary: bool
    last_connected_at: datetime | None
    connection_status: str
    settings: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}


class OISConnectionTestResult(BaseModel):
    success: bool
    message: str
    response_time_ms: float | None = None
    ois_version: str | None = None
    capabilities: list[str] = []


# --- Patient Lookup ---
class OISPatientLookupRequest(BaseModel):
    mrn: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    date_of_birth: str | None = None


class OISPatientResult(BaseModel):
    external_id: str
    mrn: str
    first_name: str
    last_name: str
    middle_name: str | None = None
    date_of_birth: str | None = None
    sex: str | None = None
    diagnoses: list[dict] = []
    courses: list[dict] = []
    source_system: str


class OISPatientImportResult(BaseModel):
    success: bool
    local_patient_id: uuid.UUID | None = None
    message: str
    imported_courses: int = 0
    imported_plans: int = 0


# --- Plan Import ---
class OISPlanResult(BaseModel):
    external_id: str
    plan_label: str
    plan_type: str | None = None
    status: str | None = None
    modality: str | None = None
    technique: str | None = None
    num_beams: int = 0
    prescribed_dose_cgy: float | None = None
    num_fractions: int | None = None
    approval_status: str | None = None
    created_date: str | None = None
    source_system: str


class OISPlanImportRequest(BaseModel):
    connection_id: uuid.UUID
    external_patient_id: str
    external_plan_id: str
    local_patient_id: uuid.UUID
    local_course_id: uuid.UUID | None = None


# --- Schedule Sync ---
class OISAppointmentResult(BaseModel):
    external_id: str
    patient_mrn: str
    patient_name: str
    scheduled_start: datetime
    scheduled_end: datetime | None = None
    appointment_type: str
    machine_name: str | None = None
    status: str
    source_system: str


class OISScheduleSyncRequest(BaseModel):
    connection_id: uuid.UUID
    date_from: str
    date_to: str
    machine_name: str | None = None


class OISScheduleSyncResult(BaseModel):
    success: bool
    message: str
    appointments_synced: int = 0
    appointments_created: int = 0
    appointments_updated: int = 0
    conflicts: list[dict] = []


# --- Treatment Record Export ---
class OISRecordExportRequest(BaseModel):
    connection_id: uuid.UUID
    session_id: uuid.UUID


class OISRecordExportResult(BaseModel):
    success: bool
    message: str
    external_record_id: str | None = None


# --- Sync Logs ---
class OISSyncLogResponse(BaseModel):
    id: uuid.UUID
    connection_id: uuid.UUID
    operation: str
    entity_type: str | None
    entity_id: str | None
    status: str
    message: str | None
    records_processed: int
    records_failed: int
    duration_ms: float | None
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Sync Status ---
class OISSyncStatusResponse(BaseModel):
    connection_id: uuid.UUID
    connection_name: str
    ois_type: str
    is_active: bool
    connection_status: str
    last_connected_at: datetime | None
    total_mapped_patients: int = 0
    total_mapped_plans: int = 0
    total_mapped_appointments: int = 0
    recent_syncs: list[OISSyncLogResponse] = []
