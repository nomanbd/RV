import apiClient from './client';
import type {
  Patient,
  PatientDetail,
  PatientCreate,
  TwoIdVerificationRequest,
  TwoIdVerificationResponse,
  Diagnosis,
  Allergy,
} from '../types/patient';

export const patientsApi = {
  list: async (params?: {
    q?: string;
    mrn?: string;
    name?: string;
    is_active?: boolean;
    skip?: number;
    limit?: number;
  }): Promise<Patient[]> => {
    const res = await apiClient.get<Patient[]>('/patients', { params });
    return res.data;
  },

  get: async (id: string): Promise<PatientDetail> => {
    const res = await apiClient.get<PatientDetail>(`/patients/${id}`);
    return res.data;
  },

  create: async (data: PatientCreate): Promise<PatientDetail> => {
    const res = await apiClient.post<PatientDetail>('/patients', data);
    return res.data;
  },

  update: async (id: string, data: Partial<PatientCreate>): Promise<PatientDetail> => {
    const res = await apiClient.put<PatientDetail>(`/patients/${id}`, data);
    return res.data;
  },

  verify: async (
    id: string,
    data: TwoIdVerificationRequest
  ): Promise<TwoIdVerificationResponse> => {
    const res = await apiClient.post<TwoIdVerificationResponse>(
      `/patients/${id}/verify`,
      data
    );
    return res.data;
  },

  addDiagnosis: async (
    patientId: string,
    data: Omit<Diagnosis, 'id' | 'created_at'>
  ): Promise<Diagnosis> => {
    const res = await apiClient.post<Diagnosis>(
      `/patients/${patientId}/diagnoses`,
      data
    );
    return res.data;
  },

  addAllergy: async (
    patientId: string,
    data: Omit<Allergy, 'id'>
  ): Promise<Allergy> => {
    const res = await apiClient.post<Allergy>(
      `/patients/${patientId}/allergies`,
      data
    );
    return res.data;
  },
};
