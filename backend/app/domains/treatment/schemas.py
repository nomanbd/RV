import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


# --- Session ---
class SessionCreate(BaseModel):
    fraction_id: uuid.UUID
    patient_id: uuid.UUID
    machine_id: uuid.UUID
    plan_id: uuid.UUID
    tolerance_table_id: uuid.UUID
    primary_therapist_id: uuid.UUID | None = None
    secondary_therapist_id: uuid.UUID | None = None


class SessionResponse(BaseModel):
    id: uuid.UUID
    fraction_id: uuid.UUID
    patient_id: uuid.UUID
    machine_id: uuid.UUID
    plan_id: uuid.UUID
    tolerance_table_id: uuid.UUID
    status: str
    check_in_at: datetime | None
    setup_start_at: datetime | None
    imaging_start_at: datetime | None
    treatment_start_at: datetime | None
    treatment_end_at: datetime | None
    primary_therapist_id: uuid.UUID | None
    secondary_therapist_id: uuid.UUID | None
    supervising_physician_id: uuid.UUID | None
    patient_verified: bool
    patient_verified_by_id: uuid.UUID | None
    patient_verified_at: datetime | None
    verification_method: str | None
    imaging_performed: bool
    position_correction_applied: bool
    all_beams_verified: bool
    all_beams_delivered: bool
    session_notes: str | None
    rt_record_sop_uid: str | None
    rt_record_path: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SessionStatusUpdate(BaseModel):
    status: str = Field(
        pattern="^(scheduled|checked_in|setup|imaging|treatment|completed|interrupted|cancelled)$"
    )


# --- Beam Verification ---
class VerifyBeamRequest(BaseModel):
    beam_number: int
    actual_parameters: dict  # gantry_angle, collimator_angle, couch_angle, jaw_x1-y2, energy, dose_rate, mu, optional mlc_positions


class ParameterResultItem(BaseModel):
    name: str
    planned: str | None
    actual: str | None
    deviation: str | None
    tolerance: str | None
    result: str


class VerifyBeamResponse(BaseModel):
    overall_result: str
    parameter_results: list[ParameterResultItem]
    out_of_tolerance: list[ParameterResultItem]


# --- Beam Authorization ---
class AuthorizeBeamRequest(BaseModel):
    beam_number: int


# --- Delivery Recording ---
class RecordDeliveryRequest(BaseModel):
    beam_number: int
    actual_mu: float
    actual_gantry_angle: float | None = None
    actual_collimator_angle: float | None = None
    actual_couch_angle: float | None = None
    actual_energy: str | None = None
    actual_dose_rate: float | None = None
    actual_jaw_x1: float | None = None
    actual_jaw_x2: float | None = None
    actual_jaw_y1: float | None = None
    actual_jaw_y2: float | None = None
    actual_couch_vertical: float | None = None
    actual_couch_lateral: float | None = None
    actual_couch_longitudinal: float | None = None
    delivered_dose_cgy: float | None = None
    beam_on_at: datetime | None = None
    beam_off_at: datetime | None = None


class DeliveryRecordResponse(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    plan_beam_id: uuid.UUID
    beam_number: int
    verification_result: str
    verified_at: datetime | None
    verified_by_id: uuid.UUID | None
    override_reason: str | None
    override_approved_by_id: uuid.UUID | None
    planned_mu: float | None
    planned_gantry_angle: float | None
    planned_collimator_angle: float | None
    planned_couch_angle: float | None
    planned_energy: str | None
    planned_dose_rate: float | None
    planned_jaw_x1: float | None
    planned_jaw_x2: float | None
    planned_jaw_y1: float | None
    planned_jaw_y2: float | None
    actual_mu: float | None
    actual_gantry_angle: float | None
    actual_collimator_angle: float | None
    actual_couch_angle: float | None
    actual_energy: str | None
    actual_dose_rate: float | None
    actual_jaw_x1: float | None
    actual_jaw_x2: float | None
    actual_jaw_y1: float | None
    actual_jaw_y2: float | None
    actual_couch_vertical: float | None
    actual_couch_lateral: float | None
    actual_couch_longitudinal: float | None
    deviations: dict | None
    beam_on_at: datetime | None
    beam_off_at: datetime | None
    beam_hold_count: int
    beam_interrupted: bool
    interruption_reason: str | None
    delivered_dose_cgy: float | None
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Override ---
class OverrideRequest(BaseModel):
    beam_number: int
    reason: str
    signature_id: uuid.UUID


# --- Fraction ---
class FractionResponse(BaseModel):
    id: uuid.UUID
    prescription_id: uuid.UUID
    plan_id: uuid.UUID
    fraction_number: int
    status: str
    scheduled_date: date | None
    treated_date: date | None
    treated_by_id: uuid.UUID | None
    planned_dose_cgy: float | None
    delivered_dose_cgy: float | None
    cumulative_dose_cgy: float | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Dose Summary ---
class DoseSummaryResponse(BaseModel):
    patient_id: uuid.UUID
    total_prescribed_cgy: float
    total_delivered_cgy: float
    fractions_completed: int
    fractions_remaining: int


# --- Patient Verification ---
class VerifyPatientRequest(BaseModel):
    identifier1_type: str
    identifier1_value: str
    identifier2_type: str
    identifier2_value: str
    verification_method: str = "two_id"
