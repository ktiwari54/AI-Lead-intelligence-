'use client'

import { useState } from 'react'
import { GitBranch, Plus, Play, Pause, Trash2, Clock, Zap, Mail, Target, Download, Brain, CheckCircle2, AlertCircle, X, Loader2 } from 'lucide-react'
import { toast } from 'sonner'
import { PageHeader } from '@/components/enterprise/PageHeader'
import { Card, CardContent } from '@/components/ui/card'
import { EmptyState } from '@/components/enterprise/EmptyState'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'

type WorkflowStatus = 'active' | 'paused' | 'draft' | 'error'
type TriggerType = 'segment_match' | 'score_threshold' | 'new_company' | 'new_contact' | 'schedule'
type ActionType = 'send_email' | 'ai_score' | 'export_csv' | 'add_to_list' | 'webhook' | 'crm_stage'

interface WorkflowStep {
  id: string
  type: 'trigger' | 'action'
  kind: TriggerType | ActionType
  label: string
  config: string
}

interface Workflow {
  id: string
  name: string
  description: string
  status: WorkflowStatus
  steps: WorkflowStep[]
  runsTotal: number
  lastRun?: string
  createdAt: string
}

const TRIGGER_OPTIONS: { value: TriggerType; label: string; icon: typeof Zap; desc: string }[] = [
  { value: 'segment_match', label: 'Segment Match', icon: Target, desc: 'When a record enters a segment' },
  { value: 'score_threshold', label: 'Score Threshold', icon: Brain, desc: 'When a lead score crosses a value' },
  { value: 'new_company', label: 'New Company', icon: Zap, desc: 'When a company is added' },
  { value: 'new_contact', label: 'New Contact', icon: Zap, desc: 'When a contact is added' },
  { value: 'schedule', label: 'Scheduled', icon: Clock, desc: 'Run on a recurring schedule' },
]

const ACTION_OPTIONS: { value: ActionType; label: string; icon: typeof Mail; desc: string }[] = [
  { value: 'ai_score', label: 'Run AI Score', icon: Brain, desc: 'Trigger lead scoring' },
  { value: 'send_email', label: 'Send Email', icon: Mail, desc: 'Send outreach via email' },
  { value: 'export_csv', label: 'Export CSV', icon: Download, desc: 'Auto-export matching records' },
  { value: 'add_to_list', label: 'Add to List', icon: Target, desc: 'Add record to a saved list' },
  { value: 'crm_stage', label: 'Move CRM Stage', icon: GitBranch, desc: 'Advance deal to next stage' },
  { value: 'webhook', label: 'Send Webhook', icon: Zap, desc: 'POST data to an endpoint' },
]

const INITIAL_WORKFLOWS: Workflow[] = [
  {
    id: '1', name: 'Score & Export High-Intent Leads', description: 'AI-score new companies and export those scoring 75+ to CRM weekly',
    status: 'active',
    steps: [
      { id: 's1', type: 'trigger', kind: 'schedule', label: 'Every Monday 9am', config: 'schedule=weekly' },
      { id: 's2', type: 'action', kind: 'ai_score', label: 'Run AI Score', config: 'entity=companies' },
      { id: 's3', type: 'action', kind: 'export_csv', label: 'Export CSV', config: 'filter=score>=75' },
    ],
    runsTotal: 24, lastRun: '2026-06-22T09:00:00Z', createdAt: '2026-04-01',
  },
  {
    id: '2', name: 'New High-Score Alert', description: 'Notify Slack when a contact scores above 80',
    status: 'active',
    steps: [
      { id: 's4', type: 'trigger', kind: 'score_threshold', label: 'Score ≥ 80', config: 'threshold=80' },
      { id: 's5', type: 'action', kind: 'webhook', label: 'Post to Slack', config: 'url=slack-webhook' },
    ],
    runsTotal: 47, lastRun: '2026-06-28T11:30:00Z', createdAt: '2026-05-15',
  },
  {
    id: '3', name: 'Auto-Nurture Segment', description: 'Add mid-score contacts to nurture list automatically',
    status: 'paused',
    steps: [
      { id: 's6', type: 'trigger', kind: 'segment_match', label: 'Segment: Needs Nurture', config: 'segment_id=seg_3' },
      { id: 's7', type: 'action', kind: 'add_to_list', label: 'Add to Nurture List', config: 'list_id=list_2' },
    ],
    runsTotal: 89, lastRun: '2026-06-20T14:00:00Z', createdAt: '2026-03-10',
  },
]

const STATUS_CONFIG: Record<WorkflowStatus, { badge: 'success' | 'warning' | 'secondary' | 'danger'; label: string }> = {
  active: { badge: 'success', label: 'Active' },
  paused: { badge: 'warning', label: 'Paused' },
  draft: { badge: 'secondary', label: 'Draft' },
  error: { badge: 'danger', label: 'Error' },
}

const STEP_ICONS: Record<string, typeof Zap> = {
  send_email: Mail, ai_score: Brain, export_csv: Download, add_to_list: Target,
  crm_stage: GitBranch, webhook: Zap, segment_match: Target, score_threshold: Brain,
  new_company: Zap, new_contact: Zap, schedule: Clock,
}

function relativeTime(iso: string) {
  const diff = Date.now() - new Date(iso).getTime()
  const d = Math.floor(diff / 86400000)
  const h = Math.floor(diff / 3600000)
  if (d > 0) return `${d}d ago`
  return `${h}h ago`
}

interface CreateWorkflowModalProps { open: boolean; onClose: () => void; onCreate: (w: Workflow) => void }

function CreateWorkflowModal({ open, onClose, onCreate }: CreateWorkflowModalProps) {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [trigger, setTrigger] = useState<TriggerType>('new_company')
  const [actions, setActions] = useState<ActionType[]>(['ai_score'])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  if (!open) return null

  const toggleAction = (a: ActionType) =>
    setActions(prev => prev.includes(a) ? prev.filter(x => x !== a) : [...prev, a])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!name.trim()) { setError('Workflow name is required.'); return }
    if (actions.length === 0) { setError('Add at least one action.'); return }
    setLoading(true)
    await new Promise(r => setTimeout(r, 800))
    const tOpt = TRIGGER_OPTIONS.find(t => t.value === trigger)!
    const steps: WorkflowStep[] = [
      { id: 't1', type: 'trigger', kind: trigger, label: tOpt.label, config: '' },
      ...actions.map((a, i) => {
        const aOpt = ACTION_OPTIONS.find(o => o.value === a)!
        return { id: `a${i}`, type: 'action' as const, kind: a, label: aOpt.label, config: '' }
      }),
    ]
    onCreate({ id: Date.now().toString(), name: name.trim(), description: description.trim(), status: 'draft', steps, runsTotal: 0, createdAt: new Date().toISOString().split('T')[0] })
    setLoading(false)
    onClose()
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
      <div className="w-full max-w-lg rounded-2xl border border-border bg-card shadow-xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between border-b border-border px-6 py-4 sticky top-0 bg-card z-10">
          <h2 className="text-base font-semibold text-foreground">Create Workflow</h2>
          <button onClick={onClose} className="rounded-lg p-1 text-muted-foreground hover:bg-accent hover:text-foreground transition-colors">
            <X className="h-4 w-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          <div>
            <label className="mb-1.5 block text-sm font-medium text-foreground">Workflow Name *</label>
            <input className="input-base" value={name} onChange={e => setName(e.target.value)} placeholder="e.g. Auto-score new companies" autoFocus />
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium text-foreground">Description</label>
            <input className="input-base" value={description} onChange={e => setDescription(e.target.value)} placeholder="What does this workflow do?" />
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium text-foreground">Trigger</label>
            <div className="space-y-2">
              {TRIGGER_OPTIONS.map(opt => {
                const Icon = opt.icon
                return (
                  <button key={opt.value} type="button" onClick={() => setTrigger(opt.value)}
                    className={`w-full flex items-center gap-3 rounded-xl border px-4 py-3 text-left transition-colors ${trigger === opt.value ? 'border-primary bg-primary/5' : 'border-border hover:border-primary/40'}`}>
                    <Icon className={`h-4 w-4 shrink-0 ${trigger === opt.value ? 'text-primary' : 'text-muted-foreground'}`} />
                    <div>
                      <p className="text-sm font-medium text-foreground">{opt.label}</p>
                      <p className="text-xs text-muted-foreground">{opt.desc}</p>
                    </div>
                    {trigger === opt.value && <CheckCircle2 className="ml-auto h-4 w-4 text-primary" />}
                  </button>
                )
              })}
            </div>
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium text-foreground">Actions (select one or more)</label>
            <div className="grid grid-cols-2 gap-2">
              {ACTION_OPTIONS.map(opt => {
                const Icon = opt.icon
                const selected = actions.includes(opt.value)
                return (
                  <button key={opt.value} type="button" onClick={() => toggleAction(opt.value)}
                    className={`flex items-center gap-2 rounded-xl border px-3 py-2.5 text-left transition-colors ${selected ? 'border-primary bg-primary/5' : 'border-border hover:border-primary/40'}`}>
                    <Icon className={`h-4 w-4 shrink-0 ${selected ? 'text-primary' : 'text-muted-foreground'}`} />
                    <span className="text-sm font-medium text-foreground">{opt.label}</span>
                  </button>
                )
              })}
            </div>
          </div>

          {error && <p className="text-xs text-destructive">{error}</p>}

          <div className="flex gap-3 border-t border-border pt-4">
            <Button type="button" variant="outline" className="flex-1" onClick={onClose}>Cancel</Button>
            <Button type="submit" className="flex-1" disabled={loading}>
              {loading ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Creating...</> : 'Create Draft'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default function WorkflowsPage() {
  const [workflows, setWorkflows] = useState(INITIAL_WORKFLOWS)
  const [createOpen, setCreateOpen] = useState(false)

  const toggleStatus = (id: string) => {
    setWorkflows(prev => prev.map(w => {
      if (w.id !== id) return w
      const next = w.status === 'active' ? 'paused' : w.status === 'paused' ? 'active' : w.status
      toast.success(`"${w.name}" ${next === 'active' ? 'resumed' : 'paused'}`)
      return { ...w, status: next }
    }))
  }

  const handleDelete = (id: string, name: string) => {
    setWorkflows(prev => prev.filter(w => w.id !== id))
    toast.success(`"${name}" deleted`)
  }

  const handleActivate = (id: string) => {
    setWorkflows(prev => prev.map(w => w.id === id ? { ...w, status: 'active' } : w))
    toast.success('Workflow activated')
  }

  return (
    <div className="page-container space-y-6">
      <PageHeader
        title="Workflow Builder"
        description="Automate lead scoring, exports, CRM updates, and outreach with trigger-based workflows."
        badge={`${workflows.filter(w => w.status === 'active').length} active`}
        actions={
          <Button onClick={() => setCreateOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            New Workflow
          </Button>
        }
      />

      {workflows.length === 0 ? (
        <EmptyState
          icon={GitBranch}
          title="No workflows yet"
          description="Automate repetitive tasks with trigger-based workflows."
          action={{ label: 'Create Workflow', onClick: () => setCreateOpen(true) }}
        />
      ) : (
        <div className="space-y-4">
          {workflows.map(w => {
            const s = STATUS_CONFIG[w.status]
            return (
              <Card key={w.id} className="group transition-colors hover:border-primary/30">
                <CardContent className="p-5">
                  <div className="flex items-start gap-4">
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary/10">
                      <GitBranch className="h-5 w-5 text-primary" />
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex flex-wrap items-center gap-2 mb-1">
                        <p className="font-semibold text-foreground">{w.name}</p>
                        <Badge variant={s.badge} className="text-[10px]">{s.label}</Badge>
                      </div>
                      {w.description && <p className="text-sm text-muted-foreground mb-3">{w.description}</p>}

                      {/* Step flow */}
                      <div className="flex flex-wrap items-center gap-1.5">
                        {w.steps.map((step, i) => {
                          const Icon = STEP_ICONS[step.kind] ?? Zap
                          return (
                            <div key={step.id} className="flex items-center gap-1.5">
                              {i > 0 && <span className="text-muted-foreground text-xs">→</span>}
                              <div className={`inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-1 text-xs font-medium ${step.type === 'trigger' ? 'border-amber-200 bg-amber-50 text-amber-700 dark:border-amber-900 dark:bg-amber-950 dark:text-amber-300' : 'border-border bg-muted/50 text-foreground'}`}>
                                <Icon className="h-3 w-3" />
                                {step.label}
                              </div>
                            </div>
                          )
                        })}
                      </div>

                      <div className="mt-3 flex items-center gap-4 text-xs text-muted-foreground">
                        <span>{w.runsTotal} runs total</span>
                        {w.lastRun && <span>Last run {relativeTime(w.lastRun)}</span>}
                        <span>Created {w.createdAt}</span>
                      </div>
                    </div>

                    <div className="flex shrink-0 items-center gap-2 opacity-0 transition-opacity group-hover:opacity-100">
                      {w.status === 'draft' ? (
                        <Button size="sm" onClick={() => handleActivate(w.id)}>Activate</Button>
                      ) : (
                        <button
                          onClick={() => toggleStatus(w.id)}
                          className="rounded-lg p-1.5 text-muted-foreground hover:bg-accent hover:text-foreground transition-colors"
                          title={w.status === 'active' ? 'Pause' : 'Resume'}
                        >
                          {w.status === 'active' ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                        </button>
                      )}
                      <button
                        onClick={() => handleDelete(w.id, w.name)}
                        className="rounded-lg p-1.5 text-muted-foreground hover:bg-destructive/10 hover:text-destructive transition-colors"
                        title="Delete"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}

      <CreateWorkflowModal
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onCreate={w => {
          setWorkflows(prev => [w, ...prev])
          toast.success(`"${w.name}" created as draft — activate when ready`)
        }}
      />
    </div>
  )
}
