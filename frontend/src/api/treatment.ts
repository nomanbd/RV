import api from './client';
import type { TreatmentSession, BeamDeliveryRecord, Fraction, VerificationResult, DoseSummary } from '../types/treatment';

export const treatmentApi = {
  // Sessions
  createSession: (data: {
    fraction_id: string;
    machine_id: string;
    plan_id: string;
    tolerance_table_id?: string;
  }) => api.post<TreatmentSession>('/treatment/sessions', data).then(r => r.data),

  getSession: (sessionId: string) =>
    api.get<TreatmentSession>(`/treatment/sessions/${sessionId}`).then(r => r.data),

  updateSessionStatus: (sessionId: string, status: string) =>
    api.patch<TreatmentSession>(`/treatment/sessions/${sessionId}/status`, { status }).then(r => r.data),

  verifyPatient: (sessionId: string, data: {
    verification_method: string;
    identifier_1: string;
    identifier_2: string;
  }) => api.post<TreatmentSession>(`/treatment/sessions/${sessionId}/verify-patient`, data).then(r => r.data),

  verifyBeam: (sessionId: string, data: {
    beam_number: number;
    actual_gantry_angle?: number;
    actual_collimator_angle?: number;
    actual_couch_angle?: number;
    actual_jaw_x1?: number;
    actual_jaw_x2?: number;
    actual_jaw_y1?: number;
    actual_jaw_y2?: number;
    actual_energy?: string;
    actual_dose_rate?: number;
    actual_mu?: number;
  }) => api.post<VerificationResult>(`/treatment/sessions/${sessionId}/verify-beam`, data).then(r => r.data),

  authorizeBeam: (sessionId: string, beamNumber: number) =>
    api.post<BeamDeliveryRecord>(`/treatment/sessions/${sessionId}/authorize-beam`, {
      beam_number: beamNumber,
    }).then(r => r.data),

  recordDelivery: (sessionId: string, data: {
    beam_number: number;
    delivered_mu: number;
    beam_on_at?: string;
    beam_off_at?: string;
  }) => api.post<BeamDeliveryRecord>(`/treatment/sessions/${sessionId}/record-delivery`, data).then(r => r.data),

  overrideVerification: (sessionId: string, data: {
    beam_number: number;
    reason: string;
    signature_id: string;
  }) => api.post<BeamDeliveryRecord>(`/treatment/sessions/${sessionId}/override`, data).then(r => r.data),

  completeSession: (sessionId: string) =>
    api.post<TreatmentSession>(`/treatment/sessions/${sessionId}/complete`).then(r => r.data),

  listDeliveryRecords: (sessionId: string) =>
    api.get<BeamDeliveryRecord[]>(`/treatment/sessions/${sessionId}/delivery-records`).then(r => r.data),

  // Fractions
  getFraction: (fractionId: string) =>
    api.get<Fraction>(`/treatment/fractions/${fractionId}`).then(r => r.data),

  // Dose Summary
  getDoseSummary: (patientId: string) =>
    api.get<DoseSummary>(`/treatment/patients/${patientId}/dose-summary`).then(r => r.data),
};
