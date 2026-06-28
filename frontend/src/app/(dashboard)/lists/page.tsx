'use client'

import { useState } from 'react'
import Link from 'next/link'
import { List, Plus, Building2, Users, MoreHorizontal, Trash2, Download, Loader2, X } from 'lucide-react'
import { toast } from 'sonner'
import { PageHeader } from '@/components/enterprise/PageHeader'
import { Card, CardContent } from '@/components/ui/card'
import { EmptyState } from '@/components/enterprise/EmptyState'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'

interface SavedList {
  id: string
  name: string
  description: string
  entities: number
  type: 'company' | 'contact' | 'mixed'
  updatedAt: string
  createdBy: string
}

const INITIAL_LISTS: SavedList[] = [
  { id: '1', name: 'Q3 Enterprise Targets', description: 'High-value enterprise companies for Q3 outreach', entities: 142, type: 'company', updatedAt: '2026-06-27', createdBy: 'Alex Chen' },
  { id: '2', name: 'SaaS VP Sales', description: 'VP-level sales contacts at SaaS companies', entities: 58, type: 'contact', updatedAt: '2026-06-25', createdBy: 'Jordan Lee' },
  { id: '3', name: 'Austin Fintech', description: 'Fintech companies headquartered in Austin, TX', entities: 31, type: 'company', updatedAt: '2026-06-20', createdBy: 'Alex Chen' },
]

interface CreateListModalProps {
  open: boolean
  onClose: () => void
  onCreate: (list: SavedList) => void
}

function CreateListModal({ open, onClose, onCreate }: CreateListModalProps) {
  const [form, setForm] = useState({ name: '', description: '', type: 'company' as 'company' | 'contact' | 'mixed' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  if (!open) return null

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.name.trim()) { setError('List name is required.'); return }
    setLoading(true)
    await new Promise(r => setTimeout(r, 600))
    onCreate({
      id: Date.now().toString(),
      name: form.name.trim(),
      description: form.description.trim(),
      entities: 0,
      type: form.type,
      updatedAt: new Date().toISOString().split('T')[0],
      createdBy: 'You',
    })
    setForm({ name: '', description: '', type: 'company' })
    setError('')
    setLoading(false)
    onClose()
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
      <div className="w-full max-w-md rounded-2xl border border-border bg-card p-6 shadow-xl">
        <div className="mb-5 flex items-center justify-between">
          <h2 className="text-base font-semibold text-foreground">Create List</h2>
          <button onClick={onClose} className="rounded-lg p-1 text-muted-foreground hover:bg-accent hover:text-foreground transition-colors">
            <X className="h-4 w-4" />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="mb-1.5 block text-sm font-medium text-foreground">List Name *</label>
            <input
              className="input-base"
              value={form.name}
              onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
              placeholder="e.g. Q4 Enterprise Targets"
              autoFocus
            />
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium text-foreground">Description</label>
            <textarea
              className="input-base min-h-[80px] resize-none"
              value={form.description}
              onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
              placeholder="What is this list for?"
            />
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium text-foreground">Record Type</label>
            <div className="grid grid-cols-3 gap-2">
              {(['company', 'contact', 'mixed'] as const).map(type => (
                <button
                  key={type}
                  type="button"
                  onClick={() => setForm(f => ({ ...f, type }))}
                  className={`rounded-lg border px-3 py-2 text-sm font-medium transition-colors capitalize ${
                    form.type === type
                      ? 'border-primary bg-primary/10 text-primary'
                      : 'border-border bg-card text-muted-foreground hover:border-primary/40'
                  }`}
                >
                  {type}
                </button>
              ))}
            </div>
          </div>
          {error && <p className="text-xs text-destructive">{error}</p>}
          <div className="flex gap-3 pt-1">
            <Button type="button" variant="outline" className="flex-1" onClick={onClose}>Cancel</Button>
            <Button type="submit" className="flex-1" disabled={loading}>
              {loading ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Creating...</> : 'Create List'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default function ListsPage() {
  const [lists, setLists] = useState<SavedList[]>(INITIAL_LISTS)
  const [createOpen, setCreateOpen] = useState(false)

  const handleDelete = (id: string, name: string) => {
    setLists(prev => prev.filter(l => l.id !== id))
    toast.success(`"${name}" deleted`)
  }

  const handleExport = (name: string) => {
    toast.success(`Exporting "${name}"...`)
  }

  return (
    <div className="page-container space-y-6">
      <PageHeader
        title="Lists"
        description="Static collections of companies and contacts for campaigns, outreach, and exports."
        badge={`${lists.length} lists`}
        actions={
          <Button onClick={() => setCreateOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Create List
          </Button>
        }
      />

      {lists.length === 0 ? (
        <EmptyState
          icon={List}
          title="No lists yet"
          description="Create a list to group companies or contacts for campaigns and exports."
          action={{ label: 'Create List', onClick: () => setCreateOpen(true) }}
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {lists.map(list => (
            <Card key={list.id} className="group relative h-full transition-colors hover:border-primary/40">
              <CardContent className="p-5">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10">
                    <List className="h-5 w-5 text-primary" />
                  </div>
                  <div className="flex items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100">
                    <button
                      onClick={() => handleExport(list.name)}
                      className="rounded-lg p-1.5 text-muted-foreground hover:bg-accent hover:text-foreground transition-colors"
                      title="Export list"
                    >
                      <Download className="h-3.5 w-3.5" />
                    </button>
                    <button
                      onClick={() => handleDelete(list.id, list.name)}
                      className="rounded-lg p-1.5 text-muted-foreground hover:bg-destructive/10 hover:text-destructive transition-colors"
                      title="Delete list"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                </div>

                <p className="mt-3 font-semibold text-foreground leading-snug">{list.name}</p>
                {list.description && (
                  <p className="mt-1 text-xs text-muted-foreground line-clamp-2">{list.description}</p>
                )}

                <div className="mt-3 flex items-center justify-between">
                  <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                    {list.type === 'contact' ? <Users className="h-3 w-3" /> : <Building2 className="h-3 w-3" />}
                    <span className="font-medium text-foreground">{list.entities}</span> records
                  </div>
                  <Badge variant="secondary" className="text-[10px]">{list.type}</Badge>
                </div>

                <div className="mt-3 flex items-center justify-between border-t border-border pt-3">
                  <span className="text-xs text-muted-foreground">Updated {list.updatedAt}</span>
                  <span className="text-xs text-muted-foreground">by {list.createdBy}</span>
                </div>
              </CardContent>
            </Card>
          ))}

          <button
            onClick={() => setCreateOpen(true)}
            className="flex h-full min-h-[160px] flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed border-border text-muted-foreground transition-colors hover:border-primary/40 hover:text-primary"
          >
            <Plus className="h-6 w-6" />
            <span className="text-sm font-medium">New List</span>
          </button>
        </div>
      )}

      <CreateListModal
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onCreate={(list) => {
          setLists(prev => [list, ...prev])
          toast.success(`"${list.name}" created`)
        }}
      />
    </div>
  )
}
