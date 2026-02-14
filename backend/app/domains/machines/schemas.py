import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


# --- Machine ---
class MachineCreate(BaseModel):
    name: str = Field(max_length=100)
    machine_type: str = Field(pattern="^(linac|cobalt|cyberknife|tomotherapy|proton)$")
    manufacturer: str | None = None
    model: str | None = None
    serial_number: str | None = None
    institution_name: str | None = None
    location: str | None = None
    dicom_ae_title: str | None = Field(None, max_length=16)
    available_energies: list[str] | None = None
    has_mlc: bool = True
    mlc_model: str | None = None
    mlc_num_leaf_pairs: int | None = None
    has_cbct: bool = False
    has_epid: bool = False
    max_dose_rate: int | None = None


class MachineUpdate(BaseModel):
    name: str | None = None
    manufacturer: str | None = None
    model: str | None = None
    serial_number: str | None = None
    institution_name: str | None = None
    location: str | None = None
    dicom_ae_title: str | None = Field(None, max_length=16)
    available_energies: list[str] | None = None
    has_mlc: bool | None = None
    mlc_model: str | None = None
    mlc_num_leaf_pairs: int | None = None
    has_cbct: bool | None = None
    has_epid: bool | None = None
    max_dose_rate: int | None = None


class MachineResponse(BaseModel):
    id: uuid.UUID
    name: str
    machine_type: str
    manufacturer: str | None
    model: str | None
    serial_number: str | None
    institution_name: str | None
    department: str | None
    location: str | None
    dicom_ae_title: str | None
    status: str
    available_energies: list | None
    has_mlc: bool
    mlc_model: str | None
    mlc_num_leaf_pairs: int | None
    mlc_leaf_widths: list | None
    max_gantry_speed: float | None
    max_dose_rate: int | None
    has_cbct: bool
    has_epid: bool
    has_kvkv: bool
    has_surface_guidance: bool
    last_qa_date: date | None
    next_qa_date: date | None
    commissioning_date: date | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Tolerance Table ---
class ToleranceTableCreate(BaseModel):
    name: str = Field(max_length=100)
    machine_id: uuid.UUID | None = None
    description: str | None = None
    is_default: bool = False
    gantry_angle_tol: float | None = None
    collimator_angle_tol: float | None = None
    couch_angle_tol: float | None = None
    couch_vertical_tol: float | None = None
    couch_lateral_tol: float | None = None
    couch_longitudinal_tol: float | None = None
    jaw_x1_tol: float | None = None
    jaw_x2_tol: float | None = None
    jaw_y1_tol: float | None = None
    jaw_y2_tol: float | None = None
    mlc_tol: float | None = None
    energy_tol: float | None = None
    dose_rate_tol: float | None = None
    mu_tol: float | None = None
    wedge_angle_tol: float | None = None
    custom_tolerances: dict | None = None
    created_by_id: uuid.UUID


class ToleranceTableUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    is_default: bool | None = None
    gantry_angle_tol: float | None = None
    collimator_angle_tol: float | None = None
    couch_angle_tol: float | None = None
    couch_vertical_tol: float | None = None
    couch_lateral_tol: float | None = None
    couch_longitudinal_tol: float | None = None
    jaw_x1_tol: float | None = None
    jaw_x2_tol: float | None = None
    jaw_y1_tol: float | None = None
    jaw_y2_tol: float | None = None
    mlc_tol: float | None = None
    energy_tol: float | None = None
    dose_rate_tol: float | None = None
    mu_tol: float | None = None
    wedge_angle_tol: float | None = None
    custom_tolerances: dict | None = None


class ToleranceTableResponse(BaseModel):
    id: uuid.UUID
    name: str
    machine_id: uuid.UUID | None
    description: str | None
    is_default: bool
    gantry_angle_tol: float | None
    collimator_angle_tol: float | None
    couch_angle_tol: float | None
    couch_vertical_tol: float | None
    couch_lateral_tol: float | None
    couch_longitudinal_tol: float | None
    jaw_x1_tol: float | None
    jaw_x2_tol: float | None
    jaw_y1_tol: float | None
    jaw_y2_tol: float | None
    mlc_tol: float | None
    energy_tol: float | None
    dose_rate_tol: float | None
    mu_tol: float | None
    wedge_angle_tol: float | None
    custom_tolerances: dict | None
    created_by_id: uuid.UUID
    approved_by_id: uuid.UUID | None
    approved_at: date | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
