export interface TreatmentMachine {
  id: string;
  name: string;
  machine_type: string;
  manufacturer: string | null;
  model: string | null;
  serial_number: string | null;
  dicom_ae_title: string | null;
  status: 'active' | 'maintenance' | 'decommissioned';
  location: string | null;
  supported_energies: string[] | null;
  has_mlc: boolean;
  mlc_model: string | null;
  num_leaf_pairs: number | null;
  has_epid: boolean;
  has_cbct: boolean;
  has_kv_imaging: boolean;
  commissioning_date: string | null;
  last_calibration_date: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface ToleranceTable {
  id: string;
  name: string;
  description: string | null;
  machine_id: string | null;
  gantry_angle_tol: number | null;
  collimator_angle_tol: number | null;
  couch_angle_tol: number | null;
  couch_vertical_tol: number | null;
  couch_lateral_tol: number | null;
  couch_longitudinal_tol: number | null;
  jaw_x_tol: number | null;
  jaw_y_tol: number | null;
  mlc_tol: number | null;
  mu_tol: number | null;
  dose_rate_tol: number | null;
  energy_tol: number | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}
