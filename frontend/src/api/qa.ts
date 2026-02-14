import api from './client';
import type { QAChecklist, QARecord } from '../types/qa';

export const qaApi = {
  // Checklists
  createChecklist: (data: {
    name: string;
    checklist_type: string;
    machine_id?: string;
    items: Array<{ key: string; label: string; type: string; required: boolean }>;
  }) => api.post<QAChecklist>('/qa/checklists', data).then(r => r.data),

  listChecklists: (params?: { checklist_type?: string; machine_id?: string }) =>
    api.get<QAChecklist[]>('/qa/checklists', { params }).then(r => r.data),

  getChecklist: (checklistId: string) =>
    api.get<QAChecklist>(`/qa/checklists/${checklistId}`).then(r => r.data),

  updateChecklist: (checklistId: string, data: Partial<QAChecklist>) =>
    api.put<QAChecklist>(`/qa/checklists/${checklistId}`, data).then(r => r.data),

  // Records
  submitRecord: (data: {
    checklist_id: string;
    machine_id?: string;
    patient_id?: string;
    results: Record<string, unknown>;
    overall_pass: boolean;
    notes?: string;
  }) => api.post<QARecord>('/qa/records', data).then(r => r.data),

  listRecords: (params?: {
    machine_id?: string;
    date_from?: string;
    date_to?: string;
    skip?: number;
    limit?: number;
  }) => api.get<QARecord[]>('/qa/records', { params }).then(r => r.data),

  getRecord: (recordId: string) =>
    api.get<QARecord>(`/qa/records/${recordId}`).then(r => r.data),

  reviewRecord: (recordId: string, signatureId: string) =>
    api.post<QARecord>(`/qa/records/${recordId}/review`, {
      signature_id: signatureId,
    }).then(r => r.data),
};
