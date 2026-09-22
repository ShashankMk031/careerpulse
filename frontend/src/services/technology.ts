import { apiClient } from "../api/client";
import type { ApiResponse, TechnologyAnalytics } from "../types";

export interface GetTechnologyParams {
  page?: number;
  page_size?: number;
  sort_by?: string;
  sort_order?: "asc" | "desc" | string;
  search?: string;
}

export const technologyService = {
  /**
   * Retrieves technology and framework adoption analytics.
   */
  async getTechnology(params?: GetTechnologyParams): Promise<ApiResponse<TechnologyAnalytics[]>> {
    const response = await apiClient.get<ApiResponse<TechnologyAnalytics[]>>("/api/v1/technology", {
      params,
    });
    return response.data;
  },
};

export default technologyService;
