import uuid
from datetime import date, datetime, timezone

from sqlalchemy import and_, case, cast, func, select, Date
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.domains.machines.models import TreatmentMachine
from app.domains.patients.models import Patient, PatientDiagnosis
from app.domains.planning.models import PlanBeam, Prescription, TreatmentCourse, TreatmentPlan
from app.domains.reporting.schemas import (
    DashboardStats,
    DoseTrackingReport,
    MachineUtilizationReport,
    TreatmentSummaryReport,
)
from app.domains.scheduling.models import WorkflowTask
from app.domains.treatment.models import BeamDeliveryRecord, Fraction, TreatmentSession


class ReportingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_treatment_summary(
        self,
        patient_id: uuid.UUID,
        course_id: uuid.UUID | None = None,
    ) -> TreatmentSummaryReport:
        # Fetch patient
        result = await self.db.execute(
            select(Patient).where(Patient.id == patient_id)
        )
        patient = result.scalar_one_or_none()
        if patient is None:
            raise NotFoundError("Patient not found")

        # Determine course
        course_query = select(TreatmentCourse).where(
            TreatmentCourse.patient_id == patient_id
        )
        if course_id is not None:
            course_query = course_query.where(TreatmentCourse.id == course_id)
        else:
            course_query = course_query.order_by(TreatmentCourse.created_at.desc()).limit(1)

        result = await self.db.execute(course_query)
        course = result.scalar_one_or_none()
        if course is None:
            raise NotFoundError("Treatment course not found")

        # Fetch primary diagnosis
        diagnosis_text: str | None = None
        if course.diagnosis_id is not None:
            result = await self.db.execute(
                select(PatientDiagnosis).where(PatientDiagnosis.id == course.diagnosis_id)
            )
            diagnosis = result.scalar_one_or_none()
            if diagnosis is not None:
                diagnosis_text = f"{diagnosis.icd10_code} - {diagnosis.description}"

        # Fetch first prescription for the course
        result = await self.db.execute(
            select(Prescription)
            .where(Prescription.course_id == course.id)
            .order_by(Prescription.created_at)
            .limit(1)
        )
        prescription = result.scalar_one_or_none()
        prescription_text: str | None = None
        total_prescribed_dose_cgy = 0
        fractions_total = 0
        if prescription is not None:
            prescription_text = (
                f"{prescription.site_name} - "
                f"{prescription.total_dose_cgy} cGy / "
                f"{prescription.num_fractions} fx"
            )
            total_prescribed_dose_cgy = prescription.total_dose_cgy
            fractions_total = prescription.num_fractions

        # Fetch current plan
        result = await self.db.execute(
            select(TreatmentPlan)
            .where(
                TreatmentPlan.course_id == course.id,
                TreatmentPlan.is_current.is_(True),
            )
            .limit(1)
        )
        plan = result.scalar_one_or_none()
        plan_label = plan.plan_label if plan is not None else None

        # Fetch completed fractions
        frac_query = (
            select(Fraction)
            .join(Prescription, Fraction.prescription_id == Prescription.id)
            .where(
                Prescription.course_id == course.id,
                Fraction.status == "completed",
            )
        )
        result = await self.db.execute(frac_query)
        completed_fractions = list(result.scalars().all())
        fractions_completed = len(completed_fractions)
        total_delivered_dose_cgy = sum(
            float(f.delivered_dose_cgy or 0) for f in completed_fractions
        )

        # Fetch beam info from current plan
        beams_data: list[dict] = []
        if plan is not None:
            result = await self.db.execute(
                select(PlanBeam)
                .where(PlanBeam.plan_id == plan.id)
                .order_by(PlanBeam.beam_sequence_order)
            )
            for beam in result.scalars().all():
                beams_data.append(
                    {
                        "beam_number": beam.beam_number,
                        "beam_name": beam.beam_name,
                        "beam_type": beam.beam_type,
                        "energy_label": beam.energy_label,
                        "planned_mu": float(beam.planned_mu) if beam.planned_mu else None,
                        "gantry_angle": float(beam.gantry_angle) if beam.gantry_angle else None,
                    }
                )

        # Fetch recent sessions
        sessions_data: list[dict] = []
        if plan is not None:
            result = await self.db.execute(
                select(TreatmentSession)
                .where(
                    TreatmentSession.patient_id == patient_id,
                    TreatmentSession.plan_id == plan.id,
                )
                .order_by(TreatmentSession.created_at.desc())
                .limit(50)
            )
            for session in result.scalars().all():
                sessions_data.append(
                    {
                        "id": str(session.id),
                        "status": session.status,
                        "treatment_start_at": (
                            session.treatment_start_at.isoformat()
                            if session.treatment_start_at
                            else None
                        ),
                        "treatment_end_at": (
                            session.treatment_end_at.isoformat()
                            if session.treatment_end_at
                            else None
                        ),
                    }
                )

        return TreatmentSummaryReport(
            patient_name=patient.full_name,
            mrn=patient.mrn,
            diagnosis=diagnosis_text,
            prescription=prescription_text,
            plan_label=plan_label,
            fractions_completed=fractions_completed,
            fractions_total=fractions_total,
            total_prescribed_dose_cgy=total_prescribed_dose_cgy,
            total_delivered_dose_cgy=total_delivered_dose_cgy,
            beams=beams_data,
            sessions=sessions_data,
        )

    async def get_dose_tracking(
        self, course_id: uuid.UUID
    ) -> DoseTrackingReport:
        # Verify course exists and get prescription
        result = await self.db.execute(
            select(TreatmentCourse).where(TreatmentCourse.id == course_id)
        )
        course = result.scalar_one_or_none()
        if course is None:
            raise NotFoundError("Treatment course not found")

        result = await self.db.execute(
            select(Prescription)
            .where(Prescription.course_id == course_id)
            .order_by(Prescription.created_at)
            .limit(1)
        )
        prescription = result.scalar_one_or_none()
        site_name = prescription.site_name if prescription else "Unknown"

        # Fetch all fractions for this course
        result = await self.db.execute(
            select(Fraction)
            .join(Prescription, Fraction.prescription_id == Prescription.id)
            .where(Prescription.course_id == course_id)
            .order_by(Fraction.fraction_number)
        )
        fractions_list = list(result.scalars().all())

        fractions_data: list[dict] = []
        for frac in fractions_list:
            fractions_data.append(
                {
                    "fraction_number": frac.fraction_number,
                    "date": str(frac.treated_date) if frac.treated_date else None,
                    "planned_cgy": float(frac.planned_dose_cgy) if frac.planned_dose_cgy else 0,
                    "delivered_cgy": float(frac.delivered_dose_cgy) if frac.delivered_dose_cgy else 0,
                    "cumulative_cgy": float(frac.cumulative_dose_cgy) if frac.cumulative_dose_cgy else 0,
                }
            )

        return DoseTrackingReport(
            course_id=course_id,
            prescription_site=site_name,
            fractions=fractions_data,
        )

    async def get_machine_utilization(
        self,
        machine_id: uuid.UUID | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> list[MachineUtilizationReport]:
        # Build session aggregation query
        session_query = (
            select(
                TreatmentMachine.name.label("machine_name"),
                func.count(TreatmentSession.id).label("total_sessions"),
                func.avg(
                    func.extract(
                        "epoch",
                        TreatmentSession.treatment_end_at
                        - TreatmentSession.treatment_start_at,
                    )
                    / 60
                ).label("avg_duration_min"),
            )
            .join(
                TreatmentSession,
                TreatmentSession.machine_id == TreatmentMachine.id,
            )
            .where(TreatmentSession.status == "completed")
            .group_by(TreatmentMachine.id, TreatmentMachine.name)
        )

        if machine_id is not None:
            session_query = session_query.where(TreatmentMachine.id == machine_id)
        if date_from is not None:
            session_query = session_query.where(
                cast(TreatmentSession.treatment_start_at, Date) >= date_from
            )
        if date_to is not None:
            session_query = session_query.where(
                cast(TreatmentSession.treatment_start_at, Date) <= date_to
            )

        result = await self.db.execute(session_query)
        session_rows = result.all()

        # Build beam count query per machine
        beam_query = (
            select(
                TreatmentSession.machine_id,
                func.count(BeamDeliveryRecord.id).label("total_beams"),
            )
            .join(
                BeamDeliveryRecord,
                BeamDeliveryRecord.session_id == TreatmentSession.id,
            )
            .where(TreatmentSession.status == "completed")
            .group_by(TreatmentSession.machine_id)
        )

        if machine_id is not None:
            beam_query = beam_query.where(TreatmentSession.machine_id == machine_id)
        if date_from is not None:
            beam_query = beam_query.where(
                cast(TreatmentSession.treatment_start_at, Date) >= date_from
            )
        if date_to is not None:
            beam_query = beam_query.where(
                cast(TreatmentSession.treatment_start_at, Date) <= date_to
            )

        result = await self.db.execute(beam_query)
        beam_counts: dict[uuid.UUID, int] = {}
        for row in result.all():
            beam_counts[row.machine_id] = row.total_beams

        # Get machine IDs for cross-referencing beam counts
        machine_names_query = (
            select(TreatmentMachine.id, TreatmentMachine.name)
        )
        if machine_id is not None:
            machine_names_query = machine_names_query.where(
                TreatmentMachine.id == machine_id
            )
        result = await self.db.execute(machine_names_query)
        machine_id_map: dict[str, uuid.UUID] = {}
        for row in result.all():
            machine_id_map[row.name] = row.id

        reports: list[MachineUtilizationReport] = []
        for row in session_rows:
            m_id = machine_id_map.get(row.machine_name)
            reports.append(
                MachineUtilizationReport(
                    machine_name=row.machine_name,
                    total_sessions=row.total_sessions,
                    total_beams=beam_counts.get(m_id, 0) if m_id else 0,
                    avg_session_duration_min=round(float(row.avg_duration_min or 0), 2),
                    date_from=date_from,
                    date_to=date_to,
                )
            )

        return reports

    async def get_dashboard_stats(self) -> DashboardStats:
        today = datetime.now(timezone.utc).date()

        # Active patients
        result = await self.db.execute(
            select(func.count(Patient.id)).where(Patient.is_active.is_(True))
        )
        active_patients = result.scalar() or 0

        # Today's treatments (appointments or sessions scheduled for today)
        result = await self.db.execute(
            select(func.count(TreatmentSession.id)).where(
                cast(TreatmentSession.created_at, Date) == today,
                TreatmentSession.status.in_(["scheduled", "checked_in", "setup", "treatment", "completed"]),
            )
        )
        todays_treatments = result.scalar() or 0

        # Pending plans
        result = await self.db.execute(
            select(func.count(TreatmentPlan.id)).where(
                TreatmentPlan.status.in_(["draft", "pending_review", "pending_approval"])
            )
        )
        pending_plans = result.scalar() or 0

        # Machines online (active)
        result = await self.db.execute(
            select(func.count(TreatmentMachine.id)).where(
                TreatmentMachine.status == "active"
            )
        )
        machines_online = result.scalar() or 0

        # Pending QA tasks (workflow tasks of type containing 'qa' that are not completed)
        result = await self.db.execute(
            select(func.count(WorkflowTask.id)).where(
                WorkflowTask.task_type.ilike("%qa%"),
                WorkflowTask.status.in_(["pending", "assigned", "in_progress"]),
            )
        )
        pending_qa_tasks = result.scalar() or 0

        return DashboardStats(
            active_patients=active_patients,
            todays_treatments=todays_treatments,
            pending_plans=pending_plans,
            machines_online=machines_online,
            pending_qa_tasks=pending_qa_tasks,
        )
