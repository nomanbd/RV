import api from './client';
import type {
  TreatmentSummaryReport,
  DoseTrackingReport,
  MachineUtilizationReport,
  DashboardStats,
} from '../types/reporting';

export const reportingApi = {
  getTreatmentSummary: (patientId: string, courseId?: string) =>
    api.get<TreatmentSummaryReport>(`/reports/treatment-summary/${patientId}`, {
      params: courseId ? { course_id: courseId } : {},
    }).then(r => r.data),

  getDoseTracking: (courseId: string) =>
    api.get<DoseTrackingReport>(`/reports/dose-tracking/${courseId}`).then(r => r.data),

  getMachineUtilization: (params?: {
    machine_id?: string;
    date_from?: string;
    date_to?: string;
  }) => api.get<MachineUtilizationReport[]>('/reports/machine-utilization', { params }).then(r => r.data),

  getDashboardStats: () =>
    api.get<DashboardStats>('/dashboard/stats').then(r => r.data),
};
