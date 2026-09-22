export const API_BASE_URL: string =
  (import.meta.env.VITE_API_BASE_URL as string) ?? "http://127.0.0.1:8000";

export const API_V1_URL: string = `${API_BASE_URL}/api/v1`;
