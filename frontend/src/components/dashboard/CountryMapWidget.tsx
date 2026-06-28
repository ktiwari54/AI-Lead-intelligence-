'use client'

import { useMemo } from 'react'

interface CountryData {
  code: string
  name: string
  count: number
}

const MOCK_DATA: CountryData[] = [
  { code: 'US', name: 'United States', count: 1842 },
  { code: 'GB', name: 'United Kingdom', count: 634 },
  { code: 'DE', name: 'Germany', count: 521 },
  { code: 'CA', name: 'Canada', count: 418 },
  { code: 'AU', name: 'Australia', count: 312 },
  { code: 'FR', name: 'France', count: 289 },
  { code: 'IN', name: 'India', count: 245 },
  { code: 'NL', name: 'Netherlands', count: 198 },
  { code: 'SG', name: 'Singapore', count: 156 },
  { code: 'SE', name: 'Sweden', count: 134 },
]

export function CountryMapWidget() {
  const maxCount = useMemo(() => Math.max(...MOCK_DATA.map(d => d.count)), [])
  const total = useMemo(() => MOCK_DATA.reduce((s, d) => s + d.count, 0), [])

  return (
    <div className="flex h-full flex-col gap-3">
      <p className="text-xs text-muted-foreground shrink-0">
        {total.toLocaleString()} companies across {MOCK_DATA.length} countries
      </p>

      <div className="flex-1 min-h-0 overflow-auto space-y-1.5">
        {MOCK_DATA.map((d) => {
          const pct = (d.count / maxCount) * 100
          const displayPct = ((d.count / total) * 100).toFixed(1)
          return (
            <div key={d.code} className="group flex items-center gap-3">
              <span className="w-6 shrink-0 text-xs font-medium text-muted-foreground">{d.code}</span>
              <div className="relative flex-1 h-5 rounded-full bg-muted overflow-hidden">
                <div
                  className="absolute inset-y-0 left-0 rounded-full bg-primary/70 transition-all group-hover:bg-primary"
                  style={{ width: `${pct}%` }}
                />
                <span className="absolute inset-0 flex items-center px-2 text-[10px] font-medium text-foreground">
                  {d.name}
                </span>
              </div>
              <div className="w-14 shrink-0 text-right">
                <span className="text-xs font-semibold text-foreground">{d.count.toLocaleString()}</span>
                <span className="ml-1 text-[10px] text-muted-foreground">{displayPct}%</span>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
