import uuid
from datetime import date, datetime

from pydantic import BaseModel


class TreatmentSummaryReport(BaseModel):
    patient_name: str
    mrn: str
    diagnosis: str | None
    prescription: str | None
    plan_label: str | None
    fractions_completed: int
    fractions_total: int
    total_prescribed_dose_cgy: int
    total_delivered_dose_cgy: float
    beams: list[dict]
    sessions: list[dict]


class DoseTrackingReport(BaseModel):
    course_id: uuid.UUID
    prescription_site: str
    fractions: list[dict]
    """Each dict contains: fraction_number, date, planned_cgy, delivered_cgy, cumulative_cgy"""


class MachineUtilizationReport(BaseModel):
    machine_name: str
    total_sessions: int
    total_beams: int
    avg_session_duration_min: float
    date_from: date | None
    date_to: date | None


class DashboardStats(BaseModel):
    active_patients: int
    todays_treatments: int
    pending_plans: int
    machines_online: int
    pending_qa_tasks: int
