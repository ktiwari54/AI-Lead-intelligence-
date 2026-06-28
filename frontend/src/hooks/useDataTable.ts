'use client'

import { useState, useCallback } from 'react'
import {
  SortingState,
  RowSelectionState,
  VisibilityState,
  ColumnSizingState,
  ColumnOrderState,
} from '@tanstack/react-table'
import type { ColumnConfig } from '@/types/table'

export function useDataTable(defaultColumnOrder: string[]) {
  const [sorting, setSorting] = useState<SortingState>([])
  const [rowSelection, setRowSelection] = useState<RowSelectionState>({})
  const [columnVisibility, setColumnVisibility] = useState<VisibilityState>({})
  const [columnSizing, setColumnSizing] = useState<ColumnSizingState>({})
  const [columnOrder, setColumnOrder] = useState<ColumnOrderState>(defaultColumnOrder)

  const getCurrentColumnConfig = useCallback((): ColumnConfig[] => {
    return columnOrder.map((id, index) => ({
      id,
      visible: columnVisibility[id] !== false,
      width: columnSizing[id] ?? 150,
      pinned: null,
      order: index,
    }))
  }, [columnOrder, columnVisibility, columnSizing])

  const applyColumnConfig = useCallback((configs: ColumnConfig[]) => {
    const order = configs.sort((a, b) => a.order - b.order).map((c) => c.id)
    const visibility: VisibilityState = {}
    const sizing: ColumnSizingState = {}
    configs.forEach((c) => {
      visibility[c.id] = c.visible
      sizing[c.id] = c.width
    })
    setColumnOrder(order)
    setColumnVisibility(visibility)
    setColumnSizing(sizing)
  }, [])

  const selectedCount = Object.keys(rowSelection).length

  return {
    sorting,
    setSorting,
    rowSelection,
    setRowSelection,
    columnVisibility,
    setColumnVisibility,
    columnSizing,
    setColumnSizing,
    columnOrder,
    setColumnOrder,
    getCurrentColumnConfig,
    applyColumnConfig,
    selectedCount,
    clearSelection: () => setRowSelection({}),
  }
}