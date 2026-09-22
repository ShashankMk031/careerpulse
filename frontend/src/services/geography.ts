import { apiClient } from "../api/client";
import type { ApiResponse, GeographyAnalytics } from "../types";

export interface GetGeographyParams {
  country?: string;
  remote?: boolean;
  sort_by?: string;
  sort_order?: "asc" | "desc" | string;
}

export const geographyService = {
  /**
   * Retrieves regional hiring and remote job distributions.
   */
  async getGeography(params?: GetGeographyParams): Promise<ApiResponse<GeographyAnalytics[]>> {
    const response = await apiClient.get<ApiResponse<GeographyAnalytics[]>>("/api/v1/geography", {
      params,
    });
    return response.data;
  },
};

export default geographyService;
