import apiClient from './client';
import type {
  OISConnection,
  OISConnectionCreate,
  OISConnectionTestResult,
  OISPatientResult,
  OISPatientImportResult,
  OISPlanResult,
  OISSyncLog,
  OISSyncStatus,
  OISScheduleSyncResult,
} from '../types/ois';

export const oisApi = {
  // Connections
  listConnections: async (activeOnly = false): Promise<OISConnection[]> => {
    const res = await apiClient.get<OISConnection[]>('/ois/connections', {
      params: { active_only: activeOnly },
    });
    return res.data;
  },

  getConnection: async (id: string): Promise<OISConnection> => {
    const res = await apiClient.get<OISConnection>(`/ois/connections/${id}`);
    return res.data;
  },

  createConnection: async (data: OISConnectionCreate): Promise<OISConnection> => {
    const res = await apiClient.post<OISConnection>('/ois/connections', data);
    return res.data;
  },

  updateConnection: async (
    id: string,
    data: Partial<OISConnectionCreate> & { is_active?: boolean }
  ): Promise<OISConnection> => {
    const res = await apiClient.put<OISConnection>(`/ois/connections/${id}`, data);
    return res.data;
  },

  deleteConnection: async (id: string): Promise<void> => {
    await apiClient.delete(`/ois/connections/${id}`);
  },

  testConnection: async (id: string): Promise<OISConnectionTestResult> => {
    const res = await apiClient.post<OISConnectionTestResult>(
      `/ois/connections/${id}/test`
    );
    return res.data;
  },

  // Patient Lookup
  lookupPatients: async (
    connectionId: string,
    params: { mrn?: string; first_name?: string; last_name?: string; date_of_birth?: string }
  ): Promise<OISPatientResult[]> => {
    const res = await apiClient.post<OISPatientResult[]>(
      `/ois/connections/${connectionId}/patients/lookup`,
      params
    );
    return res.data;
  },

  importPatient: async (
    connectionId: string,
    externalId: string
  ): Promise<OISPatientImportResult> => {
    const res = await apiClient.post<OISPatientImportResult>(
      `/ois/connections/${connectionId}/patients/${externalId}/import`
    );
    return res.data;
  },

  // Plans
  getPatientPlans: async (
    connectionId: string,
    externalPatientId: string
  ): Promise<OISPlanResult[]> => {
    const res = await apiClient.get<OISPlanResult[]>(
      `/ois/connections/${connectionId}/patients/${externalPatientId}/plans`
    );
    return res.data;
  },

  // Schedule Sync
  syncSchedule: async (data: {
    connection_id: string;
    date_from: string;
    date_to: string;
    machine_name?: string;
  }): Promise<OISScheduleSyncResult> => {
    const res = await apiClient.post<OISScheduleSyncResult>('/ois/schedule/sync', data);
    return res.data;
  },

  // Treatment Record Export
  exportRecord: async (data: {
    connection_id: string;
    session_id: string;
  }): Promise<{ success: boolean; message: string; external_record_id?: string }> => {
    const res = await apiClient.post('/ois/records/export', data);
    return res.data;
  },

  // Sync Status & Logs
  getSyncStatus: async (connectionId: string): Promise<OISSyncStatus> => {
    const res = await apiClient.get<OISSyncStatus>(
      `/ois/connections/${connectionId}/status`
    );
    return res.data;
  },

  getSyncLogs: async (params?: {
    connection_id?: string;
    operation?: string;
    limit?: number;
  }): Promise<OISSyncLog[]> => {
    const res = await apiClient.get<OISSyncLog[]>('/ois/sync-logs', { params });
    return res.data;
  },
};
