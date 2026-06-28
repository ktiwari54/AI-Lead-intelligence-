'use client'

import { useState } from 'react'
import { Bookmark, Plus, Trash2 } from 'lucide-react'
import { useTableStore } from '@/stores/table-store'
import type { ColumnConfig } from '@/types/table'
import { cn } from '@/lib/utils'

interface SavedViewsMenuProps {
  entityType: string
  currentColumns: ColumnConfig[]
  onApplyView: (columns: ColumnConfig[]) => void
}

export function SavedViewsMenu({
  entityType,
  currentColumns,
  onApplyView,
}: SavedViewsMenuProps) {
  const [open, setOpen] = useState(false)
  const [saveName, setSaveName] = useState('')
  const views = useTableStore((s) => s.getViews(entityType))
  const addView = useTableStore((s) => s.addView)
  const removeView = useTableStore((s) => s.removeView)

  const handleSave = () => {
    if (!saveName.trim()) return
    addView({
      id: crypto.randomUUID(),
      name: saveName.trim(),
      entityType,
      columns: currentColumns,
      createdAt: new Date().toISOString(),
    })
    setSaveName('')
    setOpen(false)
  }

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground hover:bg-accent transition-colors"
      >
        <Bookmark className="h-4 w-4" />
        Views
        {views.length > 0 && (
          <span className="rounded-full bg-muted px-1.5 text-xs text-muted-foreground">
            {views.length}
          </span>
        )}
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-dropdown" onClick={() => setOpen(false)} />
          <div className="absolute right-0 top-full z-dropdown mt-1 w-56 rounded-lg border border-border bg-popover py-1 shadow-md">
            {views.length === 0 ? (
              <p className="px-3 py-2 text-xs text-muted-foreground">No saved views yet</p>
            ) : (
              views.map((view) => (
                <div
                  key={view.id}
                  className="flex items-center justify-between px-3 py-2 hover:bg-accent group"
                >
                  <button
                    onClick={() => {
                      onApplyView(view.columns)
                      setOpen(false)
                    }}
                    className="flex-1 text-left text-sm text-foreground"
                  >
                    {view.name}
                  </button>
                  <button
                    onClick={() => removeView(entityType, view.id)}
                    className="opacity-0 group-hover:opacity-100 p-1 text-muted-foreground hover:text-destructive"
                    aria-label={`Delete view ${view.name}`}
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              ))
            )}
            <div className="border-t border-border mt-1 px-3 py-2 space-y-2">
              <input
                type="text"
                value={saveName}
                onChange={(e) => setSaveName(e.target.value)}
                placeholder="View name..."
                className="input-base text-sm"
                onKeyDown={(e) => e.key === 'Enter' && handleSave()}
              />
              <button
                onClick={handleSave}
                disabled={!saveName.trim()}
                className={cn(
                  'flex w-full items-center justify-center gap-1.5 rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground',
                  'hover:bg-primary/90 disabled:opacity-50'
                )}
              >
                <Plus className="h-3.5 w-3.5" />
                Save current view
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}