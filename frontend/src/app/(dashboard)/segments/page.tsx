'use client'

import { useState } from 'react'
import { Target, Sparkles, Plus, Trash2, RefreshCw, Loader2, X, ChevronDown } from 'lucide-react'
import { toast } from 'sonner'
import { PageHeader } from '@/components/enterprise/PageHeader'
import { Card, CardContent } from '@/components/ui/card'
import { EmptyState } from '@/components/enterprise/EmptyState'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'

interface SegmentRule {
  id: string
  field: string
  operator: string
  value: string
}

interface Segment {
  id: string
  name: string
  description: string
  rules: SegmentRule[]
  count: number
  autoSync: boolean
  updatedAt: string
}

const INITIAL_SEGMENTS: Segment[] = [
  {
    id: '1', name: 'High-intent SaaS', description: 'SaaS companies with strong lead scores',
    rules: [{ id: 'r1', field: 'industry', operator: 'equals', value: 'SaaS' }, { id: 'r2', field: 'score', operator: 'gte', value: '75' }],
    count: 284, autoSync: true, updatedAt: '2026-06-28',
  },
  {
    id: '2', name: 'Enterprise 500+', description: 'Large enterprise companies in the US',
    rules: [{ id: 'r3', field: 'employee_count', operator: 'gte', value: '500' }, { id: 'r4', field: 'country', operator: 'equals', value: 'US' }],
    count: 156, autoSync: true, updatedAt: '2026-06-26',
  },
  {
    id: '3', name: 'Needs nurture', description: 'Mid-score contacted leads pending follow-up',
    rules: [{ id: 'r5', field: 'score', operator: 'between', value: '50-74' }, { id: 'r6', field: 'status', operator: 'equals', value: 'contacted' }],
    count: 412, autoSync: true, updatedAt: '2026-06-24',
  },
]

const FIELDS = [
  { value: 'industry', label: 'Industry' },
  { value: 'country', label: 'Country' },
  { value: 'employee_count', label: 'Employee Count' },
  { value: 'annual_revenue', label: 'Annual Revenue' },
  { value: 'score', label: 'Lead Score' },
  { value: 'status', label: 'Status' },
  { value: 'founded_year', label: 'Founded Year' },
  { value: 'department', label: 'Department' },
]

const OPERATORS = [
  { value: 'equals', label: 'equals' },
  { value: 'not_equals', label: 'does not equal' },
  { value: 'gte', label: 'is greater than or equal to' },
  { value: 'lte', label: 'is less than or equal to' },
  { value: 'contains', label: 'contains' },
  { value: 'between', label: 'is between' },
]

function ruleToText(rule: SegmentRule) {
  const field = FIELDS.find(f => f.value === rule.field)?.label ?? rule.field
  const op = OPERATORS.find(o => o.value === rule.operator)?.label ?? rule.operator
  return `${field} ${op} ${rule.value}`
}

interface CreateSegmentModalProps {
  open: boolean
  onClose: () => void
  onCreate: (seg: Segment) => void
}

function CreateSegmentModal({ open, onClose, onCreate }: CreateSegmentModalProps) {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [rules, setRules] = useState<SegmentRule[]>([{ id: '1', field: 'industry', operator: 'equals', value: '' }])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  if (!open) return null

  const addRule = () => setRules(r => [...r, { id: Date.now().toString(), field: 'industry', operator: 'equals', value: '' }])
  const removeRule = (id: string) => setRules(r => r.filter(x => x.id !== id))
  const updateRule = (id: string, key: keyof SegmentRule, val: string) =>
    setRules(r => r.map(x => x.id === id ? { ...x, [key]: val } : x))

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!name.trim()) { setError('Segment name is required.'); return }
    if (rules.some(r => !r.value.trim())) { setError('All rules must have a value.'); return }
    setLoading(true)
    await new Promise(r => setTimeout(r, 700))
    onCreate({
      id: Date.now().toString(),
      name: name.trim(),
      description: description.trim(),
      rules,
      count: Math.floor(Math.random() * 300) + 10,
      autoSync: true,
      updatedAt: new Date().toISOString().split('T')[0],
    })
    setLoading(false)
    onClose()
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
      <div className="w-full max-w-lg rounded-2xl border border-border bg-card shadow-xl">
        <div className="flex items-center justify-between border-b border-border px-6 py-4">
          <h2 className="text-base font-semibold text-foreground">Create Segment</h2>
          <button onClick={onClose} className="rounded-lg p-1 text-muted-foreground hover:bg-accent hover:text-foreground transition-colors">
            <X className="h-4 w-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          <div>
            <label className="mb-1.5 block text-sm font-medium text-foreground">Segment Name *</label>
            <input
              className="input-base"
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="e.g. High-intent SaaS"
              autoFocus
            />
          </div>

          <div>
            <label className="mb-1.5 block text-sm font-medium text-foreground">Description</label>
            <input
              className="input-base"
              value={description}
              onChange={e => setDescription(e.target.value)}
              placeholder="Brief description of this segment"
            />
          </div>

          <div>
            <div className="mb-2 flex items-center justify-between">
              <label className="text-sm font-medium text-foreground">Filter Rules</label>
              <span className="text-xs text-muted-foreground">Records match ALL rules</span>
            </div>

            <div className="space-y-2">
              {rules.map((rule, i) => (
                <div key={rule.id} className="flex items-center gap-2">
                  {i > 0 && (
                    <span className="w-8 shrink-0 text-center text-xs font-medium text-muted-foreground">AND</span>
                  )}
                  {i === 0 && <span className="w-8 shrink-0 text-center text-xs font-medium text-primary">IF</span>}

                  <select
                    className="input-base flex-1 text-sm"
                    value={rule.field}
                    onChange={e => updateRule(rule.id, 'field', e.target.value)}
                  >
                    {FIELDS.map(f => <option key={f.value} value={f.value}>{f.label}</option>)}
                  </select>

                  <select
                    className="input-base flex-1 text-sm"
                    value={rule.operator}
                    onChange={e => updateRule(rule.id, 'operator', e.target.value)}
                  >
                    {OPERATORS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
                  </select>

                  <input
                    className="input-base flex-1 text-sm"
                    value={rule.value}
                    onChange={e => updateRule(rule.id, 'value', e.target.value)}
                    placeholder="value"
                  />

                  <button
                    type="button"
                    onClick={() => removeRule(rule.id)}
                    disabled={rules.length === 1}
                    className="shrink-0 rounded-lg p-1.5 text-muted-foreground hover:bg-destructive/10 hover:text-destructive disabled:opacity-30 transition-colors"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              ))}
            </div>

            <button
              type="button"
              onClick={addRule}
              className="mt-2 flex items-center gap-1.5 text-xs font-medium text-primary hover:underline"
            >
              <Plus className="h-3.5 w-3.5" /> Add rule
            </button>
          </div>

          {error && <p className="text-xs text-destructive">{error}</p>}

          <div className="flex gap-3 border-t border-border pt-4">
            <Button type="button" variant="outline" className="flex-1" onClick={onClose}>Cancel</Button>
            <Button type="submit" className="flex-1" disabled={loading}>
              {loading ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Creating...</> : 'Create Segment'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default function SegmentsPage() {
  const [segments, setSegments] = useState<Segment[]>(INITIAL_SEGMENTS)
  const [createOpen, setCreateOpen] = useState(false)
  const [syncing, setSyncing] = useState<string | null>(null)

  const handleSync = async (id: string, name: string) => {
    setSyncing(id)
    await new Promise(r => setTimeout(r, 1200))
    setSyncing(null)
    toast.success(`"${name}" synced — ${Math.floor(Math.random() * 50) + 1} new records added`)
  }

  const handleDelete = (id: string, name: string) => {
    setSegments(prev => prev.filter(s => s.id !== id))
    toast.success(`"${name}" deleted`)
  }

  return (
    <div className="page-container space-y-6">
      <PageHeader
        title="Segments"
        description="Dynamic audiences that auto-update whenever records match your filter criteria."
        badge={`${segments.length} active`}
        actions={
          <Button onClick={() => setCreateOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Create Segment
          </Button>
        }
      />

      {segments.length === 0 ? (
        <EmptyState
          icon={Target}
          title="No segments yet"
          description="Create dynamic audiences that auto-refresh as your data changes."
          action={{ label: 'Create Segment', onClick: () => setCreateOpen(true) }}
        />
      ) : (
        <div className="space-y-3">
          {segments.map(seg => (
            <Card key={seg.id} className="group transition-colors hover:border-primary/30">
              <CardContent className="p-5">
                <div className="flex items-start gap-4">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary/10">
                    <Target className="h-5 w-5 text-primary" />
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <p className="font-semibold text-foreground">{seg.name}</p>
                      {seg.autoSync && <Badge variant="primary" className="text-[10px]">Auto-sync</Badge>}
                    </div>
                    {seg.description && (
                      <p className="mt-0.5 text-sm text-muted-foreground">{seg.description}</p>
                    )}
                    <div className="mt-2 flex flex-wrap gap-1.5">
                      {seg.rules.map(rule => (
                        <span key={rule.id} className="inline-flex items-center rounded-md border border-border bg-muted/50 px-2 py-0.5 text-xs text-muted-foreground">
                          {ruleToText(rule)}
                        </span>
                      ))}
                    </div>
                    <p className="mt-2 text-xs text-muted-foreground">Updated {seg.updatedAt}</p>
                  </div>

                  <div className="flex shrink-0 items-center gap-4">
                    <div className="text-right">
                      <p className="text-2xl font-bold text-foreground">{seg.count.toLocaleString()}</p>
                      <p className="text-xs text-muted-foreground">records</p>
                    </div>

                    <div className="flex flex-col gap-1 opacity-0 transition-opacity group-hover:opacity-100">
                      <button
                        onClick={() => handleSync(seg.id, seg.name)}
                        disabled={syncing === seg.id}
                        className="rounded-lg p-1.5 text-muted-foreground hover:bg-accent hover:text-foreground disabled:opacity-50 transition-colors"
                        title="Sync now"
                      >
                        {syncing === seg.id
                          ? <Loader2 className="h-3.5 w-3.5 animate-spin" />
                          : <RefreshCw className="h-3.5 w-3.5" />}
                      </button>
                      <button
                        onClick={() => handleDelete(seg.id, seg.name)}
                        className="rounded-lg p-1.5 text-muted-foreground hover:bg-destructive/10 hover:text-destructive transition-colors"
                        title="Delete segment"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}

          <button
            onClick={() => setCreateOpen(true)}
            className="flex w-full items-center justify-center gap-2 rounded-xl border-2 border-dashed border-border py-4 text-sm font-medium text-muted-foreground transition-colors hover:border-primary/40 hover:text-primary"
          >
            <Plus className="h-4 w-4" /> New Segment
          </button>
        </div>
      )}

      <Card className="border-dashed">
        <CardContent className="flex items-center gap-3 p-5 text-sm text-muted-foreground">
          <Sparkles className="h-5 w-5 shrink-0 text-primary" />
          Segments power targeted discovery, batch scoring, and scheduled exports. Records are evaluated every 6 hours.
        </CardContent>
      </Card>

      <CreateSegmentModal
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onCreate={seg => {
          setSegments(prev => [seg, ...prev])
          toast.success(`"${seg.name}" created — syncing ${seg.count} records`)
        }}
      />
    </div>
  )
}
