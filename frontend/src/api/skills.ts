import { apiClient } from "./axios";
import type { ResponseEnvelope, SkillAnalytics } from "../types/api";

export interface GetSkillsParams {
  page?: number;
  page_size?: number;
  sort_by?: string;
  sort_order?: string;
  search?: string;
  min_demand?: number;
}

export async function getSkills(
  params?: GetSkillsParams
): Promise<ResponseEnvelope<SkillAnalytics[]>> {
  const response = await apiClient.get<ResponseEnvelope<SkillAnalytics[]>>(
    "/api/v1/skills",
    { params }
  );
  return response.data;
}
