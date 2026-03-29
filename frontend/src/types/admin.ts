import type { UserRole } from "./auth";

export interface Department {
  id: number;
  company_id: number;
  name: string;
  code: string | null;
  created_at: string;
  updated_at: string;
}

export interface Category {
  id: number;
  company_id: number;
  name: string;
  code: string | null;
  description: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AdminUser {
  id: number;
  company_id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: UserRole;
  is_approver: boolean;
  is_active: boolean;
  department_id: number | null;
  manager_id: number | null;
  created_at: string;
}

export interface DepartmentCreatePayload {
  name: string;
  code?: string | null;
}

export interface DepartmentUpdatePayload {
  name?: string;
  code?: string | null;
}

export interface CategoryCreatePayload {
  name: string;
  code?: string | null;
  description?: string | null;
}

export interface CategoryUpdatePayload {
  name?: string;
  code?: string | null;
  description?: string | null;
  is_active?: boolean;
}

export interface UserCreatePayload {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  role: UserRole;
  is_approver: boolean;
  department_id?: number | null;
  manager_id?: number | null;
}

export interface UserUpdatePayload {
  first_name?: string;
  last_name?: string;
  role?: UserRole;
  is_approver?: boolean;
  is_active?: boolean;
  department_id?: number | null;
  manager_id?: number | null;
  password?: string;
}
