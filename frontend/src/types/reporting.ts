export interface TreatmentSummaryReport {
  patient_id: string;
  patient_name: string;
  mrn: string;
  courses: CourseSummary[];
  generated_at: string;
}

export interface CourseSummary {
  course_id: string;
  course_number: number;
  intent: string;
  prescriptions: PrescriptionSummary[];
  plans: PlanSummary[];
  fractions_completed: number;
  fractions_total: number;
  total_delivered_dose_cgy: number;
}

export interface PrescriptionSummary {
  site_name: string;
  modality: string;
  technique: string;
  total_dose_cgy: number;
  dose_per_fraction_cgy: number;
  num_fractions: number;
}

export interface PlanSummary {
  plan_label: string;
  status: string;
  num_beams: number | null;
  approved_at: string | null;
}

export interface DoseTrackingReport {
  course_id: string;
  fractions: FractionDosePoint[];
  prescribed_total_dose_cgy: number;
  current_cumulative_dose_cgy: number;
}

export interface FractionDosePoint {
  fraction_number: number;
  planned_dose_cgy: number;
  delivered_dose_cgy: number;
  cumulative_dose_cgy: number;
  date: string;
}

export interface MachineUtilizationReport {
  machine_id: string;
  machine_name: string;
  total_sessions: number;
  completed_sessions: number;
  total_beam_on_minutes: number;
  utilization_percentage: number;
  date_from: string;
  date_to: string;
}

export interface DashboardStats {
  total_patients: number;
  active_plans: number;
  todays_appointments: number;
  pending_tasks: number;
  machines_active: number;
  machines_total: number;
  qa_due: number;
}
