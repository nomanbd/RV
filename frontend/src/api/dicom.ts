import api from './client';

export interface DicomPeer {
  name: string;
  ae_title: string;
  host: string;
  port: number;
  description: string;
}

export interface DicomStatus {
  scp_running: boolean;
  scp_ae_title: string | null;
  scp_port: number | null;
  registered_peers: number;
  peer_names: string[];
}

export const dicomApi = {
  getStatus: () =>
    api.get<DicomStatus>('/dicom/status').then(r => r.data),

  startScp: () =>
    api.post<{ started: boolean; status: DicomStatus }>('/dicom/scp/start').then(r => r.data),

  stopScp: () =>
    api.post<{ stopped: boolean; status: DicomStatus }>('/dicom/scp/stop').then(r => r.data),

  listPeers: () =>
    api.get<DicomPeer[]>('/dicom/peers').then(r => r.data),

  addPeer: (data: {
    name: string;
    ae_title: string;
    host: string;
    port: number;
    description?: string;
  }) => api.post<DicomPeer>('/dicom/peers', data).then(r => r.data),

  removePeer: (peerName: string) =>
    api.delete<{ removed: boolean }>(`/dicom/peers/${peerName}`).then(r => r.data),

  echoPeer: (peerName: string) =>
    api.post<{ peer_name: string; success: boolean }>(`/dicom/peers/${peerName}/echo`).then(r => r.data),
};
