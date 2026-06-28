'use client'

import { Activity, Wifi, Zap } from 'lucide-react'
import { Badge } from '@/components/ui/Badge'
import { cn } from '@/lib/utils'

interface StatusBarProps {
  className?: string
}

export function StatusBar({ className }: StatusBarProps) {
  return (
    <footer
      className={cn(
        'flex h-8 items-center justify-between border-t border-border bg-muted/40 px-4 text-[11px] text-muted-foreground lg:px-6',
        className
      )}
    >
      <div className="flex items-center gap-4">
        <span className="inline-flex items-center gap-1.5">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-success opacity-75" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-success" />
          </span>
          All systems operational
        </span>
        <span className="hidden items-center gap-1 sm:inline-flex">
          <Wifi className="h-3 w-3" />
          API connected
        </span>
      </div>
      <div className="flex items-center gap-3">
        <Badge variant="outline" className="h-5 px-1.5 text-[10px] font-normal">
          <Zap className="mr-1 h-2.5 w-2.5" />
          Mock discovery
        </Badge>
        <span className="hidden items-center gap-1 md:inline-flex">
          <Activity className="h-3 w-3" />
          v3.0 Enterprise
        </span>
      </div>
    </footer>
  )
}