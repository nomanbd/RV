import apiClient from './client';
import type {
  LoginRequest,
  TokenResponse,
  User,
  ElectronicSignatureRequest,
  ElectronicSignatureResponse,
} from '../types/auth';

export const authApi = {
  login: async (data: LoginRequest): Promise<TokenResponse> => {
    const res = await apiClient.post<TokenResponse>('/auth/login', data);
    return res.data;
  },

  getMe: async (): Promise<User> => {
    const res = await apiClient.get<User>('/users/me');
    return res.data;
  },

  changePassword: async (currentPassword: string, newPassword: string): Promise<void> => {
    await apiClient.post('/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    });
  },

  createElectronicSignature: async (
    data: ElectronicSignatureRequest
  ): Promise<ElectronicSignatureResponse> => {
    const res = await apiClient.post<ElectronicSignatureResponse>(
      '/auth/electronic-signature',
      data
    );
    return res.data;
  },
};
