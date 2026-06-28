import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { SavedView } from '@/types/table'

interface TableStore {
  savedViews: Record<string, SavedView[]>
  getViews: (entityType: string) => SavedView[]
  addView: (view: SavedView) => void
  removeView: (entityType: string, viewId: string) => void
  setDefaultView: (entityType: string, viewId: string) => void
}

export const useTableStore = create<TableStore>()(
  persist(
    (set, get) => ({
      savedViews: {},
      getViews: (entityType) => get().savedViews[entityType] ?? [],
      addView: (view) =>
        set((s) => ({
          savedViews: {
            ...s.savedViews,
            [view.entityType]: [...(s.savedViews[view.entityType] ?? []), view],
          },
        })),
      removeView: (entityType, viewId) =>
        set((s) => ({
          savedViews: {
            ...s.savedViews,
            [entityType]: (s.savedViews[entityType] ?? []).filter((v) => v.id !== viewId),
          },
        })),
      setDefaultView: (entityType, viewId) =>
        set((s) => ({
          savedViews: {
            ...s.savedViews,
            [entityType]: (s.savedViews[entityType] ?? []).map((v) => ({
              ...v,
              isDefault: v.id === viewId,
            })),
          },
        })),
    }),
    { name: 'ali-table-views' }
  )
)