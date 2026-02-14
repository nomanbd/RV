import api from './client';
import type { RTImage, ImageReview } from '../types/imaging';

export const imagingApi = {
  importImage: (file: File, patientId: string, sessionId?: string) => {
    const formData = new FormData();
    formData.append('file', file);
    const params: Record<string, string> = { patient_id: patientId };
    if (sessionId) params.session_id = sessionId;
    return api.post<RTImage>('/imaging/images/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      params,
    }).then(r => r.data);
  },

  listImages: (params?: { patient_id?: string; session_id?: string; image_type?: string }) =>
    api.get<RTImage[]>('/imaging/images', { params }).then(r => r.data),

  getImage: (imageId: string) =>
    api.get<RTImage>(`/imaging/images/${imageId}`).then(r => r.data),

  createReview: (imageId: string, data: {
    shift_vertical_mm?: number;
    shift_lateral_mm?: number;
    shift_longitudinal_mm?: number;
    rotation_pitch_deg?: number;
    rotation_roll_deg?: number;
    rotation_yaw_deg?: number;
    notes?: string;
  }) => api.post<ImageReview>(`/imaging/images/${imageId}/review`, {
    image_id: imageId,
    ...data,
  }).then(r => r.data),

  applyShifts: (reviewId: string) =>
    api.post<ImageReview>(`/imaging/reviews/${reviewId}/apply-shifts`).then(r => r.data),
};
