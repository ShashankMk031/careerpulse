import { useQuery } from "@tanstack/react-query";
import { technologyService, type GetTechnologyParams } from "../services/technology";

export const TECHNOLOGY_QUERY_KEY = ["technology"] as const;

/**
 * Hook fetching technology and framework analytics.
 */
export function useTechnology(params?: GetTechnologyParams) {
  return useQuery({
    queryKey: [...TECHNOLOGY_QUERY_KEY, params],
    queryFn: () => technologyService.getTechnology(params),
    staleTime: 60 * 60 * 1000, // 1 hour (matches backend Cache-Control: max-age=3600)
  });
}

export default useTechnology;
