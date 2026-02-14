export interface OISConnection {
  id: string;
  name: string;
  ois_type: 'aria' | 'raycare' | 'generic_fhir';
  base_url: string;
  auth_type: 'basic' | 'oauth2' | 'api_key' | 'certificate';
  fhir_base_url: string | null;
  dicom_ae_title: string | null;
  dicom_host: string | null;
  dicom_port: number | null;
  is_active: boolean;
  is_primary: boolean;
  last_connected_at: string | null;
  connection_status: string;
  settings: Record<string, unknown> | null;
  created_at: string;
}

export interface OISConnectionCreate {
  name: string;
  ois_type: 'aria' | 'raycare' | 'generic_fhir';
  base_url: string;
  auth_type: 'basic' | 'oauth2' | 'api_key' | 'certificate';
  client_id?: string;
  client_secret?: string;
  api_key?: string;
  username?: string;
  password?: string;
  certificate_path?: string;
  fhir_base_url?: string;
  dicom_ae_title?: string;
  dicom_host?: string;
  dicom_port?: number;
  is_primary?: boolean;
  settings?: Record<string, unknown>;
}

export interface OISConnectionTestResult {
  success: boolean;
  message: string;
  response_time_ms: number | null;
  ois_version: string | null;
  capabilities: string[];
}

export interface OISPatientResult {
  external_id: string;
  mrn: string;
  first_name: string;
  last_name: string;
  middle_name: string | null;
  date_of_birth: string | null;
  sex: string | null;
  diagnoses: Array<{ code: string; description: string; site?: string }>;
  courses: Array<{ id: string; course_id: string; intent: string; start_date?: string }>;
  source_system: string;
}

export interface OISPatientImportResult {
  success: boolean;
  local_patient_id: string | null;
  message: string;
  imported_courses: number;
  imported_plans: number;
}

export interface OISPlanResult {
  external_id: string;
  plan_label: string;
  plan_type: string | null;
  status: string | null;
  modality: string | null;
  technique: string | null;
  num_beams: number;
  prescribed_dose_cgy: number | null;
  num_fractions: number | null;
  approval_status: string | null;
  created_date: string | null;
  source_system: string;
}

export interface OISSyncLog {
  id: string;
  connection_id: string;
  operation: string;
  entity_type: string | null;
  entity_id: string | null;
  status: string;
  message: string | null;
  records_processed: number;
  records_failed: number;
  duration_ms: number | null;
  created_at: string;
}

export interface OISSyncStatus {
  connection_id: string;
  connection_name: string;
  ois_type: string;
  is_active: boolean;
  connection_status: string;
  last_connected_at: string | null;
  total_mapped_patients: number;
  total_mapped_plans: number;
  total_mapped_appointments: number;
  recent_syncs: OISSyncLog[];
}

export interface OISScheduleSyncResult {
  success: boolean;
  message: string;
  appointments_synced: number;
  appointments_created: number;
  appointments_updated: number;
  conflicts: Array<{ external_id: string; reason: string }>;
}
