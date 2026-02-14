export interface RTImage {
  id: string;
  patient_id: string;
  session_id: string | null;
  sop_instance_uid: string | null;
  series_instance_uid: string | null;
  study_instance_uid: string | null;
  image_type: 'portal' | 'cbct' | 'kv' | 'mv' | 'drr' | 'ct';
  modality: string | null;
  acquisition_date: string | null;
  rows: number | null;
  columns: number | null;
  pixel_spacing_x: number | null;
  pixel_spacing_y: number | null;
  window_center: number | null;
  window_width: number | null;
  file_path: string;
  thumbnail_path: string | null;
  rt_image_description: string | null;
  gantry_angle: number | null;
  beam_limiting_device_angle: number | null;
  patient_support_angle: number | null;
  sid: number | null;
  created_at: string;
}

export interface ImageReview {
  id: string;
  image_id: string;
  reviewer_id: string;
  reviewed_at: string;
  shift_vertical_mm: number | null;
  shift_lateral_mm: number | null;
  shift_longitudinal_mm: number | null;
  rotation_pitch_deg: number | null;
  rotation_roll_deg: number | null;
  rotation_yaw_deg: number | null;
  shifts_applied: boolean;
  applied_by_id: string | null;
  applied_at: string | null;
  notes: string | null;
  created_at: string;
}
