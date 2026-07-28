import axios from "axios";
import { API_BASE_URL } from "../config/env";
import { REQUEST_TIMEOUT } from "../constants/network";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: REQUEST_TIMEOUT,
  headers: {
    "Content-Type": "application/json",
    Accept: "application/json",
  },
});

// Configure simple response interceptors for global logging/error normalization
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Standard error mapping that can be caught by queries
    const message =
      error.response?.data?.error ||
      error.message ||
      "An unexpected network error occurred.";
    
    console.error("API Error:", message, error);
    return Promise.reject(new Error(message));
  }
);

export default apiClient;
export { apiClient };
