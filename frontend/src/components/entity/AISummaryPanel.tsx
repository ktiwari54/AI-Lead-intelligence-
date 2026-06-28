'use client'

import { Sparkles, Lightbulb, RefreshCw } from 'lucide-react'
import { ScoreGauge } from '@/components/ui/ScoreGauge'
import Badge from '@/components/ui/Badge'
import { cn } from '@/lib/utils'

interface Recommendation {
  action: string
  reason: string
}

interface AISummaryPanelProps {
  score?: number
  recommendation?: 'pursue' | 'nurture' | 'deprioritize'
  summary?: string
  recommendations?: Recommendation[]
  crmStatus?: string
  tags?: string[]
  onScore?: () => void
  onEnrich?: () => void
  loading?: boolean
}

const recVariant: Record<string, 'success' | 'warning' | 'danger'> = {
  pursue: 'success',
  nurture: 'warning',
  deprioritize: 'danger',
}

export function AISummaryPanel({
  score,
  recommendation = 'nurture',
  summary,
  recommendations = [],
  crmStatus,
  tags = [],
  onScore,
  onEnrich,
  loading,
}: AISummaryPanelProps) {
  return (
    <div className="space-y-4">
      {score != null && (
        <div className="rounded-xl border border-border bg-card p-4">
          <div className="flex items-center justify-between">
            <ScoreGauge score={score} label="Lead Score" size={80} />
            <Badge variant={recVariant[recommendation] ?? 'warning'}>
              {recommendation.charAt(0).toUpperCase() + recommendation.slice(1)}
            </Badge>
          </div>
          <div className="mt-3 flex gap-2">
            {onScore && (
              <button
                onClick={onScore}
                disabled={loading}
                className="flex-1 rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
              >
                Re-score
              </button>
            )}
            {onEnrich && (
              <button
                onClick={onEnrich}
                disabled={loading}
                className="flex-1 rounded-md border border-border px-3 py-1.5 text-xs font-medium hover:bg-accent disabled:opacity-50"
              >
                Enrich
              </button>
            )}
          </div>
        </div>
      )}

      <div className="rounded-xl border border-border bg-card p-4">
        <div className="flex items-center gap-2 mb-3">
          <Sparkles className="h-4 w-4 text-primary" />
          <h3 className="text-sm font-semibold text-foreground">AI Summary</h3>
        </div>
        <p className="text-sm text-muted-foreground leading-relaxed">
          {summary ?? 'Run AI scoring to generate an intelligent summary of this record.'}
        </p>
      </div>

      {recommendations.length > 0 && (
        <div className="rounded-xl border border-border bg-card p-4">
          <div className="flex items-center gap-2 mb-3">
            <Lightbulb className="h-4 w-4 text-warning" />
            <h3 className="text-sm font-semibold text-foreground">Recommendations</h3>
          </div>
          <ul className="space-y-2">
            {recommendations.map((rec, i) => (
              <li key={i} className="text-sm">
                <span className="font-medium text-foreground">{rec.action}</span>
                <span className="text-muted-foreground"> — {rec.reason}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {crmStatus && (
        <div className="rounded-xl border border-border bg-card p-4">
          <div className="flex items-center gap-2 mb-2">
            <RefreshCw className="h-4 w-4 text-muted-foreground" />
            <h3 className="text-sm font-semibold text-foreground">CRM Sync</h3>
          </div>
          <p className="text-sm text-success">{crmStatus}</p>
        </div>
      )}

      {tags.length > 0 && (
        <div className="rounded-xl border border-border bg-card p-4">
          <h3 className="text-sm font-semibold text-foreground mb-2">Tags</h3>
          <div className="flex flex-wrap gap-1.5">
            {tags.map((tag) => (
              <Badge key={tag} variant="gray">{tag}</Badge>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}