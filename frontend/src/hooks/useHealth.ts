import { useQuery } from "@tanstack/react-query";
import { healthService } from "../services/health";

export const HEALTH_QUERY_KEY = ["health"] as const;

/**
 * Hook querying /health to check database connectivity status.
 * Polling is conservative (every 60s) to avoid unnecessary overhead.
 */
export function useHealth() {
  return useQuery({
    queryKey: HEALTH_QUERY_KEY,
    queryFn: () => healthService.getHealth(),
    staleTime: 30 * 1000, // 30 seconds
    refetchInterval: 60 * 1000, // Background poll every 60s (not aggressive)
    retry: 1,
  });
}

/**
 * Hook querying /metrics to retrieve pipeline freshness lag status.
 */
export function useDatasetFreshness() {
  return useQuery({
    queryKey: ["metrics", "freshness"],
    queryFn: () => healthService.getDatasetFreshness(),
    staleTime: 2 * 60 * 1000,
  });
}

/**
 * Hook querying /version to fetch runtime build and git hash details.
 */
export function useApiVersion() {
  return useQuery({
    queryKey: ["version"],
    queryFn: () => healthService.getVersion(),
    staleTime: 24 * 60 * 60 * 1000,
  });
}

export default useHealth;
