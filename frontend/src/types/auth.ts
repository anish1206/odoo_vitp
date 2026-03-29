export type UserRole = "ADMIN" | "EMPLOYEE";

export interface Company {
  id: number;
  name: string;
  country_code: string;
  base_currency: string;
  created_at: string;
}

export interface User {
  id: number;
  company_id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: UserRole;
  is_approver: boolean;
  is_active: boolean;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
  company: Company;
}

export interface AccessTokenResponse {
  access_token: string;
  token_type: string;
}

export interface CurrentUserResponse {
  user: User;
  company: Company;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface SignupRequest {
  company_name: string;
  country_code: string;
  admin_first_name: string;
  admin_last_name: string;
  email: string;
  password: string;
}
