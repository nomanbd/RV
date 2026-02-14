import uuid

from sqlalchemy import Boolean, Date, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TreatmentMachine(Base):
    __tablename__ = "treatment_machines"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    machine_type: Mapped[str] = mapped_column(
        Enum("linac", "cobalt", "cyberknife", "tomotherapy", "proton", name="machine_type", create_type=False),
        nullable=False,
    )
    manufacturer: Mapped[str | None] = mapped_column(String(100), nullable=True)
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    serial_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    institution_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    department: Mapped[str | None] = mapped_column(String(200), nullable=True)
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    dicom_ae_title: Mapped[str | None] = mapped_column(String(16), nullable=True)
    status: Mapped[str] = mapped_column(
        Enum("active", "maintenance", "decommissioned", name="machine_status", create_type=False),
        default="active", nullable=False,
    )
    available_energies: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    has_mlc: Mapped[bool] = mapped_column(Boolean, default=True)
    mlc_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    mlc_num_leaf_pairs: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mlc_leaf_widths: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    max_gantry_speed: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    max_dose_rate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    has_cbct: Mapped[bool] = mapped_column(Boolean, default=False)
    has_epid: Mapped[bool] = mapped_column(Boolean, default=False)
    has_kvkv: Mapped[bool] = mapped_column(Boolean, default=False)
    has_surface_guidance: Mapped[bool] = mapped_column(Boolean, default=False)
    last_qa_date: Mapped[str | None] = mapped_column(Date, nullable=True)
    next_qa_date: Mapped[str | None] = mapped_column(Date, nullable=True)
    commissioning_date: Mapped[str | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class ToleranceTable(Base):
    __tablename__ = "tolerance_tables"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    machine_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("treatment_machines.id"), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    gantry_angle_tol: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    collimator_angle_tol: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    couch_angle_tol: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    couch_vertical_tol: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    couch_lateral_tol: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    couch_longitudinal_tol: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    jaw_x1_tol: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    jaw_x2_tol: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    jaw_y1_tol: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    jaw_y2_tol: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    mlc_tol: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    energy_tol: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    dose_rate_tol: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    mu_tol: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    wedge_angle_tol: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    custom_tolerances: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    approved_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[str | None] = mapped_column(Date, nullable=True)
