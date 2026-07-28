import { apiClient } from "./axios";
import type { ResponseEnvelope, HiringSummary } from "../types/api";

export async function getDashboardSummary(): Promise<ResponseEnvelope<HiringSummary>> {
  const response = await apiClient.get<ResponseEnvelope<HiringSummary>>("/api/v1/summary");
  return response.data;
}
