import uuid
from datetime import datetime

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, Time
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RTImage(Base):
    __tablename__ = "rt_images"

    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True)
    session_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("treatment_sessions.id"), nullable=True, index=True)
    sop_instance_uid: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    series_instance_uid: Mapped[str | None] = mapped_column(String(128), nullable=True)
    study_instance_uid: Mapped[str | None] = mapped_column(String(128), nullable=True)
    image_type: Mapped[str] = mapped_column(
        Enum("portal", "cbct", "kv_kv", "mv", "drr", "surface", name="image_type", create_type=False), nullable=False
    )
    acquisition_date: Mapped[str | None] = mapped_column(Date, nullable=True)
    acquisition_time: Mapped[str | None] = mapped_column(Time, nullable=True)
    machine_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("treatment_machines.id"), nullable=True)
    gantry_angle: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    beam_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    image_plane: Mapped[str | None] = mapped_column(String(50), nullable=True)
    rows: Mapped[int | None] = mapped_column(Integer, nullable=True)
    columns: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pixel_spacing: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    thumbnail_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    dicom_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    reviews: Mapped[list["ImageReview"]] = relationship(back_populates="image", lazy="selectin")


class ImageReview(Base):
    __tablename__ = "image_reviews"

    image_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("rt_images.id"), nullable=False)
    session_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("treatment_sessions.id"), nullable=True)
    reviewer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(
        Enum("pending", "reviewed", "approved", "rejected", name="image_review_status", create_type=False),
        default="pending", nullable=False,
    )
    shift_vertical_cm: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    shift_lateral_cm: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    shift_longitudinal_cm: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    rotation_pitch_deg: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    rotation_roll_deg: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    rotation_yaw_deg: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    shifts_applied: Mapped[bool] = mapped_column(Boolean, default=False)
    shifts_applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    shifts_applied_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    review_type: Mapped[str] = mapped_column(String(20), default="online", nullable=False)
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    signature_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("electronic_signatures.id"), nullable=True)
    reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    image: Mapped["RTImage"] = relationship(back_populates="reviews")
