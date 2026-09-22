import { useQuery } from "@tanstack/react-query";
import { geographyService, type GetGeographyParams } from "../services/geography";

export const GEOGRAPHY_QUERY_KEY = ["geography"] as const;

/**
 * Hook fetching geographical job distributions and remote metrics.
 */
export function useGeography(params?: GetGeographyParams) {
  return useQuery({
    queryKey: [...GEOGRAPHY_QUERY_KEY, params],
    queryFn: () => geographyService.getGeography(params),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export default useGeography;
