import { apiClient } from "./axios";
import type { ResponseEnvelope, GeographyAnalytics } from "../types/api";

export interface GetGeographyParams {
  country?: string;
  remote?: boolean;
  sort_by?: string;
  sort_order?: string;
}

export async function getGeography(
  params?: GetGeographyParams
): Promise<ResponseEnvelope<GeographyAnalytics[]>> {
  const response = await apiClient.get<ResponseEnvelope<GeographyAnalytics[]>>(
    "/api/v1/geography",
    { params }
  );
  return response.data;
}
