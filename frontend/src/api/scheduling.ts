import api from './client';
import type { Appointment, Resource, WorkflowTask, Notification } from '../types/scheduling';

export const schedulingApi = {
  // Appointments
  createAppointment: (data: {
    patient_id: string;
    appointment_type: string;
    scheduled_start: string;
    scheduled_end: string;
    resource_id?: string;
    notes?: string;
  }) => api.post<Appointment>('/scheduling/appointments', data).then(r => r.data),

  listAppointments: (params?: {
    patient_id?: string;
    resource_id?: string;
    date_from?: string;
    date_to?: string;
    status?: string;
    skip?: number;
    limit?: number;
  }) => api.get<Appointment[]>('/scheduling/appointments', { params }).then(r => r.data),

  getAppointment: (appointmentId: string) =>
    api.get<Appointment>(`/scheduling/appointments/${appointmentId}`).then(r => r.data),

  updateAppointment: (appointmentId: string, data: Partial<Appointment>) =>
    api.put<Appointment>(`/scheduling/appointments/${appointmentId}`, data).then(r => r.data),

  cancelAppointment: (appointmentId: string, reason: string) =>
    api.delete<Appointment>(`/scheduling/appointments/${appointmentId}`, {
      data: { reason },
    }).then(r => r.data),

  createRecurring: (data: {
    patient_id: string;
    appointment_type: string;
    scheduled_start: string;
    scheduled_end: string;
    resource_id?: string;
    num_occurrences: number;
    frequency: string;
  }) => api.post<Appointment[]>('/scheduling/appointments/recurring', data).then(r => r.data),

  // Resources
  listResources: (resourceType?: string) =>
    api.get<Resource[]>('/scheduling/resources', {
      params: resourceType ? { resource_type: resourceType } : {},
    }).then(r => r.data),

  createResource: (data: Partial<Resource>) =>
    api.post<Resource>('/scheduling/resources', data).then(r => r.data),

  // Workflow Tasks
  createTask: (data: {
    patient_id: string;
    task_type: string;
    title: string;
    description?: string;
    priority?: string;
    assigned_to_id?: string;
    due_date?: string;
    depends_on_id?: string;
  }) => api.post<WorkflowTask>('/scheduling/tasks', data).then(r => r.data),

  listTasks: (params?: {
    patient_id?: string;
    assigned_to_id?: string;
    status?: string;
    skip?: number;
    limit?: number;
  }) => api.get<WorkflowTask[]>('/scheduling/tasks', { params }).then(r => r.data),

  updateTask: (taskId: string, data: Partial<WorkflowTask>) =>
    api.patch<WorkflowTask>(`/scheduling/tasks/${taskId}`, data).then(r => r.data),

  // Notifications
  getNotifications: (unreadOnly = true) =>
    api.get<Notification[]>('/scheduling/notifications', {
      params: { unread_only: unreadOnly },
    }).then(r => r.data),

  markNotificationRead: (notificationId: string) =>
    api.patch<Notification>(`/scheduling/notifications/${notificationId}/read`).then(r => r.data),
};
