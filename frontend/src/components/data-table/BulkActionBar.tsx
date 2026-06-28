'use client'

import { X } from 'lucide-react'
import { cn } from '@/lib/utils'

interface BulkAction {
  label: string
  onClick: () => void
  variant?: 'default' | 'danger'
}

interface BulkActionBarProps {
  selectedCount: number
  onClear: () => void
  actions: BulkAction[]
  className?: string
}

export function BulkActionBar({
  selectedCount,
  onClear,
  actions,
  className,
}: BulkActionBarProps) {
  if (selectedCount === 0) return null

  return (
    <div
      className={cn(
        'fixed bottom-6 left-1/2 z-overlay flex -translate-x-1/2 items-center gap-3 rounded-xl border border-border bg-card px-4 py-3 shadow-lg',
        className
      )}
    >
      <span className="text-sm font-medium text-foreground">
        {selectedCount} selected
      </span>
      <div className="h-4 w-px bg-border" />
      {actions.map((action) => (
        <button
          key={action.label}
          onClick={action.onClick}
          className={cn(
            'rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
            action.variant === 'danger'
              ? 'text-destructive hover:bg-destructive/10'
              : 'text-foreground hover:bg-accent'
          )}
        >
          {action.label}
        </button>
      ))}
      <button
        onClick={onClear}
        className="ml-1 rounded-md p-1.5 text-muted-foreground hover:bg-accent hover:text-foreground"
        aria-label="Clear selection"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  )
}