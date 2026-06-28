'use client'

import { Search } from 'lucide-react'
import { Table } from '@tanstack/react-table'
import { ColumnVisibilityMenu } from './ColumnVisibilityMenu'
import { SavedViewsMenu } from './SavedViewsMenu'
import type { ColumnConfig } from '@/types/table'

interface DataTableToolbarProps<T> {
  table: Table<T>
  entityType: string
  searchValue: string
  onSearchChange: (value: string) => void
  searchPlaceholder?: string
  currentColumns: ColumnConfig[]
  onApplyView: (columns: ColumnConfig[]) => void
  children?: React.ReactNode
}

export function DataTableToolbar<T>({
  table,
  entityType,
  searchValue,
  onSearchChange,
  searchPlaceholder = 'Search...',
  currentColumns,
  onApplyView,
  children,
}: DataTableToolbarProps<T>) {
  return (
    <div className="flex flex-col gap-3 border-b border-border p-4 sm:flex-row sm:items-center">
      <div className="relative flex-1 max-w-sm">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <input
          type="search"
          value={searchValue}
          onChange={(e) => onSearchChange(e.target.value)}
          placeholder={searchPlaceholder}
          className="input-base pl-9"
        />
      </div>
      <div className="flex items-center gap-2">
        {children}
        <ColumnVisibilityMenu table={table} />
        <SavedViewsMenu
          entityType={entityType}
          currentColumns={currentColumns}
          onApplyView={onApplyView}
        />
      </div>
    </div>
  )
}