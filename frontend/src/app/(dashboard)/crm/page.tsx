"use client";

import { useState } from "react";
import {
  usePipelines,
  useDeals,
  useCreateDeal,
  useUpdateDeal,
  useTasks,
  useCreateTask,
  useUpdateTask,
  CRMDeal,
  CRMTask,
  CRMPipeline,
} from "@/hooks/useCRM";

function formatCurrency(value?: number, currency = "USD") {
  if (value == null) return "-";
  return new Intl.NumberFormat("en-US", { style: "currency", currency, maximumFractionDigits: 0 }).format(value);
}

function formatDate(dateStr?: string) {
  if (!dateStr) return "-";
  return new Date(dateStr).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

const PRIORITY_COLORS: Record<string, string> = {
  low: "bg-gray-100 text-gray-700",
  medium: "bg-yellow-100 text-yellow-700",
  high: "bg-red-100 text-red-700",
};

const STATUS_COLORS: Record<string, string> = {
  open: "bg-blue-100 text-blue-700",
  won: "bg-green-100 text-green-700",
  lost: "bg-red-100 text-red-700",
  pending: "bg-yellow-100 text-yellow-700",
  done: "bg-green-100 text-green-700",
  todo: "bg-gray-100 text-gray-700",
};

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
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold text-gray-900">New Deal</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl leading-none">&times;</button>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Deal Name *</label>
            <input
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              value={form.name}
              onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
              placeholder="e.g. Acme Corp - Enterprise Plan"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Value (USD)</label>
            <input
              type="number"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              value={form.value}
              onChange={e => setForm(f => ({ ...f, value: e.target.value }))}
              placeholder="0"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Stage</label>
            <select
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              value={form.stage_id}
              onChange={e => setForm(f => ({ ...f, stage_id: e.target.value }))}
            >
              {pipeline.stages.sort((a, b) => a.order - b.order).map(s => (
                <option key={s.id} value={s.id}>{s.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Expected Close Date</label>
            <input
              type="date"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              value={form.expected_close_date}
              onChange={e => setForm(f => ({ ...f, expected_close_date: e.target.value }))}
            />
          </div>
          {error && <p className="text-red-600 text-sm">{error}</p>}
          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 text-sm border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={createDeal.isPending}
              className="flex-1 px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
            >
              {createDeal.isPending ? "Creating..." : "Create Deal"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

interface NewTaskModalProps {
  open: boolean;
  onClose: () => void;
}

function NewTaskModal({ open, onClose }: NewTaskModalProps) {
  const createTask = useCreateTask();
  const [form, setForm] = useState({
    title: "",
    description: "",
    task_type: "TODO",
    priority: "medium",
    due_at: "",
  });
  const [error, setError] = useState("");

  if (!open) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.title.trim()) { setError("Title is required."); return; }
    try {
      await createTask.mutateAsync({
        title: form.title,
        description: form.description || undefined,
        task_type: form.task_type,
        priority: form.priority,
        due_at: form.due_at || undefined,
        status: "todo",
      });
      setForm({ title: "", description: "", task_type: "TODO", priority: "medium", due_at: "" });
      setError("");
      onClose();
    } catch {
      setError("Failed to create task.");
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold text-gray-900">New Task</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl leading-none">&times;</button>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Title *</label>
            <input
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              value={form.title}
              onChange={e => setForm(f => ({ ...f, title: e.target.value }))}
              placeholder="Task title"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <textarea
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              rows={3}
              value={form.description}
              onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
              placeholder="Optional description"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
              <select
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                value={form.task_type}
                onChange={e => setForm(f => ({ ...f, task_type: e.target.value }))}
              >
                <option value="TODO">To-Do</option>
                <option value="CALL">Call</option>
                <option value="EMAIL">Email</option>
                <option value="MEETING">Meeting</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Priority</label>
              <select
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                value={form.priority}
                onChange={e => setForm(f => ({ ...f, priority: e.target.value }))}
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
              </select>
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Due Date</label>
            <input
              type="datetime-local"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              value={form.due_at}
              onChange={e => setForm(f => ({ ...f, due_at: e.target.value }))}
            />
          </div>
          {error && <p className="text-red-600 text-sm">{error}</p>}
          <div className="flex gap-3 pt-2">
            <button type="button" onClick={onClose} className="flex-1 px-4 py-2 text-sm border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50">Cancel</button>
            <button type="submit" disabled={createTask.isPending} className="flex-1 px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50">
              {createTask.isPending ? "Creating..." : "Create Task"}
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
  const [showNewTask, setShowNewTask] = useState(false);
  const [addDealStageId, setAddDealStageId] = useState<string | undefined>(undefined);

  const activePipeline = pipelines?.find(p => p.id === (selectedPipelineId ?? pipelines?.[0]?.id)) ?? pipelines?.[0];
  const { data: deals, isLoading: loadingDeals } = useDeals(activePipeline?.id);
  const { data: tasks, isLoading: loadingTasks } = useTasks();
  const updateTask = useUpdateTask();

  const openTasks = tasks?.filter(t => t.status !== "done") ?? [];

  if (loadingPipelines) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" />
      </div>
    );
  }

  if (pipelineError) {
    return (
      <div className="p-8 text-center text-red-600">
        Failed to load CRM data. Please try again.
      </div>
    );
  }

  if (!pipelines || pipelines.length === 0) {
    return (
      <div className="p-8 text-center">
        <div className="text-gray-400 text-5xl mb-4">📋</div>
        <h2 className="text-xl font-semibold text-gray-700 mb-2">No pipeline found.</h2>
        <p className="text-gray-500">Create your first pipeline to get started.</p>
      </div>
    );
  }

  const stages = activePipeline?.stages.slice().sort((a, b) => a.order - b.order) ?? [];

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">CRM</h1>
        <button
          onClick={() => setShowNewDeal(true)}
          className="px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700"
        >
          + New Deal
        </button>
      </div>

      {/* Pipeline selector */}
      <div className="mb-4">
        <select
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          value={activePipeline?.id ?? ""}
          onChange={e => setSelectedPipelineId(e.target.value)}
        >
          {pipelines.map(p => (
            <option key={p.id} value={p.id}>{p.name}{p.is_default ? " (Default)" : ""}</option>
          ))}
        </select>
      </div>

      {/* Kanban board */}
      <div className="flex gap-4 overflow-x-auto pb-4 flex-1 min-h-0">
        {stages.map(stage => {
          const stageDeals = deals?.filter(d => d.stage_id === stage.id) ?? [];
          return (
            <div key={stage.id} className="flex-shrink-0 w-72 bg-gray-50 rounded-xl flex flex-col">
              {/* Column header */}
              <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200">
                <span className="font-medium text-gray-800 text-sm">{stage.name}</span>
                <span className="text-xs font-semibold bg-gray-200 text-gray-600 rounded-full px-2 py-0.5">
                  {stageDeals.length}
                </span>
              </div>

              {/* Deal cards */}
              <div className="flex-1 overflow-y-auto p-3 space-y-2">
                {loadingDeals ? (
                  <div className="flex justify-center py-4">
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-indigo-600" />
                  </div>
                ) : stageDeals.length === 0 ? (
                  <p className="text-center text-gray-400 text-xs py-4">No deals</p>
                ) : (
                  stageDeals.map(deal => (
                    <div key={deal.id} className="bg-white rounded-lg p-3 shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
                      <p className="font-medium text-gray-900 text-sm mb-1 truncate">{deal.name}</p>
                      {deal.value != null && (
                        <p className="text-indigo-600 font-semibold text-sm">{formatCurrency(deal.value, deal.currency)}</p>
                      )}
                      {deal.company_id && (
                        <p className="text-xs text-gray-500 mt-1 truncate">Company: {deal.company_id}</p>
                      )}
                      <div className="flex items-center justify-between mt-2">
                        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${STATUS_COLORS[deal.status] ?? "bg-gray-100 text-gray-600"}`}>
                          {deal.status}
                        </span>
                        {deal.expected_close_date && (
                          <span className="text-xs text-gray-400">{formatDate(deal.expected_close_date)}</span>
                        )}
                      </div>
                    </div>
                  ))
                )}
              </div>

              {/* Add deal button */}
              <button
                onClick={() => { setAddDealStageId(stage.id); setShowNewDeal(true); }}
                className="m-3 text-sm text-gray-500 hover:text-indigo-600 border border-dashed border-gray-300 hover:border-indigo-400 rounded-lg py-2 transition-colors"
              >
                + Add Deal
              </button>
            </div>
          );
        })}
      </div>

      {/* Tasks section */}
      <div className="mt-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Open Tasks</h2>
          <button
            onClick={() => setShowNewTask(true)}
            className="px-3 py-1.5 bg-white border border-gray-300 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-50"
          >
            + New Task
          </button>
        </div>

        {loadingTasks ? (
          <div className="flex justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" />
          </div>
        ) : openTasks.length === 0 ? (
          <div className="text-center py-8 text-gray-400">No open tasks</div>
        ) : (
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-4 py-3 text-left font-medium text-gray-600">Title</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-600">Type</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-600">Priority</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-600">Due Date</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-600">Status</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-600">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {openTasks.map(task => (
                  <tr key={task.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium text-gray-900">{task.title}</td>
                    <td className="px-4 py-3 text-gray-600">{task.task_type}</td>
                    <td className="px-4 py-3">
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${PRIORITY_COLORS[task.priority] ?? "bg-gray-100 text-gray-600"}`}>
                        {task.priority}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-600">{formatDate(task.due_at)}</td>
                    <td className="px-4 py-3">
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${STATUS_COLORS[task.status] ?? "bg-gray-100 text-gray-600"}`}>
                        {task.status}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <button
                        onClick={() => updateTask.mutate({ id: task.id, status: "done" })}
                        className="text-xs text-green-600 hover:text-green-800 font-medium"
                      >
                        Mark Done
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modals */}
      {activePipeline && (
        <NewDealModal
          open={showNewDeal}
          onClose={() => { setShowNewDeal(false); setAddDealStageId(undefined); }}
          pipeline={activePipeline}
        />
      )}
      <NewTaskModal open={showNewTask} onClose={() => setShowNewTask(false)} />
    </div>
  );
}
