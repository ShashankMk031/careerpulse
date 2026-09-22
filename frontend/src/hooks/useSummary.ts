import { useQuery } from "@tanstack/react-query";
import { summaryService } from "../services/summary";

export const SUMMARY_QUERY_KEY = ["summary"] as const;

/**
 * Hook fetching the executive KPI summary metrics with 5-minute cache consistency.
 */
export function useSummary() {
  return useQuery({
    queryKey: SUMMARY_QUERY_KEY,
    queryFn: () => summaryService.getSummary(),
    staleTime: 5 * 60 * 1000, // 5 minutes (matches backend Cache-Control: max-age=300)
    gcTime: 10 * 60 * 1000,
  });
}

export default useSummary;
