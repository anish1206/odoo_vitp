import { http } from "./http";
import type {
  AdminUser,
  Category,
  CategoryCreatePayload,
  CategoryUpdatePayload,
  Department,
  DepartmentCreatePayload,
  DepartmentUpdatePayload,
  UserCreatePayload,
  UserUpdatePayload,
} from "../types/admin";

export const listDepartments = async (): Promise<Department[]> => {
  const response = await http.get<Department[]>("/departments");
  return response.data;
};

export const createDepartment = async (
  payload: DepartmentCreatePayload,
): Promise<Department> => {
  const response = await http.post<Department>("/departments", payload);
  return response.data;
};

export const updateDepartment = async (
  departmentId: number,
  payload: DepartmentUpdatePayload,
): Promise<Department> => {
  const response = await http.patch<Department>(`/departments/${departmentId}`, payload);
  return response.data;
};

export const listCategories = async (): Promise<Category[]> => {
  const response = await http.get<Category[]>("/categories");
  return response.data;
};

export const createCategory = async (payload: CategoryCreatePayload): Promise<Category> => {
  const response = await http.post<Category>("/categories", payload);
  return response.data;
};

export const updateCategory = async (
  categoryId: number,
  payload: CategoryUpdatePayload,
): Promise<Category> => {
  const response = await http.patch<Category>(`/categories/${categoryId}`, payload);
  return response.data;
};

export const listUsers = async (): Promise<AdminUser[]> => {
  const response = await http.get<AdminUser[]>("/users");
  return response.data;
};

export const createUser = async (payload: UserCreatePayload): Promise<AdminUser> => {
  const response = await http.post<AdminUser>("/users", payload);
  return response.data;
};

export const updateUser = async (
  userId: number,
  payload: UserUpdatePayload,
): Promise<AdminUser> => {
  const response = await http.patch<AdminUser>(`/users/${userId}`, payload);
  return response.data;
};
