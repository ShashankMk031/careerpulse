import { apiClient } from "../api/client";
import type { ApiResponse, CompanyAnalytics } from "../types";

export interface GetCompaniesParams {
  page?: number;
  page_size?: number;
  sort_by?: string;
  sort_order?: "asc" | "desc" | string;
  search?: string;
  min_jobs?: number;
}

export const companiesService = {
  /**
   * Retrieves paginated, sorted, and filtered lists of company analytics records.
   */
  async getCompanies(params?: GetCompaniesParams): Promise<ApiResponse<CompanyAnalytics[]>> {
    const response = await apiClient.get<ApiResponse<CompanyAnalytics[]>>("/api/v1/companies", {
      params,
    });
    return response.data;
  },

  /**
   * Retrieves detail analytics record for an individual company.
   */
  async getCompanyByName(companyName: string): Promise<ApiResponse<CompanyAnalytics>> {
    const response = await apiClient.get<ApiResponse<CompanyAnalytics>>(
      `/api/v1/companies/${encodeURIComponent(companyName)}`
    );
    return response.data;
  },
};

export default companiesService;
