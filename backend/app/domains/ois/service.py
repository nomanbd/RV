"""OIS integration service.

Coordinates all OIS operations: connection management, patient lookups,
plan imports, schedule synchronization, and treatment record exports.
Uses the adapter pattern to support multiple OIS backends (Aria, RayCare, FHIR).
"""

import hashlib
import json
import time
import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.domains.ois.adapters.aria import AriaAdapter
from app.domains.ois.adapters.base import OISAdapter
from app.domains.ois.adapters.fhir_client import FHIRAdapter
from app.domains.ois.adapters.raycare import RayCareAdapter
from app.domains.ois.models import OISConnection, OISSyncLog, OISSyncMapping
from app.domains.ois.schemas import (
    OISConnectionCreate,
    OISConnectionTestResult,
    OISConnectionUpdate,
    OISPatientImportResult,
    OISPatientLookupRequest,
    OISPatientResult,
    OISPlanResult,
    OISRecordExportResult,
    OISScheduleSyncResult,
    OISSyncStatusResponse,
)


class OISService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Connection Management ─────────────────────────────────────────

    async def create_connection(self, data: OISConnectionCreate) -> OISConnection:
        conn = OISConnection(
            name=data.name,
            ois_type=data.ois_type,
            base_url=data.base_url,
            auth_type=data.auth_type,
            client_id=data.client_id,
            client_secret_encrypted=data.client_secret,  # TODO: encrypt in production
            api_key_encrypted=data.api_key,
            username=data.username,
            password_encrypted=data.password,
            certificate_path=data.certificate_path,
            fhir_base_url=data.fhir_base_url,
            dicom_ae_title=data.dicom_ae_title,
            dicom_host=data.dicom_host,
            dicom_port=data.dicom_port,
            is_primary=data.is_primary,
            settings=data.settings,
        )

        # If marking as primary, unset other primary connections
        if data.is_primary:
            await self._unset_other_primary(None)

        self.db.add(conn)
        await self.db.flush()
        return conn

    async def update_connection(self, connection_id: uuid.UUID, data: OISConnectionUpdate) -> OISConnection:
        conn = await self._get_connection(connection_id)
        update_data = data.model_dump(exclude_unset=True)

        # Map secret fields
        secret_map = {
            "client_secret": "client_secret_encrypted",
            "api_key": "api_key_encrypted",
            "password": "password_encrypted",
        }
        for field, db_field in secret_map.items():
            if field in update_data:
                update_data[db_field] = update_data.pop(field)

        if update_data.get("is_primary"):
            await self._unset_other_primary(connection_id)

        for field, value in update_data.items():
            setattr(conn, field, value)
        await self.db.flush()
        return conn

    async def list_connections(self, active_only: bool = False) -> list[OISConnection]:
        query = select(OISConnection).order_by(OISConnection.is_primary.desc(), OISConnection.name)
        if active_only:
            query = query.where(OISConnection.is_active.is_(True))
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_connection(self, connection_id: uuid.UUID) -> OISConnection:
        return await self._get_connection(connection_id)

    async def delete_connection(self, connection_id: uuid.UUID) -> None:
        conn = await self._get_connection(connection_id)
        await self.db.delete(conn)
        await self.db.flush()

    async def test_connection(self, connection_id: uuid.UUID) -> OISConnectionTestResult:
        conn = await self._get_connection(connection_id)
        adapter = self._create_adapter(conn)
        start = time.time()

        try:
            result = await adapter.test_connection()
            duration_ms = (time.time() - start) * 1000

            # Update connection status
            conn.connection_status = "connected" if result.success else "error"
            if result.success:
                conn.last_connected_at = datetime.now(timezone.utc)
            await self.db.flush()

            # Log the test
            await self._log_sync(
                connection_id=conn.id,
                operation="test",
                status="success" if result.success else "failure",
                message=result.message,
                duration_ms=duration_ms,
            )

            return result
        except Exception as e:
            conn.connection_status = "error"
            await self.db.flush()
            return OISConnectionTestResult(
                success=False,
                message=f"Test failed: {str(e)}",
            )
        finally:
            await adapter.close()

    # ── Patient Operations ────────────────────────────────────────────

    async def lookup_patients(
        self, connection_id: uuid.UUID, lookup: OISPatientLookupRequest,
    ) -> list[OISPatientResult]:
        conn = await self._get_connection(connection_id)
        adapter = self._create_adapter(conn)
        start = time.time()

        try:
            results = await adapter.search_patients(
                mrn=lookup.mrn,
                last_name=lookup.last_name,
                first_name=lookup.first_name,
                date_of_birth=lookup.date_of_birth,
            )
            duration_ms = (time.time() - start) * 1000

            await self._log_sync(
                connection_id=conn.id,
                operation="patient_lookup",
                status="success",
                message=f"Found {len(results)} patients",
                records_processed=len(results),
                duration_ms=duration_ms,
            )
            return results
        except Exception as e:
            await self._log_sync(
                connection_id=conn.id,
                operation="patient_lookup",
                status="failure",
                message=str(e),
            )
            raise ValidationError(f"Patient lookup failed: {str(e)}")
        finally:
            await adapter.close()

    async def import_patient(
        self,
        connection_id: uuid.UUID,
        external_id: str,
        user_id: uuid.UUID | None = None,
    ) -> OISPatientImportResult:
        """Import a patient from the OIS into the local database."""
        conn = await self._get_connection(connection_id)
        adapter = self._create_adapter(conn)
        start = time.time()

        try:
            ois_patient = await adapter.get_patient(external_id)
            if ois_patient is None:
                return OISPatientImportResult(
                    success=False,
                    message=f"Patient {external_id} not found in {conn.ois_type}",
                )

            # Check if already mapped
            existing = await self.db.execute(
                select(OISSyncMapping).where(
                    OISSyncMapping.connection_id == conn.id,
                    OISSyncMapping.entity_type == "patient",
                    OISSyncMapping.external_id == external_id,
                )
            )
            existing_mapping = existing.scalar_one_or_none()
            if existing_mapping:
                return OISPatientImportResult(
                    success=True,
                    local_patient_id=existing_mapping.local_id,
                    message=f"Patient already imported (mapped to {existing_mapping.local_id})",
                )

            # Create local patient
            from app.domains.patients.models import Patient

            # Check if patient with same MRN already exists
            mrn_check = await self.db.execute(
                select(Patient).where(Patient.mrn == ois_patient.mrn)
            )
            existing_patient = mrn_check.scalar_one_or_none()

            if existing_patient:
                local_patient_id = existing_patient.id
                message = f"Linked to existing patient with MRN {ois_patient.mrn}"
            else:
                sex_value = ois_patient.sex if ois_patient.sex in ("male", "female", "other", "unknown") else "unknown"
                patient = Patient(
                    mrn=ois_patient.mrn,
                    first_name=ois_patient.first_name,
                    last_name=ois_patient.last_name,
                    middle_name=ois_patient.middle_name,
                    date_of_birth=ois_patient.date_of_birth,
                    sex=sex_value,
                    dicom_patient_id=ois_patient.mrn,
                    notes=f"Imported from {conn.ois_type.upper()} ({conn.name})",
                )
                self.db.add(patient)
                await self.db.flush()
                local_patient_id = patient.id
                message = f"Patient imported from {conn.ois_type.upper()}"

            # Create sync mapping
            mapping = OISSyncMapping(
                connection_id=conn.id,
                entity_type="patient",
                local_id=local_patient_id,
                external_id=external_id,
                external_mrn=ois_patient.mrn,
                sync_direction="bidirectional",
                last_synced_at=datetime.now(timezone.utc),
                sync_status="synced",
                sync_hash=self._compute_hash(ois_patient.model_dump()),
            )
            self.db.add(mapping)
            await self.db.flush()

            duration_ms = (time.time() - start) * 1000
            await self._log_sync(
                connection_id=conn.id,
                operation="pull",
                entity_type="patient",
                entity_id=external_id,
                status="success",
                message=message,
                records_processed=1,
                duration_ms=duration_ms,
                initiated_by=user_id,
            )

            return OISPatientImportResult(
                success=True,
                local_patient_id=local_patient_id,
                message=message,
            )
        except Exception as e:
            await self._log_sync(
                connection_id=conn.id,
                operation="pull",
                entity_type="patient",
                entity_id=external_id,
                status="failure",
                message=str(e),
                initiated_by=user_id,
            )
            raise ValidationError(f"Patient import failed: {str(e)}")
        finally:
            await adapter.close()

    # ── Plan Operations ───────────────────────────────────────────────

    async def get_patient_plans(
        self, connection_id: uuid.UUID, external_patient_id: str,
    ) -> list[OISPlanResult]:
        conn = await self._get_connection(connection_id)
        adapter = self._create_adapter(conn)

        try:
            return await adapter.get_patient_plans(external_patient_id)
        finally:
            await adapter.close()

    async def get_plan_details(
        self, connection_id: uuid.UUID, external_patient_id: str, external_plan_id: str,
    ) -> dict:
        conn = await self._get_connection(connection_id)
        adapter = self._create_adapter(conn)

        try:
            return await adapter.get_plan_details(external_patient_id, external_plan_id)
        finally:
            await adapter.close()

    # ── Schedule Sync ─────────────────────────────────────────────────

    async def sync_schedule(
        self,
        connection_id: uuid.UUID,
        date_from: str,
        date_to: str,
        machine_name: str | None = None,
        user_id: uuid.UUID | None = None,
    ) -> OISScheduleSyncResult:
        conn = await self._get_connection(connection_id)
        adapter = self._create_adapter(conn)
        start = time.time()

        try:
            ois_appointments = await adapter.get_appointments(date_from, date_to, machine_name)
            created = 0
            updated = 0
            conflicts = []

            for ois_appt in ois_appointments:
                # Check existing mapping
                existing = await self.db.execute(
                    select(OISSyncMapping).where(
                        OISSyncMapping.connection_id == conn.id,
                        OISSyncMapping.entity_type == "appointment",
                        OISSyncMapping.external_id == ois_appt.external_id,
                    )
                )
                mapping = existing.scalar_one_or_none()

                if mapping:
                    mapping.last_synced_at = datetime.now(timezone.utc)
                    mapping.sync_status = "synced"
                    updated += 1
                else:
                    # Find local patient by MRN
                    from app.domains.patients.models import Patient
                    patient_result = await self.db.execute(
                        select(Patient).where(Patient.mrn == ois_appt.patient_mrn)
                    )
                    local_patient = patient_result.scalar_one_or_none()
                    if not local_patient:
                        conflicts.append({
                            "external_id": ois_appt.external_id,
                            "reason": f"Patient MRN {ois_appt.patient_mrn} not found locally",
                        })
                        continue

                    # Create appointment mapping (actual appointment creation deferred)
                    new_mapping = OISSyncMapping(
                        connection_id=conn.id,
                        entity_type="appointment",
                        local_id=local_patient.id,  # Link to patient for now
                        external_id=ois_appt.external_id,
                        external_mrn=ois_appt.patient_mrn,
                        sync_direction="inbound",
                        last_synced_at=datetime.now(timezone.utc),
                        sync_status="synced",
                        metadata={
                            "scheduled_start": str(ois_appt.scheduled_start),
                            "appointment_type": ois_appt.appointment_type,
                            "machine_name": ois_appt.machine_name,
                        },
                    )
                    self.db.add(new_mapping)
                    created += 1

            await self.db.flush()
            duration_ms = (time.time() - start) * 1000

            await self._log_sync(
                connection_id=conn.id,
                operation="schedule_sync",
                status="success" if not conflicts else "partial",
                message=f"Synced {created + updated} appointments ({created} new, {updated} updated)",
                records_processed=created + updated,
                records_failed=len(conflicts),
                duration_ms=duration_ms,
                initiated_by=user_id,
                details={"conflicts": conflicts} if conflicts else None,
            )

            return OISScheduleSyncResult(
                success=True,
                message=f"Schedule sync complete",
                appointments_synced=len(ois_appointments),
                appointments_created=created,
                appointments_updated=updated,
                conflicts=conflicts,
            )
        except Exception as e:
            await self._log_sync(
                connection_id=conn.id,
                operation="schedule_sync",
                status="failure",
                message=str(e),
                initiated_by=user_id,
            )
            raise ValidationError(f"Schedule sync failed: {str(e)}")
        finally:
            await adapter.close()

    # ── Treatment Record Export ────────────────────────────────────────

    async def export_treatment_record(
        self,
        connection_id: uuid.UUID,
        session_id: uuid.UUID,
        user_id: uuid.UUID | None = None,
    ) -> OISRecordExportResult:
        conn = await self._get_connection(connection_id)

        # Look up the session and patient mapping
        from app.domains.treatment.models import TreatmentSession
        session_result = await self.db.execute(
            select(TreatmentSession).where(TreatmentSession.id == session_id)
        )
        session = session_result.scalar_one_or_none()
        if not session:
            raise NotFoundError("Treatment session not found")

        # Find patient mapping
        patient_mapping = await self.db.execute(
            select(OISSyncMapping).where(
                OISSyncMapping.connection_id == conn.id,
                OISSyncMapping.entity_type == "patient",
                OISSyncMapping.local_id == session.patient_id,
            )
        )
        mapping = patient_mapping.scalar_one_or_none()
        if not mapping:
            raise ValidationError("Patient not linked to this OIS connection")

        adapter = self._create_adapter(conn)
        start = time.time()

        try:
            session_data = {
                "treatment_date": str(session.created_at.date()),
                "machine_name": str(session.machine_id),
                "fraction_number": session.fraction_number,
                "beams": [],
            }

            result = await adapter.export_treatment_record(mapping.external_id, session_data)
            duration_ms = (time.time() - start) * 1000

            await self._log_sync(
                connection_id=conn.id,
                operation="record_export",
                entity_type="session",
                entity_id=str(session_id),
                status="success" if result.success else "failure",
                message=result.message,
                records_processed=1 if result.success else 0,
                duration_ms=duration_ms,
                initiated_by=user_id,
            )
            return result
        except Exception as e:
            await self._log_sync(
                connection_id=conn.id,
                operation="record_export",
                entity_type="session",
                entity_id=str(session_id),
                status="failure",
                message=str(e),
                initiated_by=user_id,
            )
            raise ValidationError(f"Record export failed: {str(e)}")
        finally:
            await adapter.close()

    # ── Sync Status ───────────────────────────────────────────────────

    async def get_sync_status(self, connection_id: uuid.UUID) -> OISSyncStatusResponse:
        conn = await self._get_connection(connection_id)

        # Count mapped entities
        patient_count = await self.db.execute(
            select(func.count()).where(
                OISSyncMapping.connection_id == conn.id,
                OISSyncMapping.entity_type == "patient",
            )
        )
        plan_count = await self.db.execute(
            select(func.count()).where(
                OISSyncMapping.connection_id == conn.id,
                OISSyncMapping.entity_type == "plan",
            )
        )
        appt_count = await self.db.execute(
            select(func.count()).where(
                OISSyncMapping.connection_id == conn.id,
                OISSyncMapping.entity_type == "appointment",
            )
        )

        # Recent sync logs
        logs_result = await self.db.execute(
            select(OISSyncLog)
            .where(OISSyncLog.connection_id == conn.id)
            .order_by(OISSyncLog.created_at.desc())
            .limit(10)
        )
        recent_logs = list(logs_result.scalars().all())

        return OISSyncStatusResponse(
            connection_id=conn.id,
            connection_name=conn.name,
            ois_type=conn.ois_type,
            is_active=conn.is_active,
            connection_status=conn.connection_status,
            last_connected_at=conn.last_connected_at,
            total_mapped_patients=patient_count.scalar() or 0,
            total_mapped_plans=plan_count.scalar() or 0,
            total_mapped_appointments=appt_count.scalar() or 0,
            recent_syncs=[],  # Will be serialized from logs via response model
        )

    async def get_sync_logs(
        self,
        connection_id: uuid.UUID | None = None,
        operation: str | None = None,
        limit: int = 50,
    ) -> list[OISSyncLog]:
        query = select(OISSyncLog).order_by(OISSyncLog.created_at.desc()).limit(limit)
        if connection_id:
            query = query.where(OISSyncLog.connection_id == connection_id)
        if operation:
            query = query.where(OISSyncLog.operation == operation)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    # ── Private Helpers ───────────────────────────────────────────────

    async def _get_connection(self, connection_id: uuid.UUID) -> OISConnection:
        result = await self.db.execute(
            select(OISConnection).where(OISConnection.id == connection_id)
        )
        conn = result.scalar_one_or_none()
        if conn is None:
            raise NotFoundError("OIS connection not found")
        return conn

    async def _unset_other_primary(self, exclude_id: uuid.UUID | None) -> None:
        result = await self.db.execute(
            select(OISConnection).where(OISConnection.is_primary.is_(True))
        )
        for conn in result.scalars().all():
            if conn.id != exclude_id:
                conn.is_primary = False

    def _create_adapter(self, conn: OISConnection) -> OISAdapter:
        auth_config = {
            "auth_type": conn.auth_type,
            "client_id": conn.client_id,
            "client_secret": conn.client_secret_encrypted,
            "api_key": conn.api_key_encrypted,
            "username": conn.username,
            "password": conn.password_encrypted,
        }

        if conn.ois_type == "aria":
            return AriaAdapter(conn.base_url, auth_config)
        elif conn.ois_type == "raycare":
            return RayCareAdapter(conn.base_url, auth_config)
        elif conn.ois_type == "generic_fhir":
            base = conn.fhir_base_url or conn.base_url
            return FHIRAdapter(base, auth_config)
        else:
            raise ValidationError(f"Unsupported OIS type: {conn.ois_type}")

    async def _log_sync(
        self,
        connection_id: uuid.UUID,
        operation: str,
        status: str,
        message: str | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        records_processed: int = 0,
        records_failed: int = 0,
        duration_ms: float | None = None,
        initiated_by: uuid.UUID | None = None,
        details: dict | None = None,
    ) -> None:
        log = OISSyncLog(
            connection_id=connection_id,
            operation=operation,
            entity_type=entity_type,
            entity_id=entity_id,
            status=status,
            message=message,
            details=details,
            records_processed=records_processed,
            records_failed=records_failed,
            duration_ms=duration_ms,
            initiated_by=initiated_by,
        )
        self.db.add(log)
        await self.db.flush()

    @staticmethod
    def _compute_hash(data: dict) -> str:
        return hashlib.sha256(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()
