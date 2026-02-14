export interface Fraction {
  id: string;
  course_id: string;
  prescription_id: string;
  fraction_number: number;
  status: 'scheduled' | 'in_progress' | 'completed' | 'missed' | 'cancelled';
  planned_dose_cgy: number | null;
  delivered_dose_cgy: number | null;
  cumulative_dose_cgy: number | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface TreatmentSession {
  id: string;
  fraction_id: string;
  machine_id: string;
  plan_id: string;
  tolerance_table_id: string | null;
  status: 'scheduled' | 'checked_in' | 'setup' | 'imaging' | 'treatment' | 'completed' | 'interrupted';
  patient_verified: boolean;
  patient_verified_by_id: string | null;
  patient_verified_at: string | null;
  primary_therapist_id: string | null;
  secondary_therapist_id: string | null;
  physicist_id: string | null;
  setup_notes: string | null;
  treatment_notes: string | null;
  started_at: string | null;
  completed_at: string | null;
  delivery_records: BeamDeliveryRecord[];
  created_at: string;
  updated_at: string;
}

export interface BeamDeliveryRecord {
  id: string;
  session_id: string;
  plan_beam_id: string;
  beam_number: number;
  verification_result: 'pass' | 'fail' | 'override' | 'pending';
  planned_gantry_angle: number | null;
  actual_gantry_angle: number | null;
  planned_collimator_angle: number | null;
  actual_collimator_angle: number | null;
  planned_couch_angle: number | null;
  actual_couch_angle: number | null;
  planned_jaw_x1: number | null;
  actual_jaw_x1: number | null;
  planned_jaw_x2: number | null;
  actual_jaw_x2: number | null;
  planned_jaw_y1: number | null;
  actual_jaw_y1: number | null;
  planned_jaw_y2: number | null;
  actual_jaw_y2: number | null;
  planned_energy: string | null;
  actual_energy: string | null;
  planned_dose_rate: number | null;
  actual_dose_rate: number | null;
  planned_mu: number | null;
  delivered_mu: number | null;
  deviations: Record<string, unknown> | null;
  authorized_by_id: string | null;
  authorized_at: string | null;
  beam_on_at: string | null;
  beam_off_at: string | null;
  override_reason: string | null;
  override_approved_by_id: string | null;
  created_at: string;
}

export interface VerificationResult {
  overall_pass: boolean;
  checks: ParameterCheck[];
  beam_number: number;
}

export interface ParameterCheck {
  name: string;
  planned: number;
  actual: number;
  tolerance: number;
  deviation: number;
  passed: boolean;
}

export interface DoseSummary {
  patient_id: string;
  total_prescribed_dose_cgy: number;
  total_delivered_dose_cgy: number;
  fractions_completed: number;
  fractions_remaining: number;
  courses: CourseDoseSummary[];
}

export interface CourseDoseSummary {
  course_id: string;
  course_number: number;
  prescribed_dose_cgy: number;
  delivered_dose_cgy: number;
  fractions_completed: number;
  fractions_total: number;
}
