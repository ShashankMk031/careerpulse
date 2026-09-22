import axios, { type AxiosInstance, type AxiosError } from "axios";
import { API_BASE_URL, API_V1_URL } from "../config/env";

export interface ApiErrorPayload {
  success?: boolean;
  error?: string;
  error_code?: string;
  detail?: string;
}

/**
 * Root Axios client pointing to API gateway (handles root, health, metrics, version).
 */
export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: {
    "Content-Type": "application/json",
    Accept: "application/json",
  },
});

/**
 * Analytics Axios client pre-scoped to ${VITE_API_BASE_URL}/api/v1
 */
export const analyticsClient: AxiosInstance = axios.create({
  baseURL: API_V1_URL,
  timeout: 15000,
  headers: {
    "Content-Type": "application/json",
    Accept: "application/json",
  },
});

// Centralized response error handler that preserves structured backend error responses
const errorHandler = (error: AxiosError<ApiErrorPayload>) => {
  const backendMessage =
    error.response?.data?.error ||
    error.response?.data?.detail ||
    error.message ||
    "An unexpected network error occurred.";

  const status = error.response?.status;
  const errorCode = error.response?.data?.error_code;

  console.error(`[API Error ${status ?? "Network"}]:`, backendMessage, {
    status,
    errorCode,
    url: error.config?.url,
  });

  return Promise.reject(error);
};

apiClient.interceptors.response.use((response) => response, errorHandler);
analyticsClient.interceptors.response.use((response) => response, errorHandler);

export default apiClient;
