'use client'

import { Building2, User, Globe, MapPin } from 'lucide-react'
import { cn } from '@/lib/utils'

interface EntityHeaderProps {
  type: 'company' | 'contact'
  title: string
  subtitle?: string
  meta?: { icon: React.ElementType; label: string }[]
  actions?: React.ReactNode
  score?: number
  className?: string
}

export function EntityHeader({
  type,
  title,
  subtitle,
  meta = [],
  actions,
  score,
  className,
}: EntityHeaderProps) {
  const Icon = type === 'company' ? Building2 : User

  return (
    <div className={cn('rounded-xl border border-border bg-card p-5', className)}>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-start gap-4">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-primary/10">
            <Icon className="h-6 w-6 text-primary" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-foreground">{title}</h1>
            {subtitle && (
              <p className="mt-0.5 text-sm text-muted-foreground">{subtitle}</p>
            )}
            {meta.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-3">
                {meta.map((m, i) => (
                  <span key={i} className="flex items-center gap-1 text-xs text-muted-foreground">
                    <m.icon className="h-3.5 w-3.5" />
                    {m.label}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>
        <div className="flex items-center gap-3">
          {score != null && (
            <div className="text-right">
              <p className="text-2xl font-bold text-foreground">{Math.round(score)}</p>
              <p className="text-xs text-muted-foreground">Lead Score</p>
            </div>
          )}
          {actions}
        </div>
      </div>
    </div>
  )
}

export { Globe, MapPin }