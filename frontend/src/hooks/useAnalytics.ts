import { useQuery } from "@tanstack/react-query";
import { get } from "@/lib/api";

export interface TimeSeriesPoint {
  date: string;
  value: number;
  label?: string;
}

export interface BreakdownItem {
  label: string;
  value: number;
  percentage?: number;
  color?: string;
}

export interface DashboardStats {
  total_companies: number;
  total_contacts: number;
  total_searches: number;
  ai_scores_generated: number;
  credits_remaining: number;
  credits_monthly: number;
  active_deals: number;
  new_companies_this_month: number;
  new_contacts_this_month: number;
  avg_lead_score: number | null;
}

export interface LeadVelocityData {
  companies: TimeSeriesPoint[];
  contacts: TimeSeriesPoint[];
  period_days: number;
}

export interface ScoreDistribution {
  buckets: BreakdownItem[];
  avg_score: number;
  median_score: number;
  total_scored: number;
}

export interface CRMFunnelData {
  stages: BreakdownItem[];
  total_deals: number;
  total_value: number;
  avg_deal_value: number;
  deals_by_status: BreakdownItem[];
}

export interface IndustryBreakdown {
  companies_by_industry: BreakdownItem[];
  contacts_by_industry: BreakdownItem[];
}

export const useDashboardStats = () =>
  useQuery({
    queryKey: ["analytics", "dashboard"],
    queryFn: async () => (await get<{ data: DashboardStats }>("/analytics/dashboard")).data,
    staleTime: 5 * 60_000,
  });

export const useLeadVelocity = (days = 30) =>
  useQuery({
    queryKey: ["analytics", "lead-velocity", days],
    queryFn: async () => (await get<{ data: LeadVelocityData }>(`/analytics/lead-velocity?days=${days}`)).data,
    staleTime: 5 * 60_000,
  });

export const useScoreDistribution = () =>
  useQuery({
    queryKey: ["analytics", "score-distribution"],
    queryFn: async () => (await get<{ data: ScoreDistribution }>("/analytics/score-distribution")).data,
    staleTime: 5 * 60_000,
  });

export const useCRMFunnel = () =>
  useQuery({
    queryKey: ["analytics", "crm-funnel"],
    queryFn: async () => (await get<{ data: CRMFunnelData }>("/analytics/crm-funnel")).data,
    staleTime: 5 * 60_000,
  });

export const useIndustryBreakdown = () =>
  useQuery({
    queryKey: ["analytics", "industry"],
    queryFn: async () => (await get<{ data: IndustryBreakdown }>("/analytics/industry")).data,
    staleTime: 5 * 60_000,
  });
