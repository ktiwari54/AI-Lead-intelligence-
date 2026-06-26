import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { get, post, patch, del } from "@/lib/api";

export interface Subscription {
  id: string;
  plan: string;
  status: string;
  credits_monthly: number;
  credits_remaining: number;
  features: Record<string, unknown>;
  period_start?: string;
  period_end?: string;
  trial_ends_at?: string;
}

export interface CreditTransaction {
  id: string;
  amount: number;
  transaction_type: string;
  balance_before: number;
  balance_after: number;
  description?: string;
  created_at: string;
}

export function useSubscription() {
  return useQuery({
    queryKey: ["billing", "subscription"],
    queryFn: async () => (await get<{ data: Subscription }>("/billing/subscription")).data,
  });
}

export function useCreditBalance() {
  return useQuery({
    queryKey: ["billing", "credits"],
    queryFn: async () =>
      get<{ data: { credits_remaining: number; credits_monthly: number; plan: string } }>("/billing/credits").then(r => r.data),
  });
}

export function useCreditTransactions(page = 1) {
  return useQuery({
    queryKey: ["billing", "transactions", page],
    queryFn: async () => get<{ items: CreditTransaction[]; total: number }>(`/billing/credits/transactions?page=${page}`),
  });
}

export function useChangePlan() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (new_plan: string) => patch("/billing/subscription/plan", { new_plan }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["billing"] }),
  });
}

export function useBillingPortal() {
  return useMutation({
    mutationFn: (return_url: string) =>
      get<{ data: { url: string } }>(`/billing/portal?return_url=${encodeURIComponent(return_url)}`).then(r => r.data.url),
    onSuccess: (url: string) => {
      window.location.href = url;
    },
  });
}
