import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

let accessToken = "";

export const setAccessToken = (token: string | null): void => {
  accessToken = token ?? "";
};

export const http = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
});

http.interceptors.request.use((config) => {
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }
  return config;
});
