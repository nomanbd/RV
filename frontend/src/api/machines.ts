import api from './client';
import type { TreatmentMachine, ToleranceTable } from '../types/machine';

export const machinesApi = {
  listMachines: (status?: string) =>
    api.get<TreatmentMachine[]>('/machines', { params: status ? { status } : {} }).then(r => r.data),

  createMachine: (data: Partial<TreatmentMachine>) =>
    api.post<TreatmentMachine>('/machines', data).then(r => r.data),

  getMachine: (machineId: string) =>
    api.get<TreatmentMachine>(`/machines/${machineId}`).then(r => r.data),

  updateMachine: (machineId: string, data: Partial<TreatmentMachine>) =>
    api.put<TreatmentMachine>(`/machines/${machineId}`, data).then(r => r.data),

  updateMachineStatus: (machineId: string, status: string) =>
    api.patch<TreatmentMachine>(`/machines/${machineId}/status`, { status }).then(r => r.data),

  listMachineTolerances: (machineId: string) =>
    api.get<ToleranceTable[]>(`/machines/${machineId}/tolerances`).then(r => r.data),

  // Tolerance Tables
  createTolerance: (data: Partial<ToleranceTable>) =>
    api.post<ToleranceTable>('/tolerances', data).then(r => r.data),

  getTolerance: (toleranceId: string) =>
    api.get<ToleranceTable>(`/tolerances/${toleranceId}`).then(r => r.data),

  updateTolerance: (toleranceId: string, data: Partial<ToleranceTable>) =>
    api.put<ToleranceTable>(`/tolerances/${toleranceId}`, data).then(r => r.data),
};
