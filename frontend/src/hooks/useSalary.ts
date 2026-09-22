import { useQuery } from "@tanstack/react-query";
import { salaryService } from "../services/salary";

export const SALARY_QUERY_KEY = ["salary"] as const;

/**
 * Hook fetching salary tier distribution brackets.
 */
export function useSalary() {
  return useQuery({
    queryKey: SALARY_QUERY_KEY,
    queryFn: () => salaryService.getSalary(),
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
}

export default useSalary;
