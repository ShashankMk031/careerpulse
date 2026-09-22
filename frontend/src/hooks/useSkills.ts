import { useQuery } from "@tanstack/react-query";
import { skillsService, type GetSkillsParams } from "../services/skills";

export const SKILLS_QUERY_KEY = ["skills"] as const;

/**
 * Hook fetching skills demand and compensation metrics.
 */
export function useSkills(params?: GetSkillsParams) {
  return useQuery({
    queryKey: [...SKILLS_QUERY_KEY, params],
    queryFn: () => skillsService.getSkills(params),
    staleTime: 60 * 60 * 1000, // 1 hour (matches backend Cache-Control: max-age=3600)
  });
}

export default useSkills;
