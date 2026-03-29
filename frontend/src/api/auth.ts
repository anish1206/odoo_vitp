import { http } from "./http";
import type {
  AccessTokenResponse,
  AuthResponse,
  CurrentUserResponse,
  LoginRequest,
  SignupRequest,
} from "../types/auth";

export const signup = async (payload: SignupRequest): Promise<AuthResponse> => {
  const response = await http.post<AuthResponse>("/auth/signup", payload);
  return response.data;
};

export const login = async (payload: LoginRequest): Promise<AuthResponse> => {
  const response = await http.post<AuthResponse>("/auth/login", payload);
  return response.data;
};

export const refreshAccessToken = async (
  refreshToken: string,
): Promise<AccessTokenResponse> => {
  const response = await http.post<AccessTokenResponse>("/auth/refresh", {
    refresh_token: refreshToken,
  });
  return response.data;
};

export const getCurrentUser = async (): Promise<CurrentUserResponse> => {
  const response = await http.get<CurrentUserResponse>("/users/me");
  return response.data;
};
