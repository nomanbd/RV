import uuid
from datetime import datetime

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TreatmentCourse(Base):
    __tablename__ = "treatment_courses"

    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True)
    course_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    intent: Mapped[str] = mapped_column(
        Enum("curative", "palliative", "prophylactic", "boost", "sequential", name="plan_intent", create_type=False),
        nullable=False,
    )
    diagnosis_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("patient_diagnoses.id"), nullable=True)
    start_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    prescriptions: Mapped[list["Prescription"]] = relationship(back_populates="course", lazy="selectin")


class Prescription(Base):
    __tablename__ = "prescriptions"

    course_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("treatment_courses.id"), nullable=False)
    site_name: Mapped[str] = mapped_column(String(200), nullable=False)
    modality: Mapped[str] = mapped_column(
        Enum("photon", "electron", "proton", "brachy", name="modality", create_type=False), nullable=False
    )
    technique: Mapped[str] = mapped_column(
        Enum("3DCRT", "IMRT", "VMAT", "SRS", "SBRT", "TBI", "TSEI", "electron", name="technique", create_type=False),
        nullable=False,
    )
    total_dose_cgy: Mapped[int] = mapped_column(Integer, nullable=False)
    dose_per_fraction_cgy: Mapped[int] = mapped_column(Integer, nullable=False)
    num_fractions: Mapped[int] = mapped_column(Integer, nullable=False)
    fractions_per_week: Mapped[int] = mapped_column(Integer, default=5)
    energy: Mapped[str | None] = mapped_column(String(20), nullable=True)
    prescribed_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    prescribed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    approved_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approval_signature_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("electronic_signatures.id"), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    course: Mapped["TreatmentCourse"] = relationship(back_populates="prescriptions")


class TreatmentPlan(Base):
    __tablename__ = "treatment_plans"

    prescription_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("prescriptions.id"), nullable=False, index=True)
    course_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("treatment_courses.id"), nullable=False)
    plan_label: Mapped[str] = mapped_column(String(100), nullable=False)
    plan_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(
        Enum("draft", "pending_review", "reviewed", "pending_approval", "approved", "superseded", "retired",
             name="plan_status", create_type=False),
        default="draft", nullable=False, index=True,
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True)

    # DICOM references
    sop_instance_uid: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True)
    rt_plan_dicom_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    rt_dose_sop_uid: Mapped[str | None] = mapped_column(String(128), nullable=True)
    rt_struct_sop_uid: Mapped[str | None] = mapped_column(String(128), nullable=True)
    frame_of_reference_uid: Mapped[str | None] = mapped_column(String(128), nullable=True)
    plan_geometry: Mapped[str | None] = mapped_column(String(50), nullable=True)
    treatment_machine_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("treatment_machines.id"), nullable=True
    )
    num_beams: Mapped[int | None] = mapped_column(Integer, nullable=True)
    num_fractions_planned: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dicom_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Approval tracking
    created_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    reviewed_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_signature_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("electronic_signatures.id"), nullable=True)
    approved_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approval_signature_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("electronic_signatures.id"), nullable=True)
    physics_approved_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    physics_approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    physics_approval_signature_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("electronic_signatures.id"), nullable=True)

    beams: Mapped[list["PlanBeam"]] = relationship(back_populates="plan", lazy="selectin", cascade="all, delete-orphan")


class PlanBeam(Base):
    __tablename__ = "plan_beams"

    plan_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("treatment_plans.id", ondelete="CASCADE"), nullable=False, index=True)
    beam_number: Mapped[int] = mapped_column(Integer, nullable=False)
    beam_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    beam_type: Mapped[str] = mapped_column(String(50), nullable=False)
    radiation_type: Mapped[str] = mapped_column(String(50), nullable=False)
    treatment_delivery_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    energy_mev: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    energy_label: Mapped[str | None] = mapped_column(String(20), nullable=True)
    dose_rate_mu_per_min: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    planned_mu: Mapped[float | None] = mapped_column(Numeric(12, 4), nullable=True)
    num_control_points: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gantry_angle: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    gantry_rotation: Mapped[str | None] = mapped_column(String(20), nullable=True)
    collimator_angle: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    couch_angle: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    couch_vertical: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    couch_lateral: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    couch_longitudinal: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    isocenter_x: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    isocenter_y: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    isocenter_z: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    jaw_x1: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    jaw_x2: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    jaw_y1: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    jaw_y2: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    wedge_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    wedge_angle: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    bolus_description: Mapped[str | None] = mapped_column(String(200), nullable=True)
    beam_sequence_order: Mapped[int] = mapped_column(Integer, nullable=False)
    dicom_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    plan: Mapped["TreatmentPlan"] = relationship(back_populates="beams")
    control_points: Mapped[list["BeamControlPoint"]] = relationship(back_populates="beam", lazy="selectin", cascade="all, delete-orphan")


class BeamControlPoint(Base):
    __tablename__ = "beam_control_points"

    beam_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("plan_beams.id", ondelete="CASCADE"), nullable=False, index=True)
    control_point_index: Mapped[int] = mapped_column(Integer, nullable=False)
    cumulative_meterset_weight: Mapped[float | None] = mapped_column(Numeric(12, 8), nullable=True)
    gantry_angle: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    gantry_rotation_direction: Mapped[str | None] = mapped_column(String(4), nullable=True)
    collimator_angle: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    jaw_x1: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    jaw_x2: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    jaw_y1: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    jaw_y2: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    mlc_positions: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    beam: Mapped["PlanBeam"] = relationship(back_populates="control_points")
