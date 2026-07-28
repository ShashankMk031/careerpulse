import { apiClient } from "./axios";
import type { ResponseEnvelope, DatasetFreshness, ApiVersionInfo } from "../types/api";

export async function getDatasetFreshness(): Promise<ResponseEnvelope<DatasetFreshness[]>> {
  const response = await apiClient.get<ResponseEnvelope<DatasetFreshness[]>>("/metrics");
  return response.data;
}

export async function getHealth(): Promise<ResponseEnvelope<{ status: string; database: string }>> {
  const response = await apiClient.get<ResponseEnvelope<{ status: string; database: string }>>("/health");
  return response.data;
}

export async function getApiVersion(): Promise<ResponseEnvelope<ApiVersionInfo>> {
  const response = await apiClient.get<ResponseEnvelope<ApiVersionInfo>>("/version");
  return response.data;
}
