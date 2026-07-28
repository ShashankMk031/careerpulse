import { apiClient } from "./axios";
import type { ResponseEnvelope, TechnologyAnalytics } from "../types/api";

export interface GetTechnologyParams {
  page?: number;
  page_size?: number;
  sort_by?: string;
  sort_order?: string;
  search?: string;
}

export async function getTechnology(
  params?: GetTechnologyParams
): Promise<ResponseEnvelope<TechnologyAnalytics[]>> {
  const response = await apiClient.get<ResponseEnvelope<TechnologyAnalytics[]>>(
    "/api/v1/technology",
    { params }
  );
  return response.data;
}
