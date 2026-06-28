'use client'

import dynamic from 'next/dynamic'
import { useCallback, useEffect, useRef, useState } from 'react'
import { GripVertical } from 'lucide-react'
import type { Layout } from 'react-grid-layout/legacy'
import { useDashboardStore, DEFAULT_LAYOUT } from '@/stores/dashboard-store'
import 'react-grid-layout/css/styles.css'
import 'react-resizable/css/styles.css'

const WIDGET_LABELS: Record<string, string> = {
  kpis: 'Key metrics',
  velocity: 'Lead velocity',
  'quick-actions': 'Quick actions',
  activity: 'Activity feed',
  pipeline: 'CRM pipeline',
}

const ReactGridLayout = dynamic(
  () => import('react-grid-layout/legacy').then((m) => m.default),
  { ssr: false, loading: () => <div className="h-96 animate-pulse rounded-xl bg-muted" /> }
)

interface DashboardGridProps {
  children: Record<string, React.ReactNode>
}

export function DashboardGrid({ children }: DashboardGridProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [width, setWidth] = useState(1200)
  const layout = useDashboardStore((s) => s.layout)
  const setLayout = useDashboardStore((s) => s.setLayout)

  useEffect(() => {
    const el = containerRef.current
    if (!el) return
    const ro = new ResizeObserver(([entry]) => {
      setWidth(entry.contentRect.width)
    })
    ro.observe(el)
    setWidth(el.offsetWidth)
    return () => ro.disconnect()
  }, [])

  const onLayoutChange = useCallback(
    (newLayout: Layout) => {
      setLayout(
        newLayout.map((item) => ({
          i: item.i,
          x: item.x,
          y: item.y,
          w: item.w,
          h: item.h,
          minW: DEFAULT_LAYOUT.find((d) => d.i === item.i)?.minW,
          minH: DEFAULT_LAYOUT.find((d) => d.i === item.i)?.minH,
        }))
      )
    },
    [setLayout]
  )

  return (
    <div ref={containerRef} className="dashboard-grid w-full">
      <ReactGridLayout
        className="layout"
        layout={layout}
        cols={12}
        rowHeight={80}
        width={width}
        onLayoutChange={onLayoutChange}
        draggableHandle=".widget-drag-handle"
        compactType="vertical"
        margin={[16, 16]}
      >
        {layout.map((item) => (
          <div
            key={item.i}
            className="group flex flex-col overflow-hidden rounded-xl border border-border/80 bg-card shadow-sm ring-1 ring-black/[0.02]"
          >
            <div className="widget-drag-handle flex shrink-0 cursor-grab items-center gap-2 border-b border-border/60 bg-muted/30 px-4 py-2 active:cursor-grabbing">
              <GripVertical className="h-3.5 w-3.5 text-muted-foreground/60" />
              <span className="text-xs font-medium text-muted-foreground">
                {WIDGET_LABELS[item.i] ?? item.i}
              </span>
            </div>
            <div className="flex-1 min-h-0 overflow-auto p-4">
              {children[item.i]}
            </div>
          </div>
        ))}
      </ReactGridLayout>
    </div>
  )
}