export interface QAChecklist {
  id: string;
  name: string;
  checklist_type: 'daily_machine' | 'monthly_machine' | 'patient_specific' | 'chart_check';
  machine_id: string | null;
  items: QAChecklistItem[];
  is_active: boolean;
  version: number;
  created_by_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface QAChecklistItem {
  key: string;
  label: string;
  type: 'boolean' | 'numeric' | 'text';
  tolerance_min?: number;
  tolerance_max?: number;
  unit?: string;
  required: boolean;
}

export interface QARecord {
  id: string;
  checklist_id: string;
  machine_id: string | null;
  patient_id: string | null;
  performed_by_id: string;
  performed_at: string;
  results: Record<string, unknown>;
  overall_pass: boolean;
  notes: string | null;
  reviewed_by_id: string | null;
  reviewed_at: string | null;
  review_signature_id: string | null;
  created_at: string;
}
