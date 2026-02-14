export interface Patient {
  id: string;
  mrn: string;
  first_name: string;
  middle_name: string | null;
  last_name: string;
  date_of_birth: string;
  sex: string;
  phone_primary: string | null;
  email: string | null;
  address_line1: string | null;
  city: string | null;
  state: string | null;
  postal_code: string | null;
  country: string;
  primary_oncologist_id: string | null;
  is_active: boolean;
  dicom_patient_id: string | null;
  created_at: string;
}

export interface PatientDetail extends Patient {
  phone_secondary: string | null;
  address_line2: string | null;
  emergency_contact_name: string | null;
  emergency_contact_phone: string | null;
  photo_path: string | null;
  notes: string | null;
  diagnoses: Diagnosis[];
  allergies: Allergy[];
}

export interface Diagnosis {
  id: string;
  icd10_code: string;
  description: string;
  diagnosis_date: string | null;
  site: string | null;
  laterality: string | null;
  is_primary: boolean;
  created_at: string;
}

export interface Allergy {
  id: string;
  allergen: string;
  reaction: string | null;
  severity: string | null;
}

export interface PatientCreate {
  mrn: string;
  first_name: string;
  middle_name?: string;
  last_name: string;
  date_of_birth: string;
  sex: string;
  phone_primary?: string;
  email?: string;
  address_line1?: string;
  city?: string;
  state?: string;
  postal_code?: string;
  notes?: string;
}

export interface TwoIdVerificationRequest {
  identifier1_type: string;
  identifier1_value: string;
  identifier2_type: string;
  identifier2_value: string;
}

export interface TwoIdVerificationResponse {
  verified: boolean;
  patient_id: string | null;
  patient_name: string | null;
  message: string;
}
