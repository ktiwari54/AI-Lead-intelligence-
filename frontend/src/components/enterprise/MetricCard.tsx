'use client'

import { LucideIcon, TrendingUp, TrendingDown } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/lib/utils'

interface MetricCardProps {
  title: string
  value: string | number
  subtitle?: string
  icon?: LucideIcon
  trend?: { value: number; label: string }
  loading?: boolean
  className?: string
  /** Render without outer Card border — for use inside dashboard widgets */
  embedded?: boolean
}

export function MetricCard({ title, value, subtitle, icon: Icon, trend, loading, className, embedded }: MetricCardProps) {
  const trendUp = trend && trend.value >= 0

  const body = loading ? (
    <>
      <div className="flex items-center justify-between pb-2">
        <Skeleton className="h-4 w-24" />
        <Skeleton className="h-8 w-8 rounded-lg" />
      </div>
      <Skeleton className="h-8 w-20" />
      <Skeleton className="mt-2 h-3 w-32" />
    </>
  ) : (
    <>
      <div className="flex items-center justify-between pb-2">
        <p className="text-sm font-medium text-muted-foreground">{title}</p>
        {Icon && (
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10">
            <Icon className="h-4 w-4 text-primary" />
          </div>
        )}
      </div>
      <div className="text-2xl font-bold tracking-tight text-foreground">{value}</div>
      {(subtitle || trend) && (
        <div className="mt-1 flex items-center gap-2 text-xs text-muted-foreground">
          {trend && (
            <span className={cn('inline-flex items-center gap-0.5 font-medium', trendUp ? 'text-success' : 'text-destructive')}>
              {trendUp ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
              {Math.abs(trend.value)}%
            </span>
          )}
          <span>{trend?.label ?? subtitle}</span>
        </div>
      )}
    </>
  )

  if (embedded) {
    return (
      <div className={cn('rounded-lg border border-border/60 bg-background/60 p-4', className)}>
        {body}
      </div>
    )
  }

  if (loading) {
    return (
      <Card className={className}>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-8 w-8 rounded-lg" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-8 w-20" />
          <Skeleton className="mt-2 h-3 w-32" />
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className={cn('transition-shadow hover:shadow-md', className)}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
        {Icon && (
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10">
            <Icon className="h-4 w-4 text-primary" />
          </div>
        )}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold tracking-tight text-foreground">{value}</div>
        {(subtitle || trend) && (
          <div className="mt-1 flex items-center gap-2 text-xs text-muted-foreground">
            {trend && (
              <span className={cn('inline-flex items-center gap-0.5 font-medium', trendUp ? 'text-success' : 'text-destructive')}>
                {trendUp ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                {Math.abs(trend.value)}%
              </span>
            )}
            <span>{trend?.label ?? subtitle}</span>
          </div>
        )}
      </CardContent>
    </Card>
  )
}