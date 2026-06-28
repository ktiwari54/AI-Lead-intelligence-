'use client'

import { useState } from 'react'
import { Plus, CheckSquare } from 'lucide-react'
import { useTasks, useCreateTask, useUpdateTask, CRMTask } from '@/hooks/useCRM'
import { PageHeader } from '@/components/enterprise/PageHeader'
import { EmptyState } from '@/components/enterprise/EmptyState'
import { Card, CardContent } from '@/components/ui/card'
import Badge from '@/components/ui/Badge'
import Button from '@/components/ui/Button'
import Modal from '@/components/ui/Modal'
import { Skeleton } from '@/components/ui/skeleton'

const PRIORITY_VARIANT: Record<string, 'danger' | 'warning' | 'gray'> = {
  high: 'danger',
  medium: 'warning',
  low: 'gray',
}

const STATUS_VARIANT: Record<string, 'primary' | 'success' | 'gray' | 'warning'> = {
  todo: 'gray',
  open: 'primary',
  pending: 'warning',
  done: 'success',
}

function formatDate(dateStr?: string) {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

interface NewTaskModalProps {
  open: boolean
  onClose: () => void
}

function NewTaskModal({ open, onClose }: NewTaskModalProps) {
  const createTask = useCreateTask()
  const [form, setForm] = useState({
    title: '',
    description: '',
    task_type: 'TODO',
    priority: 'medium',
    due_at: '',
  })
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.title.trim()) {
      setError('Title is required.')
      return
    }
    try {
      await createTask.mutateAsync({
        title: form.title,
        description: form.description || undefined,
        task_type: form.task_type,
        priority: form.priority,
        due_at: form.due_at || undefined,
        status: 'todo',
      })
      setForm({ title: '', description: '', task_type: 'TODO', priority: 'medium', due_at: '' })
      setError('')
      onClose()
    } catch {
      setError('Failed to create task.')
    }
  }

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="New Task"
      footer={
        <div className="flex justify-end gap-3">
          <Button variant="secondary" onClick={onClose}>Cancel</Button>
          <Button type="submit" form="new-task-form" loading={createTask.isPending}>
            Create Task
          </Button>
        </div>
      }
    >
      <form id="new-task-form" onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="mb-1 block text-sm font-medium text-foreground">Title *</label>
          <input className="input-base w-full" value={form.title} onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))} placeholder="Task title" />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-foreground">Description</label>
          <textarea className="input-base w-full" rows={3} value={form.description} onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))} />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="mb-1 block text-sm font-medium text-foreground">Type</label>
            <select className="input-base w-full" value={form.task_type} onChange={(e) => setForm((f) => ({ ...f, task_type: e.target.value }))}>
              <option value="TODO">To-Do</option>
              <option value="CALL">Call</option>
              <option value="EMAIL">Email</option>
              <option value="MEETING">Meeting</option>
            </select>
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-foreground">Priority</label>
            <select className="input-base w-full" value={form.priority} onChange={(e) => setForm((f) => ({ ...f, priority: e.target.value }))}>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
          </div>
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-foreground">Due Date</label>
          <input type="datetime-local" className="input-base w-full" value={form.due_at} onChange={(e) => setForm((f) => ({ ...f, due_at: e.target.value }))} />
        </div>
        {error && <p className="text-sm text-destructive">{error}</p>}
      </form>
    </Modal>
  )
}

interface TasksViewProps {
  showHeader?: boolean
  filter?: 'all' | 'open' | 'done'
}

export function TasksView({ showHeader = true, filter: initialFilter = 'open' }: TasksViewProps) {
  const [filter, setFilter] = useState(initialFilter)
  const [showNewTask, setShowNewTask] = useState(false)
  const { data: tasks, isLoading } = useTasks()
  const updateTask = useUpdateTask()

  const filtered = (tasks ?? []).filter((t) => {
    if (filter === 'open') return t.status !== 'done'
    if (filter === 'done') return t.status === 'done'
    return true
  })

  return (
    <div className={showHeader ? 'page-container space-y-6' : 'space-y-4'}>
      {showHeader && (
        <PageHeader
          title="Tasks"
          description="Track calls, emails, meetings, and follow-ups across your pipeline."
          badge={`${filtered.length} tasks`}
          actions={
            <Button onClick={() => setShowNewTask(true)}>
              <Plus className="mr-2 h-4 w-4" />
              New Task
            </Button>
          }
        />
      )}

      <div className="flex gap-1 border-b border-border">
        {(['open', 'all', 'done'] as const).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`shrink-0 border-b-2 px-4 py-2.5 text-sm font-medium capitalize transition-colors ${
              filter === f ? 'border-primary text-primary' : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            {f === 'open' ? 'Open' : f}
          </button>
        ))}
      </div>

      {isLoading ? (
        <Skeleton className="h-64 rounded-xl" />
      ) : filtered.length === 0 ? (
        <EmptyState
          icon={CheckSquare}
          title="No tasks"
          description="Create tasks to track outreach, follow-ups, and meetings."
          action={{ label: 'New task', onClick: () => setShowNewTask(true) }}
        />
      ) : (
        <Card className="overflow-hidden">
          <CardContent className="p-0">
            <table className="w-full text-sm">
              <thead className="border-b border-border bg-muted/50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Title</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Type</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Priority</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Due</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Status</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((task: CRMTask) => (
                  <tr key={task.id} className="border-t border-border hover:bg-muted/30">
                    <td className="px-4 py-3 font-medium text-foreground">{task.title}</td>
                    <td className="px-4 py-3 text-muted-foreground">{task.task_type}</td>
                    <td className="px-4 py-3">
                      <Badge variant={PRIORITY_VARIANT[task.priority] ?? 'gray'}>{task.priority}</Badge>
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">{formatDate(task.due_at)}</td>
                    <td className="px-4 py-3">
                      <Badge variant={STATUS_VARIANT[task.status] ?? 'gray'}>{task.status}</Badge>
                    </td>
                    <td className="px-4 py-3">
                      {task.status !== 'done' && (
                        <button
                          onClick={() => updateTask.mutate({ id: task.id, status: 'done' })}
                          className="text-xs font-medium text-success hover:underline"
                        >
                          Mark done
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>
      )}

      <NewTaskModal open={showNewTask} onClose={() => setShowNewTask(false)} />
    </div>
  )
}