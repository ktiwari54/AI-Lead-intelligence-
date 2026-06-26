import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { get, post } from "@/lib/api";

export interface ScoreBreakdown {
  reasoning: string;
  strengths: string[];
  weaknesses: string[];
  recommendation: "HOT" | "WARM" | "COLD" | "DISQUALIFIED";
}

export interface LeadScore {
  id: string;
  contact_id?: string;
  company_id?: string;
  overall_score: number;
  seniority_score: number;
  company_score: number;
  engagement_score: number;
  technology_score: number;
  industry_score: number;
  fit_score: number;
  score_breakdown: ScoreBreakdown;
  model_used: string;
  created_at: string;
}

export function useContactScores(contactId: string) {
  return useQuery({
    queryKey: ["ai-scores", "contact", contactId],
    queryFn: async () => (await get<{ data: LeadScore[] }>(`/ai/scores/contact/${contactId}`)).data,
    enabled: !!contactId,
  });
}

export function useCompanyScores(companyId: string) {
  return useQuery({
    queryKey: ["ai-scores", "company", companyId],
    queryFn: async () => (await get<{ data: LeadScore[] }>(`/ai/scores/company/${companyId}`)).data,
    enabled: !!companyId,
  });
}

export function useScoreContact() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ contactId, icpProfile }: { contactId: string; icpProfile?: object }) =>
      post(`/ai/score/contact/${contactId}`, { icp_profile: icpProfile }),
    onSuccess: (_, { contactId }) => {
      qc.invalidateQueries({ queryKey: ["ai-scores", "contact", contactId] });
    },
  });
}

export function useScoreCompany() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ companyId, icpProfile }: { companyId: string; icpProfile?: object }) =>
      post(`/ai/score/company/${companyId}`, { icp_profile: icpProfile }),
    onSuccess: (_, { companyId }) => {
      qc.invalidateQueries({ queryKey: ["ai-scores", "company", companyId] });
    },
  });
}
