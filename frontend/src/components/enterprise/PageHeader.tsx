'use client'

import { ReactNode } from 'react'
import { cn } from '@/lib/utils'
import { Badge } from '@/components/ui/Badge'

interface PageHeaderProps {
  title: string
  description?: string
  badge?: string
  actions?: ReactNode
  breadcrumbs?: ReactNode
  className?: string
}

export function PageHeader({ title, description, badge, actions, breadcrumbs, className }: PageHeaderProps) {
  return (
    <div className={cn('space-y-4', className)}>
      {breadcrumbs}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="space-y-1">
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-2xl font-semibold tracking-tight text-foreground md:text-3xl">{title}</h1>
            {badge && <Badge variant="secondary">{badge}</Badge>}
          </div>
          {description && (
            <p className="max-w-3xl text-sm leading-relaxed text-muted-foreground md:text-base">{description}</p>
          )}
        </div>
        {actions && <div className="flex shrink-0 flex-wrap items-center gap-2">{actions}</div>}
      </div>
    </div>
  )
}