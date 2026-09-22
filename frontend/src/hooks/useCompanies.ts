import { useQuery } from "@tanstack/react-query";
import { companiesService, type GetCompaniesParams } from "../services/companies";

export const COMPANIES_QUERY_KEY = ["companies"] as const;

/**
 * Hook fetching paginated and filtered company analytics records.
 */
export function useCompanies(params?: GetCompaniesParams) {
  return useQuery({
    queryKey: [...COMPANIES_QUERY_KEY, params],
    queryFn: () => companiesService.getCompanies(params),
    staleTime: 60 * 1000, // 1 minute
  });
}

/**
 * Hook fetching detail for an individual company by name.
 */
export function useCompanyByName(companyName: string) {
  return useQuery({
    queryKey: [...COMPANIES_QUERY_KEY, "detail", companyName],
    queryFn: () => companiesService.getCompanyByName(companyName),
    enabled: Boolean(companyName),
    staleTime: 5 * 60 * 1000,
  });
}

export default useCompanies;
