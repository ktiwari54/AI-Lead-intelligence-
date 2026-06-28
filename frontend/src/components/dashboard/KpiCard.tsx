'use client'

import { LucideIcon, TrendingUp, TrendingDown } from 'lucide-react'
import { cn } from '@/lib/utils'

interface KpiCardProps {
  title: string
  value: string | number
  icon: LucideIcon
  change?: number
  changeLabel?: string
  loading?: boolean
}

export function KpiCard({ title, value, icon: Icon, change, changeLabel, loading }: KpiCardProps) {
  if (loading) {
    return <div className="h-full animate-pulse rounded-xl bg-muted" />
  }

  return (
    <div className="flex h-full items-center justify-between rounded-xl border border-border bg-card p-4">
      <div>
        <p className="text-xs font-medium text-muted-foreground">{title}</p>
        <p className="mt-1 text-2xl font-bold text-foreground">{value}</p>
        {change != null && (
          <p className={cn(
            'mt-1 flex items-center gap-1 text-xs',
            change >= 0 ? 'text-success' : 'text-destructive'
          )}>
            {change >= 0 ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
            {change >= 0 ? '+' : ''}{change}% {changeLabel}
          </p>
        )}
      </div>
      <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
        <Icon className="h-5 w-5 text-primary" />
      </div>
    </div>
  )
}