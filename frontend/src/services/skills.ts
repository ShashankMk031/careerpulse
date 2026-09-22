import { apiClient } from "../api/client";
import type { ApiResponse, SkillAnalytics } from "../types";

export interface GetSkillsParams {
  page?: number;
  page_size?: number;
  sort_by?: string;
  sort_order?: "asc" | "desc" | string;
  search?: string;
  min_demand?: number;
}

export const skillsService = {
  /**
   * Retrieves paginated skill demand and salary metrics.
   */
  async getSkills(params?: GetSkillsParams): Promise<ApiResponse<SkillAnalytics[]>> {
    const response = await apiClient.get<ApiResponse<SkillAnalytics[]>>("/api/v1/skills", {
      params,
    });
    return response.data;
  },
};

export default skillsService;
