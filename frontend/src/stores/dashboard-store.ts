import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface DashboardLayoutItem {
  i: string
  x: number
  y: number
  w: number
  h: number
  minW?: number
  minH?: number
}

export const DEFAULT_LAYOUT: DashboardLayoutItem[] = [
  { i: 'kpis', x: 0, y: 0, w: 12, h: 2, minW: 6, minH: 2 },
  { i: 'velocity', x: 0, y: 2, w: 8, h: 4, minW: 4, minH: 3 },
  { i: 'quick-actions', x: 8, y: 2, w: 4, h: 4, minW: 3, minH: 3 },
  { i: 'activity', x: 0, y: 6, w: 7, h: 4, minW: 4, minH: 3 },
  { i: 'pipeline', x: 7, y: 6, w: 5, h: 4, minW: 3, minH: 3 },
]

interface DashboardState {
  layout: DashboardLayoutItem[]
  setLayout: (layout: DashboardLayoutItem[]) => void
  resetLayout: () => void
}

export const useDashboardStore = create<DashboardState>()(
  persist(
    (set) => ({
      layout: DEFAULT_LAYOUT,
      setLayout: (layout) => set({ layout }),
      resetLayout: () => set({ layout: DEFAULT_LAYOUT }),
    }),
    { name: 'dashboard-layout' }
  )
)