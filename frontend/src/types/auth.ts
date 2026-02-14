export interface User {
  id: string;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  title: string | null;
  professional_id: string | null;
  status: string;
  last_login_at: string | null;
  roles: Role[];
  created_at: string;
}

export interface Role {
  id: string;
  name: string;
  description: string | null;
  is_system_role: boolean;
  permissions: Permission[];
}

export interface Permission {
  id: string;
  codename: string;
  description: string | null;
  category: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface ElectronicSignatureRequest {
  username: string;
  password: string;
  meaning: 'approval' | 'review' | 'verification' | 'authorization' | 'acknowledgment';
  reason?: string;
  entity_type: string;
  entity_id: string;
}

export interface ElectronicSignatureResponse {
  id: string;
  user_id: string;
  signer_name: string;
  meaning: string;
  reason: string | null;
  entity_type: string;
  entity_id: string;
  signed_at: string;
}
