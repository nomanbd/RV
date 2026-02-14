import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


# --- Treatment Course ---


class TreatmentCourseCreate(BaseModel):
    patient_id: uuid.UUID
    course_number: int = Field(ge=1, default=1)
    intent: str = Field(pattern="^(curative|palliative|prophylactic|boost|sequential)$")
    diagnosis_id: uuid.UUID | None = None
    start_date: date | None = None
    notes: str | None = None


class TreatmentCourseResponse(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    course_number: int
    intent: str
    diagnosis_id: uuid.UUID | None
    start_date: date | None
    end_date: date | None
    status: str
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Prescription ---


class PrescriptionCreate(BaseModel):
    course_id: uuid.UUID
    site_name: str = Field(max_length=200)
    modality: str = Field(pattern="^(photon|electron|proton|brachy)$")
    technique: str = Field(
        pattern="^(3DCRT|IMRT|VMAT|SRS|SBRT|TBI|TSEI|electron)$"
    )
    total_dose_cgy: int = Field(gt=0)
    dose_per_fraction_cgy: int = Field(gt=0)
    num_fractions: int = Field(gt=0)
    energy: str | None = Field(None, max_length=20)
    prescribed_by_id: uuid.UUID
    notes: str | None = None


class PrescriptionResponse(BaseModel):
    id: uuid.UUID
    course_id: uuid.UUID
    site_name: str
    modality: str
    technique: str
    total_dose_cgy: int
    dose_per_fraction_cgy: int
    num_fractions: int
    fractions_per_week: int
    energy: str | None
    prescribed_by_id: uuid.UUID
    prescribed_at: datetime
    approved_by_id: uuid.UUID | None
    approved_at: datetime | None
    approval_signature_id: uuid.UUID | None
    notes: str | None
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Plan Beam ---


class BeamControlPointResponse(BaseModel):
    id: uuid.UUID
    beam_id: uuid.UUID
    control_point_index: int
    cumulative_meterset_weight: float | None
    gantry_angle: float | None
    gantry_rotation_direction: str | None
    collimator_angle: float | None
    jaw_x1: float | None
    jaw_x2: float | None
    jaw_y1: float | None
    jaw_y2: float | None
    mlc_positions: dict | None

    model_config = {"from_attributes": True}


class PlanBeamResponse(BaseModel):
    id: uuid.UUID
    plan_id: uuid.UUID
    beam_number: int
    beam_name: str | None
    beam_type: str
    radiation_type: str
    treatment_delivery_type: str | None
    energy_mev: float | None
    energy_label: str | None
    dose_rate_mu_per_min: float | None
    planned_mu: float | None
    num_control_points: int | None
    gantry_angle: float | None
    gantry_rotation: str | None
    collimator_angle: float | None
    couch_angle: float | None
    couch_vertical: float | None
    couch_lateral: float | None
    couch_longitudinal: float | None
    isocenter_x: float | None
    isocenter_y: float | None
    isocenter_z: float | None
    jaw_x1: float | None
    jaw_x2: float | None
    jaw_y1: float | None
    jaw_y2: float | None
    wedge_type: str | None
    wedge_angle: float | None
    bolus_description: str | None
    beam_sequence_order: int
    dicom_data: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Treatment Plan ---


class PlanImportResponse(BaseModel):
    id: uuid.UUID
    prescription_id: uuid.UUID
    course_id: uuid.UUID
    plan_label: str
    plan_name: str | None
    status: str
    version: int
    sop_instance_uid: str | None
    rt_plan_dicom_path: str | None
    frame_of_reference_uid: str | None
    plan_geometry: str | None
    num_beams: int | None
    num_fractions_planned: int | None
    created_by_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class TreatmentPlanResponse(BaseModel):
    id: uuid.UUID
    prescription_id: uuid.UUID
    course_id: uuid.UUID
    plan_label: str
    plan_name: str | None
    status: str
    version: int
    is_current: bool
    sop_instance_uid: str | None
    rt_plan_dicom_path: str | None
    rt_dose_sop_uid: str | None
    rt_struct_sop_uid: str | None
    frame_of_reference_uid: str | None
    plan_geometry: str | None
    treatment_machine_id: uuid.UUID | None
    num_beams: int | None
    num_fractions_planned: int | None
    dicom_metadata: dict | None
    created_by_id: uuid.UUID
    reviewed_by_id: uuid.UUID | None
    reviewed_at: datetime | None
    review_signature_id: uuid.UUID | None
    approved_by_id: uuid.UUID | None
    approved_at: datetime | None
    approval_signature_id: uuid.UUID | None
    physics_approved_by_id: uuid.UUID | None
    physics_approved_at: datetime | None
    physics_approval_signature_id: uuid.UUID | None
    beams: list[PlanBeamResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Plan Approval ---


class PlanApprovalRequest(BaseModel):
    signature_id: uuid.UUID
    comment: str | None = None


# --- Plan Version ---


class PlanVersionResponse(BaseModel):
    id: uuid.UUID
    plan_label: str
    version: int
    status: str
    is_current: bool
    created_by_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}
