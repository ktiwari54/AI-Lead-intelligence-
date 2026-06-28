'use client'

import Link from 'next/link'
import { ArrowLeft } from 'lucide-react'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { cn } from '@/lib/utils'

export interface Tab {
  id: string
  label: string
  count?: number
}

interface Entity360LayoutProps {
  backHref: string
  backLabel: string
  header: React.ReactNode
  tabs: Tab[]
  activeTab: string
  onTabChange: (tabId: string) => void
  children: React.ReactNode
  sidePanel?: React.ReactNode
}

export function Entity360Layout({
  backHref,
  backLabel,
  header,
  tabs,
  activeTab,
  onTabChange,
  children,
  sidePanel,
}: Entity360LayoutProps) {
  return (
    <div className="page-container space-y-6">
      <Link
        href={backHref}
        className="inline-flex items-center gap-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" />
        {backLabel}
      </Link>

      {header}

      <div className={cn('grid gap-6', sidePanel ? 'lg:grid-cols-[1fr_320px]' : 'grid-cols-1')}>
        <div className="space-y-4">
          <Tabs value={activeTab} onValueChange={onTabChange}>
            <TabsList className="h-auto w-full justify-start gap-1 overflow-x-auto rounded-none border-b border-border bg-transparent p-0">
              {tabs.map((tab) => (
                <TabsTrigger
                  key={tab.id}
                  value={tab.id}
                  className="shrink-0 rounded-none border-b-2 border-transparent bg-transparent px-4 py-2.5 shadow-none data-[state=active]:border-primary data-[state=active]:bg-transparent data-[state=active]:shadow-none"
                >
                  {tab.label}
                  {tab.count != null && (
                    <span className="ml-1.5 rounded-full bg-muted px-1.5 text-xs">
                      {tab.count}
                    </span>
                  )}
                </TabsTrigger>
              ))}
            </TabsList>
          </Tabs>
          <div>{children}</div>
        </div>

        {sidePanel && (
          <aside className="space-y-4 lg:sticky lg:top-20 lg:self-start">
            {sidePanel}
          </aside>
        )}
      </div>
    </div>
  )
}