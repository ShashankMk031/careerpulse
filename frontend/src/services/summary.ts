import { apiClient } from "../api/client";
import type { ApiResponse, Summary } from "../types";

export const summaryService = {
  /**
   * Retrieves high-level global KPIs and pipeline generation metadata.
   */
  async getSummary(): Promise<ApiResponse<Summary>> {
    const response = await apiClient.get<ApiResponse<Summary>>("/api/v1/summary");
    return response.data;
  },
};

export default summaryService;
