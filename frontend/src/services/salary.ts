import { apiClient } from "../api/client";
import type { ApiResponse, SalaryAnalytics } from "../types";

export const salaryService = {
  /**
   * Retrieves salary tier bracket histograms.
   */
  async getSalary(): Promise<ApiResponse<SalaryAnalytics[]>> {
    const response = await apiClient.get<ApiResponse<SalaryAnalytics[]>>("/api/v1/salary");
    return response.data;
  },
};

export default salaryService;
