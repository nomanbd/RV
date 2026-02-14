import uuid
from datetime import date, datetime, time

from pydantic import BaseModel


# --- Image ---
class ImageResponse(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    session_id: uuid.UUID | None
    sop_instance_uid: str
    series_instance_uid: str | None
    study_instance_uid: str | None
    image_type: str
    acquisition_date: date | None
    acquisition_time: time | None
    machine_id: uuid.UUID | None
    gantry_angle: float | None
    beam_name: str | None
    image_plane: str | None
    rows: int | None
    columns: int | None
    pixel_spacing: list | None
    file_path: str
    file_size_bytes: int | None
    thumbnail_path: str | None
    dicom_metadata: dict | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Image Review ---
class ImageReviewCreate(BaseModel):
    image_id: uuid.UUID
    shift_vertical_cm: float | None = None
    shift_lateral_cm: float | None = None
    shift_longitudinal_cm: float | None = None
    rotation_pitch_deg: float | None = None
    rotation_roll_deg: float | None = None
    rotation_yaw_deg: float | None = None
    review_type: str = "online"
    comments: str | None = None


class ImageReviewResponse(BaseModel):
    id: uuid.UUID
    image_id: uuid.UUID
    session_id: uuid.UUID | None
    reviewer_id: uuid.UUID
    status: str
    shift_vertical_cm: float | None
    shift_lateral_cm: float | None
    shift_longitudinal_cm: float | None
    rotation_pitch_deg: float | None
    rotation_roll_deg: float | None
    rotation_yaw_deg: float | None
    shifts_applied: bool
    shifts_applied_at: datetime | None
    shifts_applied_by_id: uuid.UUID | None
    review_type: str
    comments: str | None
    signature_id: uuid.UUID | None
    reviewed_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
