export interface TreatmentCourse {
  id: string;
  patient_id: string;
  course_number: number;
  intent: 'curative' | 'palliative' | 'prophylactic' | 'boost' | 'sequential';
  diagnosis_id: string | null;
  start_date: string | null;
  end_date: string | null;
  status: string;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface Prescription {
  id: string;
  course_id: string;
  site_name: string;
  modality: 'photon' | 'electron' | 'proton' | 'brachy';
  technique: string;
  total_dose_cgy: number;
  dose_per_fraction_cgy: number;
  num_fractions: number;
  fractions_per_week: number;
  energy: string | null;
  prescribed_by_id: string;
  prescribed_at: string;
  approved_by_id: string | null;
  approved_at: string | null;
  approval_signature_id: string | null;
  notes: string | null;
  version: number;
  created_at: string;
  updated_at: string;
}

export interface BeamControlPoint {
  id: string;
  beam_id: string;
  control_point_index: number;
  cumulative_meterset_weight: number | null;
  gantry_angle: number | null;
  gantry_rotation_direction: string | null;
  collimator_angle: number | null;
  jaw_x1: number | null;
  jaw_x2: number | null;
  jaw_y1: number | null;
  jaw_y2: number | null;
  mlc_positions: Record<string, number[]> | null;
}

export interface PlanBeam {
  id: string;
  plan_id: string;
  beam_number: number;
  beam_name: string | null;
  beam_type: string;
  radiation_type: string;
  treatment_delivery_type: string | null;
  energy_mev: number | null;
  energy_label: string | null;
  dose_rate_mu_per_min: number | null;
  planned_mu: number | null;
  num_control_points: number | null;
  gantry_angle: number | null;
  gantry_rotation: string | null;
  collimator_angle: number | null;
  couch_angle: number | null;
  isocenter_x: number | null;
  isocenter_y: number | null;
  isocenter_z: number | null;
  jaw_x1: number | null;
  jaw_x2: number | null;
  jaw_y1: number | null;
  jaw_y2: number | null;
  wedge_type: string | null;
  wedge_angle: number | null;
  bolus_description: string | null;
  beam_sequence_order: number;
  created_at: string;
}

export interface TreatmentPlan {
  id: string;
  prescription_id: string;
  course_id: string;
  plan_label: string;
  plan_name: string | null;
  status: 'draft' | 'pending_review' | 'reviewed' | 'approved';
  version: number;
  is_current: boolean;
  sop_instance_uid: string | null;
  rt_plan_dicom_path: string | null;
  frame_of_reference_uid: string | null;
  plan_geometry: string | null;
  treatment_machine_id: string | null;
  num_beams: number | null;
  num_fractions_planned: number | null;
  dicom_metadata: Record<string, unknown> | null;
  created_by_id: string;
  reviewed_by_id: string | null;
  reviewed_at: string | null;
  approved_by_id: string | null;
  approved_at: string | null;
  physics_approved_by_id: string | null;
  physics_approved_at: string | null;
  beams: PlanBeam[];
  created_at: string;
  updated_at: string;
}
