'use client'

import { useEffect } from 'react'
import { CheckCircle2, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'

const DEFAULT_STEPS = [
  { key: 'connector_execution', label: 'Querying data connectors' },
  { key: 'normalization', label: 'Normalizing results' },
  { key: 'entity_resolution', label: 'Resolving duplicates' },
  { key: 'enrichment', label: 'Enriching records' },
  { key: 'confidence', label: 'Calculating confidence scores' },
]

interface SearchProgressProps {
  active: boolean
  stages?: Record<string, string>
  progressPct?: number
  onComplete?: () => void
}

function stageStatus(stages: Record<string, string> | undefined, key: string, active: boolean): 'done' | 'current' | 'pending' {
  const status = stages?.[key]
  if (status === 'completed' || status === 'skipped') return 'done'
  if (status === 'in_progress') return 'current'
  if (active && !stages) return key === 'connector_execution' ? 'current' : 'pending'
  return 'pending'
}

export function SearchProgress({ active, stages, progressPct, onComplete }: SearchProgressProps) {
  useEffect(() => {
    if (!active && progressPct === 100) onComplete?.()
  }, [active, progressPct, onComplete])

  if (!active && !stages) return null

  return (
    <div className="rounded-xl border border-border bg-card p-4">
      {progressPct != null && progressPct > 0 && (
        <div className="mb-3">
          <div className="flex justify-between text-xs text-muted-foreground mb-1">
            <span>Discovery pipeline</span>
            <span>{progressPct}%</span>
          </div>
          <div className="h-1.5 rounded-full bg-muted overflow-hidden">
            <div
              className="h-full bg-primary transition-all duration-500"
              style={{ width: `${progressPct}%` }}
            />
          </div>
        </div>
      )}
      <ul className="space-y-2">
        {DEFAULT_STEPS.map(({ key, label }) => {
          const state = stageStatus(stages, key, active)
          return (
            <li key={key} className="flex items-center gap-2 text-sm">
              {state === 'done' ? (
                <CheckCircle2 className="h-4 w-4 text-success" />
              ) : state === 'current' ? (
                <Loader2 className="h-4 w-4 animate-spin text-primary" />
              ) : (
                <span className="h-4 w-4 rounded-full border border-border" />
              )}
              <span className={cn(state !== 'pending' ? 'text-foreground' : 'text-muted-foreground')}>
                {label}
              </span>
            </li>
          )
        })}
      </ul>
    </div>
  )
}