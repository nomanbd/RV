import uuid
from datetime import datetime

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Fraction(Base):
    __tablename__ = "fractions"

    prescription_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("prescriptions.id"), nullable=False, index=True)
    plan_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("treatment_plans.id"), nullable=False)
    fraction_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        Enum("scheduled", "in_progress", "completed", "partially_treated", "not_treated", "cancelled",
             name="fraction_status", create_type=False),
        default="scheduled", nullable=False,
    )
    scheduled_date: Mapped[str | None] = mapped_column(Date, nullable=True)
    treated_date: Mapped[str | None] = mapped_column(Date, nullable=True)
    treated_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    planned_dose_cgy: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    delivered_dose_cgy: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    cumulative_dose_cgy: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    sessions: Mapped[list["TreatmentSession"]] = relationship(back_populates="fraction", lazy="selectin")


class TreatmentSession(Base):
    __tablename__ = "treatment_sessions"

    fraction_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("fractions.id"), nullable=False, index=True)
    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True)
    machine_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("treatment_machines.id"), nullable=False)
    plan_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("treatment_plans.id"), nullable=False)
    tolerance_table_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tolerance_tables.id"), nullable=False)
    status: Mapped[str] = mapped_column(
        Enum("scheduled", "checked_in", "setup", "imaging", "treatment", "completed", "cancelled", "interrupted",
             name="session_status", create_type=False),
        default="scheduled", nullable=False,
    )
    # Timestamps
    check_in_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    setup_start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    imaging_start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    treatment_start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    treatment_end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Staff
    primary_therapist_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    secondary_therapist_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    supervising_physician_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    # Patient verification
    patient_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    patient_verified_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    patient_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verification_method: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # Image guidance
    imaging_performed: Mapped[bool] = mapped_column(Boolean, default=False)
    position_correction_applied: Mapped[bool] = mapped_column(Boolean, default=False)
    # Overall
    all_beams_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    all_beams_delivered: Mapped[bool] = mapped_column(Boolean, default=False)
    session_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    rt_record_sop_uid: Mapped[str | None] = mapped_column(String(128), nullable=True)
    rt_record_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    fraction: Mapped["Fraction"] = relationship(back_populates="sessions")
    delivery_records: Mapped[list["BeamDeliveryRecord"]] = relationship(back_populates="session", lazy="selectin", cascade="all, delete-orphan")


class BeamDeliveryRecord(Base):
    __tablename__ = "beam_delivery_records"

    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("treatment_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    plan_beam_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("plan_beams.id"), nullable=False)
    beam_number: Mapped[int] = mapped_column(Integer, nullable=False)
    # Verification
    verification_result: Mapped[str] = mapped_column(
        Enum("pass", "fail", "override", name="verification_result", create_type=False), nullable=False
    )
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    override_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    override_approved_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    # Planned values
    planned_mu: Mapped[float | None] = mapped_column(Numeric(12, 4), nullable=True)
    planned_gantry_angle: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    planned_collimator_angle: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    planned_couch_angle: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    planned_energy: Mapped[str | None] = mapped_column(String(20), nullable=True)
    planned_dose_rate: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    planned_jaw_x1: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    planned_jaw_x2: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    planned_jaw_y1: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    planned_jaw_y2: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    # Actual delivered values
    actual_mu: Mapped[float | None] = mapped_column(Numeric(12, 4), nullable=True)
    actual_gantry_angle: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    actual_collimator_angle: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    actual_couch_angle: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    actual_energy: Mapped[str | None] = mapped_column(String(20), nullable=True)
    actual_dose_rate: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    actual_jaw_x1: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    actual_jaw_x2: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    actual_jaw_y1: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    actual_jaw_y2: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    actual_couch_vertical: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    actual_couch_lateral: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    actual_couch_longitudinal: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    # Deviations
    deviations: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # Beam timing
    beam_on_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    beam_off_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    beam_hold_count: Mapped[int] = mapped_column(Integer, default=0)
    beam_interrupted: Mapped[bool] = mapped_column(Boolean, default=False)
    interruption_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    delivered_dose_cgy: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)

    session: Mapped["TreatmentSession"] = relationship(back_populates="delivery_records")
