import { apiClient } from "../api/client";
import type { ApiResponse, HealthStatus, DatasetFreshness, ApiVersionInfo } from "../types";

export const healthService = {
  /**
   * Pings /health endpoint to check active connection to PostgreSQL RDS.
   */
  async getHealth(): Promise<ApiResponse<HealthStatus>> {
    const response = await apiClient.get<ApiResponse<HealthStatus>>("/health");
    return response.data;
  },

  /**
   * Retrieves data pipeline freshness indicators from /metrics.
   */
  async getDatasetFreshness(): Promise<ApiResponse<DatasetFreshness[]>> {
    const response = await apiClient.get<ApiResponse<DatasetFreshness[]>>("/metrics");
    return response.data;
  },

  /**
   * Retrieves system build, git commit, and python version telemetry from /version.
   */
  async getVersion(): Promise<ApiResponse<ApiVersionInfo>> {
    const response = await apiClient.get<ApiResponse<ApiVersionInfo>>("/version");
    return response.data;
  },
};

export default healthService;
