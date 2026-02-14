import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class OISConnection(Base):
    """Configuration for an external OIS system (Aria, RayCare, etc.)."""

    __tablename__ = "ois_connections"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    ois_type: Mapped[str] = mapped_column(
        Enum("aria", "raycare", "generic_fhir", name="ois_type_enum", create_type=False),
        nullable=False,
    )
    base_url: Mapped[str] = mapped_column(String(500), nullable=False)
    auth_type: Mapped[str] = mapped_column(
        Enum("basic", "oauth2", "api_key", "certificate", name="ois_auth_type_enum", create_type=False),
        nullable=False,
        default="oauth2",
    )
    client_id: Mapped[str | None] = mapped_column(String(500), nullable=True)
    client_secret_encrypted: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    api_key_encrypted: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    username: Mapped[str | None] = mapped_column(String(200), nullable=True)
    password_encrypted: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    certificate_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    fhir_base_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    dicom_ae_title: Mapped[str | None] = mapped_column(String(64), nullable=True)
    dicom_host: Mapped[str | None] = mapped_column(String(255), nullable=True)
    dicom_port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    last_connected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    connection_status: Mapped[str] = mapped_column(String(50), default="disconnected")
    settings: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    sync_mappings: Mapped[list["OISSyncMapping"]] = relationship(back_populates="connection", lazy="selectin")
    sync_logs: Mapped[list["OISSyncLog"]] = relationship(back_populates="connection", lazy="noload")


class OISSyncMapping(Base):
    """Maps local entities to external OIS identifiers for bidirectional sync."""

    __tablename__ = "ois_sync_mappings"

    connection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ois_connections.id", ondelete="CASCADE"), nullable=False
    )
    entity_type: Mapped[str] = mapped_column(
        Enum("patient", "plan", "course", "prescription", "appointment", "machine", name="ois_entity_type_enum", create_type=False),
        nullable=False,
    )
    local_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    external_id: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    external_mrn: Mapped[str | None] = mapped_column(String(100), nullable=True)
    sync_direction: Mapped[str] = mapped_column(
        Enum("inbound", "outbound", "bidirectional", name="ois_sync_direction_enum", create_type=False),
        default="bidirectional",
    )
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sync_status: Mapped[str] = mapped_column(String(50), default="pending")
    sync_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    connection: Mapped["OISConnection"] = relationship(back_populates="sync_mappings")


class OISSyncLog(Base):
    """Audit log for OIS synchronization operations."""

    __tablename__ = "ois_sync_logs"

    connection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ois_connections.id", ondelete="CASCADE"), nullable=False
    )
    operation: Mapped[str] = mapped_column(
        Enum("pull", "push", "test", "patient_lookup", "plan_import", "schedule_sync", "record_export",
             name="ois_operation_enum", create_type=False),
        nullable=False,
    )
    entity_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    entity_id: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(
        Enum("success", "failure", "partial", "skipped", name="ois_sync_status_enum", create_type=False),
        nullable=False,
    )
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    records_processed: Mapped[int] = mapped_column(Integer, default=0)
    records_failed: Mapped[int] = mapped_column(Integer, default=0)
    duration_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    initiated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    connection: Mapped["OISConnection"] = relationship(back_populates="sync_logs")
