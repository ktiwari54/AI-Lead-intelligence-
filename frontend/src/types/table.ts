export interface ColumnConfig {
  id: string
  visible: boolean
  width: number
  pinned: 'left' | 'right' | null
  order: number
}

export interface SavedView {
  id: string
  name: string
  entityType: string
  columns: ColumnConfig[]
  isDefault?: boolean
  createdAt: string
}

export interface TableViewState {
  columnVisibility: Record<string, boolean>
  columnOrder: string[]
  columnSizing: Record<string, number>
  sorting: { id: string; desc: boolean }[]
}