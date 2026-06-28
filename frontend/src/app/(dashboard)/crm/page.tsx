"use client";

import { useState } from "react";
import {
  usePipelines,
  useDeals,
  useCreateDeal,
  useTasks,
  CRMPipeline,
} from "@/hooks/useCRM";
import Link from "next/link";
import { CheckSquare } from "lucide-react";
import { KanbanBoard } from "@/features/crm/KanbanBoard";
import { PageHeader } from "@/components/enterprise/PageHeader";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import Button from "@/components/ui/Button";

function formatCurrency(value?: number, currency = "USD") {
  if (value == null) return "-";
  return new Intl.NumberFormat("en-US", { style: "currency", currency, maximumFractionDigits: 0 }).format(value);
}

function formatDate(dateStr?: string) {
  if (!dateStr) return "-";
  return new Date(dateStr).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

interface NewDealModalProps {
  open: boolean;
  onClose: () => void;
  pipeline: CRMPipeline;
}

function NewDealModal({ open, onClose, pipeline }: NewDealModalProps) {
  const createDeal = useCreateDeal();
  const [form, setForm] = useState({
    name: "",
    value: "",
    stage_id: pipeline.stages[0]?.id ?? "",
    expected_close_date: "",
  });
  const [error, setError] = useState("");

  if (!open) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name.trim()) { setError("Deal name is required."); return; }
    try {
      await createDeal.mutateAsync({
        name: form.name,
        pipeline_id: pipeline.id,
        stage_id: form.stage_id,
        value: form.value ? parseFloat(form.value) : undefined,
        expected_close_date: form.expected_close_date || undefined,
        currency: "USD",
        status: "open",
      });
      setForm({ name: "", value: "", stage_id: pipeline.stages[0]?.id ?? "", expected_close_date: "" });
      setError("");
      onClose();
    } catch {
      setError("Failed to create deal.");
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
      <div className="bg-card border border-border rounded-2xl shadow-xl w-full max-w-md p-6">
        <div className="flex justify-between items-center mb-5">
          <h2 className="text-base font-semibold text-foreground">New Deal</h2>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground p-1 rounded-lg hover:bg-accent transition-colors">&times;</button>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-foreground mb-1.5">Deal Name *</label>
            <input
              className="input-base"
              value={form.name}
              onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
              placeholder="e.g. Acme Corp - Enterprise Plan"
              autoFocus
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-foreground mb-1.5">Value (USD)</label>
            <input
              type="number"
              className="input-base"
              value={form.value}
              onChange={e => setForm(f => ({ ...f, value: e.target.value }))}
              placeholder="0"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-foreground mb-1.5">Stage</label>
            <select
              className="input-base"
              value={form.stage_id}
              onChange={e => setForm(f => ({ ...f, stage_id: e.target.value }))}
            >
              {pipeline.stages.sort((a, b) => a.order - b.order).map(s => (
                <option key={s.id} value={s.id}>{s.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-foreground mb-1.5">Expected Close Date</label>
            <input
              type="date"
              className="input-base"
              value={form.expected_close_date}
              onChange={e => setForm(f => ({ ...f, expected_close_date: e.target.value }))}
            />
          </div>
          {error && <p className="text-destructive text-sm">{error}</p>}
          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 text-sm border border-border rounded-lg text-foreground bg-card hover:bg-accent transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={createDeal.isPending}
              className="flex-1 px-4 py-2 text-sm bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 transition-colors"
            >
              {createDeal.isPending ? "Creating..." : "Create Deal"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function CRMPage() {
  const { data: pipelines, isLoading: loadingPipelines, error: pipelineError } = usePipelines();
  const [selectedPipelineId, setSelectedPipelineId] = useState<string | undefined>(undefined);
  const [showNewDeal, setShowNewDeal] = useState(false);
  const [addDealStageId, setAddDealStageId] = useState<string | undefined>(undefined);

  const activePipeline = pipelines?.find(p => p.id === (selectedPipelineId ?? pipelines?.[0]?.id)) ?? pipelines?.[0];
  const { data: deals, isLoading: loadingDeals } = useDeals(activePipeline?.id);
  const { data: tasks } = useTasks();
  const openTasks = tasks?.filter(t => t.status !== "done") ?? [];

  if (loadingPipelines) {
    return (
      <div className="page-container space-y-6">
        <Skeleton className="h-12 w-64" />
        <Skeleton className="h-96 rounded-xl" />
      </div>
    );
  }

  if (pipelineError) {
    return (
      <div className="page-container flex min-h-[40vh] items-center justify-center">
        <p className="text-destructive text-sm font-medium">Failed to load CRM data. Please try again.</p>
      </div>
    );
  }

  if (!pipelines || pipelines.length === 0) {
    return (
      <div className="page-container flex min-h-[40vh] flex-col items-center justify-center text-center gap-3">
        <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-muted">
          <CheckSquare className="h-7 w-7 text-muted-foreground" />
        </div>
        <h2 className="text-lg font-semibold text-foreground">No pipeline found</h2>
        <p className="text-sm text-muted-foreground">Create your first pipeline to get started.</p>
      </div>
    );
  }

  const stages = activePipeline?.stages.slice().sort((a, b) => a.order - b.order) ?? [];

  return (
    <div className="page-container space-y-6">
      <PageHeader
        title="CRM Pipeline"
        description="Drag deals between stages to update your sales pipeline."
        badge={`${openTasks.length} open tasks`}
        actions={
          <Button onClick={() => setShowNewDeal(true)} size="md">
            + New Deal
          </Button>
        }
      />

      <div className="flex flex-wrap items-center gap-4">
        <select
          className="input-base text-sm"
          value={activePipeline?.id ?? ""}
          onChange={e => setSelectedPipelineId(e.target.value)}
        >
          {pipelines.map(p => (
            <option key={p.id} value={p.id}>{p.name}{p.is_default ? " (Default)" : ""}</option>
          ))}
        </select>
        <Link href="/tasks" className="text-sm font-medium text-primary hover:underline">
          View all tasks →
        </Link>
      </div>

      <KanbanBoard
        stages={stages}
        deals={deals ?? []}
        loading={loadingDeals}
        onAddDeal={(stageId) => { setAddDealStageId(stageId); setShowNewDeal(true); }}
      />

      {openTasks.length > 0 && (
        <Link href="/tasks">
          <Card className="transition-colors hover:border-primary/40">
            <CardContent className="flex items-center justify-between p-4">
              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10">
                  <CheckSquare className="h-4 w-4 text-primary" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-foreground">{openTasks.length} open tasks</p>
                  <p className="text-xs text-muted-foreground">Manage follow-ups, calls, and meetings</p>
                </div>
              </div>
              <span className="text-sm text-primary">Open tasks →</span>
            </CardContent>
          </Card>
        </Link>
      )}

      {activePipeline && (
        <NewDealModal
          open={showNewDeal}
          onClose={() => { setShowNewDeal(false); setAddDealStageId(undefined); }}
          pipeline={activePipeline}
        />
      )}
    </div>
  );
}
