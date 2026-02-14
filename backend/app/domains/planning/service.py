import io
import uuid
from datetime import datetime, timezone

import pydicom
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError, ValidationError
from app.dicom.parsers.rt_plan import RTPlanParser
from app.dicom.storage.file_manager import DicomFileManager
from app.domains.planning.models import (
    BeamControlPoint,
    PlanBeam,
    Prescription,
    TreatmentCourse,
    TreatmentPlan,
)


class PlanningService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ---- Treatment Course ----

    async def create_course(
        self, patient_id: uuid.UUID, data: dict
    ) -> TreatmentCourse:
        course = TreatmentCourse(patient_id=patient_id, **data)
        self.db.add(course)
        await self.db.flush()
        return course

    async def get_course(self, course_id: uuid.UUID) -> TreatmentCourse:
        result = await self.db.execute(
            select(TreatmentCourse)
            .options(selectinload(TreatmentCourse.prescriptions))
            .where(TreatmentCourse.id == course_id)
        )
        course = result.scalar_one_or_none()
        if course is None:
            raise NotFoundError("Treatment course not found")
        return course

    async def list_courses(
        self,
        patient_id: uuid.UUID | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[TreatmentCourse]:
        query = select(TreatmentCourse)
        if patient_id is not None:
            query = query.where(TreatmentCourse.patient_id == patient_id)
        query = query.order_by(TreatmentCourse.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    # ---- Prescription ----

    async def create_prescription(self, data: dict) -> Prescription:
        # Verify course exists
        course_id = data.get("course_id")
        await self.get_course(course_id)

        prescription = Prescription(
            **data,
            prescribed_at=datetime.now(timezone.utc),
        )
        self.db.add(prescription)
        await self.db.flush()
        return prescription

    async def approve_prescription(
        self,
        prescription_id: uuid.UUID,
        user_id: uuid.UUID,
        signature_id: uuid.UUID,
    ) -> Prescription:
        result = await self.db.execute(
            select(Prescription).where(Prescription.id == prescription_id)
        )
        prescription = result.scalar_one_or_none()
        if prescription is None:
            raise NotFoundError("Prescription not found")

        if prescription.approved_by_id is not None:
            raise ValidationError("Prescription is already approved")

        prescription.approved_by_id = user_id
        prescription.approved_at = datetime.now(timezone.utc)
        prescription.approval_signature_id = signature_id
        await self.db.flush()
        return prescription

    # ---- Treatment Plan ----

    async def import_plan(
        self,
        file_bytes: bytes,
        filename: str,
        course_id: uuid.UUID,
        prescription_id: uuid.UUID,
        created_by_id: uuid.UUID,
    ) -> TreatmentPlan:
        # Verify course and prescription exist
        await self.get_course(course_id)
        rx_result = await self.db.execute(
            select(Prescription).where(Prescription.id == prescription_id)
        )
        if rx_result.scalar_one_or_none() is None:
            raise NotFoundError("Prescription not found")

        # Parse the DICOM RT Plan
        ds = pydicom.dcmread(io.BytesIO(file_bytes))
        parser = RTPlanParser()
        parsed = parser.parse(ds)

        plan_data = parsed["plan"]
        beams_data = parsed["beams"]
        fraction_groups = parsed["fraction_groups"]
        dicom_metadata = parsed["dicom_metadata"]

        # Store the DICOM file on disk
        file_manager = DicomFileManager()
        relative_path = file_manager.store(ds, patient_id=str(course_id))

        # Determine number of planned fractions from fraction groups
        num_fractions_planned = None
        if fraction_groups:
            num_fractions_planned = fraction_groups[0].get("num_fractions_planned")

        # Create the TreatmentPlan record
        plan = TreatmentPlan(
            prescription_id=prescription_id,
            course_id=course_id,
            plan_label=plan_data.get("plan_label", "Unknown"),
            plan_name=plan_data.get("plan_name"),
            status="draft",
            version=1,
            is_current=True,
            sop_instance_uid=plan_data.get("sop_instance_uid"),
            rt_plan_dicom_path=relative_path,
            rt_struct_sop_uid=plan_data.get("referenced_structure_set_uid"),
            rt_dose_sop_uid=plan_data.get("referenced_dose_uid"),
            frame_of_reference_uid=plan_data.get("frame_of_reference_uid"),
            plan_geometry=plan_data.get("plan_geometry"),
            num_beams=len(beams_data),
            num_fractions_planned=num_fractions_planned,
            dicom_metadata=dicom_metadata,
            created_by_id=created_by_id,
        )
        self.db.add(plan)
        await self.db.flush()

        # Create PlanBeam and BeamControlPoint records
        for beam_data in beams_data:
            control_points_data = beam_data.pop("control_points", [])
            # Remove keys not on the PlanBeam model
            beam_data.pop("treatment_machine_name", None)

            beam = PlanBeam(
                plan_id=plan.id,
                beam_number=beam_data["beam_number"],
                beam_name=beam_data.get("beam_name"),
                beam_type=beam_data["beam_type"],
                radiation_type=beam_data["radiation_type"],
                treatment_delivery_type=beam_data.get("treatment_delivery_type"),
                energy_mev=beam_data.get("energy_mev"),
                energy_label=beam_data.get("energy_label"),
                dose_rate_mu_per_min=beam_data.get("dose_rate_mu_per_min"),
                planned_mu=beam_data.get("planned_mu"),
                num_control_points=beam_data.get("num_control_points"),
                gantry_angle=beam_data.get("gantry_angle"),
                gantry_rotation=beam_data.get("gantry_rotation"),
                collimator_angle=beam_data.get("collimator_angle"),
                couch_angle=beam_data.get("couch_angle"),
                isocenter_x=beam_data.get("isocenter_x"),
                isocenter_y=beam_data.get("isocenter_y"),
                isocenter_z=beam_data.get("isocenter_z"),
                jaw_x1=beam_data.get("jaw_x1"),
                jaw_x2=beam_data.get("jaw_x2"),
                jaw_y1=beam_data.get("jaw_y1"),
                jaw_y2=beam_data.get("jaw_y2"),
                wedge_type=beam_data.get("wedge_type"),
                wedge_angle=beam_data.get("wedge_angle"),
                bolus_description=beam_data.get("bolus_description"),
                beam_sequence_order=beam_data["beam_sequence_order"],
            )
            self.db.add(beam)
            await self.db.flush()

            for cp_data in control_points_data:
                control_point = BeamControlPoint(
                    beam_id=beam.id,
                    control_point_index=cp_data["control_point_index"],
                    cumulative_meterset_weight=cp_data.get("cumulative_meterset_weight"),
                    gantry_angle=cp_data.get("gantry_angle"),
                    gantry_rotation_direction=cp_data.get("gantry_rotation_direction"),
                    collimator_angle=cp_data.get("collimator_angle"),
                    jaw_x1=cp_data.get("jaw_x1"),
                    jaw_x2=cp_data.get("jaw_x2"),
                    jaw_y1=cp_data.get("jaw_y1"),
                    jaw_y2=cp_data.get("jaw_y2"),
                    mlc_positions=cp_data.get("mlc_positions"),
                )
                self.db.add(control_point)

        await self.db.flush()
        return plan

    async def get_plan(self, plan_id: uuid.UUID) -> TreatmentPlan:
        result = await self.db.execute(
            select(TreatmentPlan)
            .options(
                selectinload(TreatmentPlan.beams).selectinload(PlanBeam.control_points)
            )
            .where(TreatmentPlan.id == plan_id)
        )
        plan = result.scalar_one_or_none()
        if plan is None:
            raise NotFoundError("Treatment plan not found")
        return plan

    async def list_plans(
        self,
        patient_id: uuid.UUID | None = None,
        status: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[TreatmentPlan]:
        query = select(TreatmentPlan).options(selectinload(TreatmentPlan.beams))

        if patient_id is not None:
            query = query.join(TreatmentCourse).where(
                TreatmentCourse.patient_id == patient_id
            )
        if status is not None:
            query = query.where(TreatmentPlan.status == status)

        query = query.order_by(TreatmentPlan.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    # ---- Plan Workflow ----

    async def _transition_plan(
        self,
        plan_id: uuid.UUID,
        from_status: str,
        to_status: str,
        error_message: str,
    ) -> TreatmentPlan:
        """Helper to load a plan and validate its status for a transition."""
        plan = await self.get_plan(plan_id)
        if plan.status != from_status:
            raise ValidationError(
                f"{error_message}. Current status: {plan.status}"
            )
        plan.status = to_status
        return plan

    async def submit_for_review(self, plan_id: uuid.UUID) -> TreatmentPlan:
        plan = await self._transition_plan(
            plan_id,
            from_status="draft",
            to_status="pending_review",
            error_message="Only draft plans can be submitted for review",
        )
        await self.db.flush()
        return plan

    async def review_plan(
        self,
        plan_id: uuid.UUID,
        reviewer_id: uuid.UUID,
        signature_id: uuid.UUID,
    ) -> TreatmentPlan:
        plan = await self._transition_plan(
            plan_id,
            from_status="pending_review",
            to_status="reviewed",
            error_message="Only plans pending review can be reviewed",
        )
        plan.reviewed_by_id = reviewer_id
        plan.reviewed_at = datetime.now(timezone.utc)
        plan.review_signature_id = signature_id
        await self.db.flush()
        return plan

    async def approve_plan(
        self,
        plan_id: uuid.UUID,
        approver_id: uuid.UUID,
        signature_id: uuid.UUID,
    ) -> TreatmentPlan:
        plan = await self._transition_plan(
            plan_id,
            from_status="reviewed",
            to_status="approved",
            error_message="Only reviewed plans can be approved",
        )
        plan.approved_by_id = approver_id
        plan.approved_at = datetime.now(timezone.utc)
        plan.approval_signature_id = signature_id
        await self.db.flush()
        return plan

    async def physics_approve_plan(
        self,
        plan_id: uuid.UUID,
        approver_id: uuid.UUID,
        signature_id: uuid.UUID,
    ) -> TreatmentPlan:
        plan = await self.get_plan(plan_id)
        if plan.status != "approved":
            raise ValidationError(
                f"Only approved plans can receive physics approval. Current status: {plan.status}"
            )
        plan.physics_approved_by_id = approver_id
        plan.physics_approved_at = datetime.now(timezone.utc)
        plan.physics_approval_signature_id = signature_id
        await self.db.flush()
        return plan

    # ---- Beam Queries ----

    async def get_plan_beams(self, plan_id: uuid.UUID) -> list[PlanBeam]:
        # Verify plan exists
        await self.get_plan(plan_id)
        result = await self.db.execute(
            select(PlanBeam)
            .where(PlanBeam.plan_id == plan_id)
            .order_by(PlanBeam.beam_sequence_order)
        )
        return list(result.scalars().all())

    async def get_beam_control_points(
        self, beam_id: uuid.UUID
    ) -> list[BeamControlPoint]:
        # Verify beam exists
        result = await self.db.execute(
            select(PlanBeam).where(PlanBeam.id == beam_id)
        )
        if result.scalar_one_or_none() is None:
            raise NotFoundError("Beam not found")

        result = await self.db.execute(
            select(BeamControlPoint)
            .where(BeamControlPoint.beam_id == beam_id)
            .order_by(BeamControlPoint.control_point_index)
        )
        return list(result.scalars().all())
