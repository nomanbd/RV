export interface Resource {
  id: string;
  name: string;
  resource_type: 'machine' | 'room' | 'staff';
  machine_id: string | null;
  location: string | null;
  is_active: boolean;
  created_at: string;
}

export interface Appointment {
  id: string;
  patient_id: string;
  appointment_type: 'treatment' | 'simulation' | 'consultation' | 'follow_up' | 'qa';
  scheduled_start: string;
  scheduled_end: string;
  resource_id: string | null;
  status: 'scheduled' | 'checked_in' | 'in_progress' | 'completed' | 'cancelled' | 'no_show';
  notes: string | null;
  cancellation_reason: string | null;
  created_by_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface WorkflowTask {
  id: string;
  patient_id: string;
  task_type: string;
  title: string;
  description: string | null;
  status: 'pending' | 'in_progress' | 'completed' | 'blocked';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  assigned_to_id: string | null;
  due_date: string | null;
  completed_at: string | null;
  completed_by_id: string | null;
  depends_on_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface Notification {
  id: string;
  user_id: string;
  notification_type: string;
  title: string;
  message: string;
  entity_type: string | null;
  entity_id: string | null;
  is_read: boolean;
  read_at: string | null;
  created_at: string;
}
