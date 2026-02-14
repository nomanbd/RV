import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError, ValidationError
from app.domains.machines.models import ToleranceTable
from app.domains.planning.models import PlanBeam, Prescription, TreatmentCourse, TreatmentPlan
from app.domains.treatment.models import BeamDeliveryRecord, Fraction, TreatmentSession
from app.domains.treatment.schemas import (
    AuthorizeBeamRequest,
    DoseSummaryResponse,
    OverrideRequest,
    RecordDeliveryRequest,
    SessionCreate,
    VerifyBeamRequest,
    VerifyPatientRequest,
)
from app.domains.treatment.verification import BeamParameters, ToleranceValues, VerificationEngine


# Valid session status transitions
_VALID_TRANSITIONS: dict[str, list[str]] = {
    "scheduled": ["checked_in", "cancelled"],
    "checked_in": ["setup", "cancelled"],
    "setup": ["imaging", "treatment", "cancelled"],
    "imaging": ["treatment", "cancelled"],
    "treatment": ["completed", "interrupted", "cancelled"],
    "interrupted": ["treatment", "cancelled"],
}


class TreatmentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.verification_engine = VerificationEngine()

    # --- Sessions ---

    async def create_session(self, data: SessionCreate) -> TreatmentSession:
        session = TreatmentSession(**data.model_dump())
        self.db.add(session)
        await self.db.flush()
        return session

    async def get_session(self, session_id: uuid.UUID) -> TreatmentSession:
        result = await self.db.execute(
            select(TreatmentSession)
            .options(selectinload(TreatmentSession.delivery_records))
            .where(TreatmentSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        if session is None:
            raise NotFoundError("Treatment session not found")
        return session

    async def update_session_status(
        self, session_id: uuid.UUID, status: str, user_id: uuid.UUID
    ) -> TreatmentSession:
        session = await self.get_session(session_id)

        # Validate state transition
        allowed = _VALID_TRANSITIONS.get(session.status, [])
        if status not in allowed:
            raise ValidationError(
                f"Invalid status transition from '{session.status}' to '{status}'. "
                f"Allowed transitions: {allowed}"
            )

        now = datetime.now(timezone.utc)
        session.status = status

        # Record timestamps for each phase
        if status == "checked_in":
            session.check_in_at = now
        elif status == "setup":
            session.setup_start_at = now
        elif status == "imaging":
            session.imaging_start_at = now
        elif status == "treatment":
            session.treatment_start_at = now
        elif status in ("completed", "interrupted", "cancelled"):
            session.treatment_end_at = now

        await self.db.flush()
        return session

    async def verify_patient(
        self, session_id: uuid.UUID, verification_data: VerifyPatientRequest, user_id: uuid.UUID
    ) -> TreatmentSession:
        session = await self.get_session(session_id)

        now = datetime.now(timezone.utc)
        session.patient_verified = True
        session.patient_verified_by_id = user_id
        session.patient_verified_at = now
        session.verification_method = verification_data.verification_method

        await self.db.flush()
        return session

    async def verify_beam(self, session_id: uuid.UUID, beam_data: VerifyBeamRequest):
        """Verify beam parameters against plan values using the tolerance table."""
        session = await self.get_session(session_id)

        # Get the plan beam for this beam number
        result = await self.db.execute(
            select(PlanBeam).where(
                PlanBeam.plan_id == session.plan_id,
                PlanBeam.beam_number == beam_data.beam_number,
            )
        )
        plan_beam = result.scalar_one_or_none()
        if plan_beam is None:
            raise NotFoundError(
                f"Beam number {beam_data.beam_number} not found in plan"
            )

        # Get tolerance table
        result = await self.db.execute(
            select(ToleranceTable).where(ToleranceTable.id == session.tolerance_table_id)
        )
        tolerance_table = result.scalar_one_or_none()
        if tolerance_table is None:
            raise NotFoundError("Tolerance table not found")

        # Build planned parameters from PlanBeam model
        planned = BeamParameters.from_dict({
            "gantry_angle": plan_beam.gantry_angle,
            "collimator_angle": plan_beam.collimator_angle,
            "couch_angle": plan_beam.couch_angle,
            "couch_vertical": plan_beam.couch_vertical,
            "couch_lateral": plan_beam.couch_lateral,
            "couch_longitudinal": plan_beam.couch_longitudinal,
            "jaw_x1": plan_beam.jaw_x1,
            "jaw_x2": plan_beam.jaw_x2,
            "jaw_y1": plan_beam.jaw_y1,
            "jaw_y2": plan_beam.jaw_y2,
            "energy": plan_beam.energy_label,
            "dose_rate": plan_beam.dose_rate_mu_per_min,
            "mu": plan_beam.planned_mu,
        })

        # Build actual parameters from request
        actual = BeamParameters.from_dict(beam_data.actual_parameters)

        # Build tolerance values from table
        tolerances = ToleranceValues.from_model(tolerance_table)

        # Run verification
        verification_result = self.verification_engine.verify_beam(planned, actual, tolerances)

        return verification_result

    async def authorize_beam(
        self, session_id: uuid.UUID, beam_number: int, user_id: uuid.UUID
    ) -> BeamDeliveryRecord:
        """Authorize a beam for delivery after successful verification."""
        session = await self.get_session(session_id)

        # Get the plan beam
        result = await self.db.execute(
            select(PlanBeam).where(
                PlanBeam.plan_id == session.plan_id,
                PlanBeam.beam_number == beam_number,
            )
        )
        plan_beam = result.scalar_one_or_none()
        if plan_beam is None:
            raise NotFoundError(f"Beam number {beam_number} not found in plan")

        now = datetime.now(timezone.utc)

        # Create or update delivery record
        result = await self.db.execute(
            select(BeamDeliveryRecord).where(
                BeamDeliveryRecord.session_id == session_id,
                BeamDeliveryRecord.beam_number == beam_number,
            )
        )
        record = result.scalar_one_or_none()

        if record is None:
            record = BeamDeliveryRecord(
                session_id=session_id,
                plan_beam_id=plan_beam.id,
                beam_number=beam_number,
                verification_result="pass",
                verified_at=now,
                verified_by_id=user_id,
                planned_mu=plan_beam.planned_mu,
                planned_gantry_angle=plan_beam.gantry_angle,
                planned_collimator_angle=plan_beam.collimator_angle,
                planned_couch_angle=plan_beam.couch_angle,
                planned_energy=plan_beam.energy_label,
                planned_dose_rate=plan_beam.dose_rate_mu_per_min,
                planned_jaw_x1=plan_beam.jaw_x1,
                planned_jaw_x2=plan_beam.jaw_x2,
                planned_jaw_y1=plan_beam.jaw_y1,
                planned_jaw_y2=plan_beam.jaw_y2,
            )
            self.db.add(record)
        else:
            record.verification_result = "pass"
            record.verified_at = now
            record.verified_by_id = user_id

        await self.db.flush()
        return record

    async def record_delivery(
        self, session_id: uuid.UUID, delivery_data: RecordDeliveryRequest
    ) -> BeamDeliveryRecord:
        """Record beam delivery data after a beam has been delivered."""
        session = await self.get_session(session_id)

        # Find existing delivery record for this beam
        result = await self.db.execute(
            select(BeamDeliveryRecord).where(
                BeamDeliveryRecord.session_id == session_id,
                BeamDeliveryRecord.beam_number == delivery_data.beam_number,
            )
        )
        record = result.scalar_one_or_none()

        if record is None:
            # Need the plan beam to create the record
            beam_result = await self.db.execute(
                select(PlanBeam).where(
                    PlanBeam.plan_id == session.plan_id,
                    PlanBeam.beam_number == delivery_data.beam_number,
                )
            )
            plan_beam = beam_result.scalar_one_or_none()
            if plan_beam is None:
                raise NotFoundError(
                    f"Beam number {delivery_data.beam_number} not found in plan"
                )

            record = BeamDeliveryRecord(
                session_id=session_id,
                plan_beam_id=plan_beam.id,
                beam_number=delivery_data.beam_number,
                verification_result="pass",
                planned_mu=plan_beam.planned_mu,
                planned_gantry_angle=plan_beam.gantry_angle,
                planned_collimator_angle=plan_beam.collimator_angle,
                planned_couch_angle=plan_beam.couch_angle,
                planned_energy=plan_beam.energy_label,
                planned_dose_rate=plan_beam.dose_rate_mu_per_min,
                planned_jaw_x1=plan_beam.jaw_x1,
                planned_jaw_x2=plan_beam.jaw_x2,
                planned_jaw_y1=plan_beam.jaw_y1,
                planned_jaw_y2=plan_beam.jaw_y2,
            )
            self.db.add(record)

        # Record actual delivery values
        record.actual_mu = delivery_data.actual_mu
        record.actual_gantry_angle = delivery_data.actual_gantry_angle
        record.actual_collimator_angle = delivery_data.actual_collimator_angle
        record.actual_couch_angle = delivery_data.actual_couch_angle
        record.actual_energy = delivery_data.actual_energy
        record.actual_dose_rate = delivery_data.actual_dose_rate
        record.actual_jaw_x1 = delivery_data.actual_jaw_x1
        record.actual_jaw_x2 = delivery_data.actual_jaw_x2
        record.actual_jaw_y1 = delivery_data.actual_jaw_y1
        record.actual_jaw_y2 = delivery_data.actual_jaw_y2
        record.actual_couch_vertical = delivery_data.actual_couch_vertical
        record.actual_couch_lateral = delivery_data.actual_couch_lateral
        record.actual_couch_longitudinal = delivery_data.actual_couch_longitudinal
        record.delivered_dose_cgy = delivery_data.delivered_dose_cgy
        record.beam_on_at = delivery_data.beam_on_at
        record.beam_off_at = delivery_data.beam_off_at

        await self.db.flush()
        return record

    async def override_verification(
        self,
        session_id: uuid.UUID,
        beam_number: int,
        reason: str,
        user_id: uuid.UUID,
        signature_id: uuid.UUID,
    ) -> BeamDeliveryRecord:
        """Override a failed beam verification with reason and e-signature."""
        session = await self.get_session(session_id)

        # Find existing delivery record or create one
        result = await self.db.execute(
            select(BeamDeliveryRecord).where(
                BeamDeliveryRecord.session_id == session_id,
                BeamDeliveryRecord.beam_number == beam_number,
            )
        )
        record = result.scalar_one_or_none()

        if record is None:
            beam_result = await self.db.execute(
                select(PlanBeam).where(
                    PlanBeam.plan_id == session.plan_id,
                    PlanBeam.beam_number == beam_number,
                )
            )
            plan_beam = beam_result.scalar_one_or_none()
            if plan_beam is None:
                raise NotFoundError(
                    f"Beam number {beam_number} not found in plan"
                )

            record = BeamDeliveryRecord(
                session_id=session_id,
                plan_beam_id=plan_beam.id,
                beam_number=beam_number,
                verification_result="override",
                planned_mu=plan_beam.planned_mu,
                planned_gantry_angle=plan_beam.gantry_angle,
                planned_collimator_angle=plan_beam.collimator_angle,
                planned_couch_angle=plan_beam.couch_angle,
                planned_energy=plan_beam.energy_label,
                planned_dose_rate=plan_beam.dose_rate_mu_per_min,
                planned_jaw_x1=plan_beam.jaw_x1,
                planned_jaw_x2=plan_beam.jaw_x2,
                planned_jaw_y1=plan_beam.jaw_y1,
                planned_jaw_y2=plan_beam.jaw_y2,
            )
            self.db.add(record)

        now = datetime.now(timezone.utc)
        record.verification_result = "override"
        record.override_reason = reason
        record.override_approved_by_id = user_id
        record.verified_at = now
        record.verified_by_id = user_id

        await self.db.flush()
        return record

    async def complete_session(
        self, session_id: uuid.UUID, user_id: uuid.UUID
    ) -> TreatmentSession:
        """Complete a treatment session and update fraction dose totals."""
        session = await self.get_session(session_id)

        # Calculate total delivered dose from all delivery records
        total_delivered = sum(
            float(r.delivered_dose_cgy or 0) for r in session.delivery_records
        )

        # Update the fraction
        result = await self.db.execute(
            select(Fraction).where(Fraction.id == session.fraction_id)
        )
        fraction = result.scalar_one_or_none()
        if fraction is not None:
            fraction.delivered_dose_cgy = float(fraction.delivered_dose_cgy or 0) + total_delivered
            fraction.status = "completed"
            fraction.treated_date = datetime.now(timezone.utc).date()
            fraction.treated_by_id = user_id

            # Update cumulative dose across all fractions for this prescription
            frac_result = await self.db.execute(
                select(Fraction).where(
                    Fraction.prescription_id == fraction.prescription_id,
                    Fraction.status == "completed",
                )
            )
            completed_fractions = frac_result.scalars().all()
            cumulative = sum(float(f.delivered_dose_cgy or 0) for f in completed_fractions)
            # Add current fraction dose if not yet in the completed list
            if fraction.id not in [f.id for f in completed_fractions]:
                cumulative += total_delivered
            fraction.cumulative_dose_cgy = cumulative

        # Mark session completed
        now = datetime.now(timezone.utc)
        session.status = "completed"
        session.treatment_end_at = now
        session.all_beams_delivered = True

        await self.db.flush()
        return session

    async def get_dose_summary(self, patient_id: uuid.UUID) -> DoseSummaryResponse:
        """Aggregate dose across all courses, prescriptions, and fractions for a patient."""
        # Get all courses for this patient
        courses_result = await self.db.execute(
            select(TreatmentCourse)
            .options(selectinload(TreatmentCourse.prescriptions))
            .where(TreatmentCourse.patient_id == patient_id)
        )
        courses = courses_result.scalars().all()

        total_prescribed_cgy = 0.0
        total_delivered_cgy = 0.0
        fractions_completed = 0
        fractions_remaining = 0

        for course in courses:
            for prescription in course.prescriptions:
                total_prescribed_cgy += float(prescription.total_dose_cgy or 0)

                # Get fractions for this prescription
                frac_result = await self.db.execute(
                    select(Fraction).where(Fraction.prescription_id == prescription.id)
                )
                fractions = frac_result.scalars().all()

                for fraction in fractions:
                    if fraction.status == "completed":
                        fractions_completed += 1
                        total_delivered_cgy += float(fraction.delivered_dose_cgy or 0)
                    elif fraction.status not in ("cancelled",):
                        fractions_remaining += 1

        return DoseSummaryResponse(
            patient_id=patient_id,
            total_prescribed_cgy=total_prescribed_cgy,
            total_delivered_cgy=total_delivered_cgy,
            fractions_completed=fractions_completed,
            fractions_remaining=fractions_remaining,
        )
