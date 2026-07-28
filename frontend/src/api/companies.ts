import { apiClient } from "./axios";
import type { ResponseEnvelope, CompanyAnalytics } from "../types/api";

export interface GetCompaniesParams {
  page?: number;
  page_size?: number;
  sort_by?: string;
  sort_order?: string;
  search?: string;
  min_jobs?: number;
}

export async function getCompanies(
  params?: GetCompaniesParams
): Promise<ResponseEnvelope<CompanyAnalytics[]>> {
  const response = await apiClient.get<ResponseEnvelope<CompanyAnalytics[]>>(
    "/api/v1/companies",
    { params }
  );
  return response.data;
}

export async function getCompanyDetails(
  companyName: string
): Promise<ResponseEnvelope<CompanyAnalytics>> {
  const response = await apiClient.get<ResponseEnvelope<CompanyAnalytics>>(
    `/api/v1/companies/${encodeURIComponent(companyName)}`
  );
  return response.data;
}
