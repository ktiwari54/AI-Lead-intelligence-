import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { get, post, patch, del } from "@/lib/api";

export interface CRMPipeline {
  id: string;
  name: string;
  description?: string;
  is_default: boolean;
  stages: CRMStage[];
  created_at: string;
}

export interface CRMStage {
  id: string;
  pipeline_id: string;
  name: string;
  order: number;
  probability: number;
}

export interface CRMDeal {
  id: string;
  pipeline_id: string;
  stage_id: string;
  contact_id?: string;
  company_id?: string;
  name: string;
  value?: number;
  currency: string;
  status: string;
  expected_close_date?: string;
  created_at: string;
}

export interface CRMTask {
  id: string;
  deal_id?: string;
  contact_id?: string;
  title: string;
  description?: string;
  task_type: string;
  status: string;
  priority: string;
  due_at?: string;
  completed_at?: string;
  created_at: string;
}

export function usePipelines() {
  return useQuery({
    queryKey: ["crm", "pipelines"],
    queryFn: async () => (await get<{ data: CRMPipeline[]; items?: CRMPipeline[] }>("/crm/pipelines")).data ?? [],
  });
}

export function useDeals(pipelineId?: string) {
  return useQuery({
    queryKey: ["crm", "deals", pipelineId],
    queryFn: async () => {
      const url = pipelineId ? `/crm/deals?pipeline_id=${pipelineId}` : "/crm/deals";
      const res = await get<{ data?: CRMDeal[]; items?: CRMDeal[] }>(url);
      return res.data ?? res.items ?? [];
    },
  });
}

export function useCreateDeal() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<CRMDeal>) => post("/crm/deals", data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["crm", "deals"] }),
  });
}

export function useUpdateDeal() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...data }: Partial<CRMDeal> & { id: string }) =>
      patch(`/crm/deals/${id}`, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["crm", "deals"] }),
  });
}

export function useDeleteDeal() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => del(`/crm/deals/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["crm", "deals"] }),
  });
}

export function useTasks() {
  return useQuery({
    queryKey: ["crm", "tasks"],
    queryFn: async () => {
      const res = await get<{ data?: CRMTask[]; items?: CRMTask[] }>("/crm/tasks");
      return res.data ?? res.items ?? [];
    },
  });
}

export function useCreateTask() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<CRMTask>) => post("/crm/tasks", data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["crm", "tasks"] }),
  });
}

export function useUpdateTask() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...data }: Partial<CRMTask> & { id: string }) =>
      patch(`/crm/tasks/${id}`, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["crm", "tasks"] }),
  });
}

export function useCreatePipeline() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: { name: string; description?: string; stages: { name: string; order: number; probability: number }[] }) =>
      post("/crm/pipelines", data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["crm", "pipelines"] }),
  });
}
