import { apiClient } from "./axios";
import type { ResponseEnvelope, SalaryAnalytics } from "../types/api";

export async function getSalaryTiers(): Promise<ResponseEnvelope<SalaryAnalytics[]>> {
  const response = await apiClient.get<ResponseEnvelope<SalaryAnalytics[]>>(
    "/api/v1/salary"
  );
  return response.data;
}
