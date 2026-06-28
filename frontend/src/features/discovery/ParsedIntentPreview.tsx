'use client'

import { ParsedIntent } from '@/lib/parse-search-intent'
import { Filter, Sparkles } from 'lucide-react'

interface ParsedIntentPreviewProps {
  intent: ParsedIntent | null
  onSearch: () => void
  onEditFilters?: () => void
  loading?: boolean
}

function Chip({ label }: { label: string }) {
  return (
    <span className="rounded-md bg-muted px-2 py-0.5 text-xs text-foreground">{label}</span>
  )
}

export function ParsedIntentPreview({
  intent,
  onSearch,
  onEditFilters,
  loading,
}: ParsedIntentPreviewProps) {
  if (!intent) return null

  const parts: string[] = [
    `Intent: ${intent.intent.replace(/_/g, ' ')}`,
    ...(intent.countries.length ? [`Location: ${intent.countries.join(', ')}`] : []),
    ...(intent.industries.length ? [`Industry: ${intent.industries.join(', ')}`] : []),
    ...(intent.technologies.length ? [`Tech: ${intent.technologies.join(', ')}`] : []),
    ...(intent.seniority_levels.length ? [`Seniority: ${intent.seniority_levels.join(', ')}`] : []),
    ...(intent.email_verified ? ['Filter: email_verified=true'] : []),
    ...(intent.connectors.length ? [`Connectors: ${intent.connectors.join(', ')}`] : []),
  ]

  return (
    <div className="rounded-xl border border-primary/20 bg-primary/5 p-4">
      <div className="flex items-start gap-3">
        <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary/10">
          <Sparkles className="h-4 w-4 text-primary" />
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-semibold text-foreground">AI Interpretation</h3>
          <p className="mt-1 text-sm text-muted-foreground">{parts.join(' · ')}</p>
          <div className="mt-2 flex flex-wrap gap-1.5">
            {intent.industries.map((i) => <Chip key={i} label={i} />)}
            {intent.countries.map((c) => <Chip key={c} label={c} />)}
            {intent.technologies.map((t) => <Chip key={t} label={t} />)}
          </div>
        </div>
        <div className="flex shrink-0 gap-2">
          {onEditFilters && (
            <button
              type="button"
              onClick={onEditFilters}
              className="flex items-center gap-1 rounded-lg border border-border px-3 py-1.5 text-xs font-medium hover:bg-accent"
            >
              <Filter className="h-3.5 w-3.5" />
              Edit Filters
            </button>
          )}
          <button
            type="button"
            onClick={onSearch}
            disabled={loading}
            className="rounded-lg bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
          >
            Search →
          </button>
        </div>
      </div>
    </div>
  )
}