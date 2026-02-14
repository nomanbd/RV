import api from './client';
import type { TreatmentCourse, Prescription, TreatmentPlan, PlanBeam, BeamControlPoint } from '../types/planning';

export const planningApi = {
  // Treatment Courses
  createCourse: (data: {
    patient_id: string;
    course_number?: number;
    intent: string;
    diagnosis_id?: string;
    start_date?: string;
    notes?: string;
  }) => api.post<TreatmentCourse>('/plans/courses', data).then(r => r.data),

  listCourses: (params?: { patient_id?: string; skip?: number; limit?: number }) =>
    api.get<TreatmentCourse[]>('/plans/courses', { params }).then(r => r.data),

  getCourse: (courseId: string) =>
    api.get<TreatmentCourse>(`/plans/courses/${courseId}`).then(r => r.data),

  // Prescriptions
  createPrescription: (data: {
    course_id: string;
    site_name: string;
    modality: string;
    technique: string;
    total_dose_cgy: number;
    dose_per_fraction_cgy: number;
    num_fractions: number;
    energy?: string;
    prescribed_by_id: string;
    notes?: string;
  }) => api.post<Prescription>('/plans/prescriptions', data).then(r => r.data),

  approvePrescription: (prescriptionId: string, signatureId: string) =>
    api.post<Prescription>(`/plans/prescriptions/${prescriptionId}/approve`, {
      signature_id: signatureId,
    }).then(r => r.data),

  // Treatment Plans
  importPlan: (file: File, courseId: string, prescriptionId: string) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post<TreatmentPlan>(
      `/plans/plans/import?course_id=${courseId}&prescription_id=${prescriptionId}`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    ).then(r => r.data);
  },

  listPlans: (params?: { patient_id?: string; status?: string; skip?: number; limit?: number }) =>
    api.get<TreatmentPlan[]>('/plans/plans', { params }).then(r => r.data),

  getPlan: (planId: string) =>
    api.get<TreatmentPlan>(`/plans/plans/${planId}`).then(r => r.data),

  getPlanBeams: (planId: string) =>
    api.get<PlanBeam[]>(`/plans/plans/${planId}/beams`).then(r => r.data),

  getBeamControlPoints: (planId: string, beamId: string) =>
    api.get<BeamControlPoint[]>(`/plans/plans/${planId}/beams/${beamId}/control-points`).then(r => r.data),

  // Plan Workflow
  submitForReview: (planId: string) =>
    api.post<TreatmentPlan>(`/plans/plans/${planId}/submit-for-review`).then(r => r.data),

  reviewPlan: (planId: string, signatureId: string, comment?: string) =>
    api.post<TreatmentPlan>(`/plans/plans/${planId}/review`, {
      signature_id: signatureId,
      comment,
    }).then(r => r.data),

  approvePlan: (planId: string, signatureId: string, comment?: string) =>
    api.post<TreatmentPlan>(`/plans/plans/${planId}/approve`, {
      signature_id: signatureId,
      comment,
    }).then(r => r.data),

  physicsApprovePlan: (planId: string, signatureId: string, comment?: string) =>
    api.post<TreatmentPlan>(`/plans/plans/${planId}/physics-approve`, {
      signature_id: signatureId,
      comment,
    }).then(r => r.data),
};
