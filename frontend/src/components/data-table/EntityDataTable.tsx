'use client'

import { useRef } from 'react'
import {
  ColumnDef,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
} from '@tanstack/react-table'
import { useVirtualizer } from '@tanstack/react-virtual'
import { ArrowUpDown, ArrowUp, ArrowDown } from 'lucide-react'
import { DataTableToolbar } from './DataTableToolbar'
import { useDataTable } from '@/hooks/useDataTable'
import { cn } from '@/lib/utils'

type TableState = ReturnType<typeof useDataTable>

interface EntityDataTableProps<T> {
  data: T[]
  columns: ColumnDef<T, unknown>[]
  loading?: boolean
  entityType: string
  searchValue: string
  onSearchChange: (value: string) => void
  searchPlaceholder?: string
  tableState: TableState
  onRowClick?: (row: T) => void
  getRowId: (row: T) => string
  emptyState?: React.ReactNode
  toolbarExtra?: React.ReactNode
  estimateRowHeight?: number
}

export function EntityDataTable<T>({
  data,
  columns,
  loading = false,
  entityType,
  searchValue,
  onSearchChange,
  searchPlaceholder,
  tableState,
  onRowClick,
  getRowId,
  emptyState,
  toolbarExtra,
  estimateRowHeight = 48,
}: EntityDataTableProps<T>) {
  const parentRef = useRef<HTMLDivElement>(null)

  const table = useReactTable({
    data,
    columns,
    state: {
      sorting: tableState.sorting,
      rowSelection: tableState.rowSelection,
      columnVisibility: tableState.columnVisibility,
      columnSizing: tableState.columnSizing,
      columnOrder: tableState.columnOrder,
    },
    onSortingChange: (updater) => {
      const next = typeof updater === 'function' ? updater(tableState.sorting) : updater
      tableState.setSorting(next)
    },
    onRowSelectionChange: (updater) => {
      const next = typeof updater === 'function' ? updater(tableState.rowSelection) : updater
      tableState.setRowSelection(next)
    },
    onColumnVisibilityChange: (updater) => {
      const next = typeof updater === 'function' ? updater(tableState.columnVisibility) : updater
      tableState.setColumnVisibility(next)
    },
    onColumnSizingChange: (updater) => {
      const next = typeof updater === 'function' ? updater(tableState.columnSizing) : updater
      tableState.setColumnSizing(next)
    },
    onColumnOrderChange: (updater) => {
      const next = typeof updater === 'function' ? updater(tableState.columnOrder) : updater
      tableState.setColumnOrder(next)
    },
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getRowId: (row) => getRowId(row),
    enableRowSelection: true,
    enableColumnResizing: true,
    columnResizeMode: 'onChange',
  })

  const { rows } = table.getRowModel()

  const virtualizer = useVirtualizer({
    count: rows.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => estimateRowHeight,
    overscan: 10,
  })

  const virtualRows = virtualizer.getVirtualItems()
  const totalSize = virtualizer.getTotalSize()
  const paddingTop = virtualRows.length > 0 ? virtualRows[0]?.start ?? 0 : 0
  const paddingBottom =
    virtualRows.length > 0
      ? totalSize - (virtualRows[virtualRows.length - 1]?.end ?? 0)
      : 0

  return (
    <div className="overflow-hidden rounded-xl border border-border bg-card">
      <DataTableToolbar
        table={table}
        entityType={entityType}
        searchValue={searchValue}
        onSearchChange={onSearchChange}
        searchPlaceholder={searchPlaceholder}
        currentColumns={tableState.getCurrentColumnConfig()}
        onApplyView={tableState.applyColumnConfig}
      >
        {toolbarExtra}
      </DataTableToolbar>

      <div ref={parentRef} className="max-h-[calc(100vh-320px)] overflow-auto">
        <table className="w-full border-collapse" style={{ width: table.getTotalSize() }}>
          <thead className="sticky top-0 z-sticky bg-muted/80 backdrop-blur">
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <th
                    key={header.id}
                    className="relative border-b border-border px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground"
                    style={{ width: header.getSize() }}
                  >
                    {header.isPlaceholder ? null : (
                      <div
                        className={cn(
                          'flex items-center gap-1',
                          header.column.getCanSort() && 'cursor-pointer select-none hover:text-foreground'
                        )}
                        onClick={header.column.getToggleSortingHandler()}
                      >
                        {flexRender(header.column.columnDef.header, header.getContext())}
                        {header.column.getCanSort() && (
                          <span className="text-muted-foreground">
                            {header.column.getIsSorted() === 'asc' ? (
                              <ArrowUp className="h-3.5 w-3.5" />
                            ) : header.column.getIsSorted() === 'desc' ? (
                              <ArrowDown className="h-3.5 w-3.5" />
                            ) : (
                              <ArrowUpDown className="h-3.5 w-3.5 opacity-40" />
                            )}
                          </span>
                        )}
                      </div>
                    )}
                    {header.column.getCanResize() && (
                      <div
                        onMouseDown={header.getResizeHandler()}
                        onTouchStart={header.getResizeHandler()}
                        className={cn(
                          'absolute right-0 top-0 h-full w-1 cursor-col-resize select-none touch-none bg-border opacity-0 hover:opacity-100',
                          header.column.getIsResizing() && 'opacity-100 bg-primary'
                        )}
                      />
                    )}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {loading ? (
              Array.from({ length: 8 }).map((_, i) => (
                <tr key={i}>
                  {columns.map((_, j) => (
                    <td key={j} className="px-4 py-3">
                      <div className="h-4 animate-pulse rounded bg-muted" />
                    </td>
                  ))}
                </tr>
              ))
            ) : rows.length === 0 ? (
              <tr>
                <td colSpan={columns.length} className="px-4 py-16 text-center">
                  {emptyState ?? (
                    <p className="text-sm text-muted-foreground">No results found</p>
                  )}
                </td>
              </tr>
            ) : (
              <>
                {paddingTop > 0 && (
                  <tr>
                    <td style={{ height: paddingTop }} colSpan={columns.length} />
                  </tr>
                )}
                {virtualRows.map((virtualRow) => {
                  const row = rows[virtualRow.index]
                  return (
                    <tr
                      key={row.id}
                      onClick={() => onRowClick?.(row.original)}
                      className={cn(
                        'border-b border-border transition-colors hover:bg-muted/50',
                        row.getIsSelected() && 'bg-primary/5 border-l-2 border-l-primary',
                        onRowClick && 'cursor-pointer'
                      )}
                    >
                      {row.getVisibleCells().map((cell) => (
                        <td
                          key={cell.id}
                          className="px-4 py-2 text-sm text-foreground"
                          style={{ width: cell.column.getSize() }}
                        >
                          {flexRender(cell.column.columnDef.cell, cell.getContext())}
                        </td>
                      ))}
                    </tr>
                  )
                })}
                {paddingBottom > 0 && (
                  <tr>
                    <td style={{ height: paddingBottom }} colSpan={columns.length} />
                  </tr>
                )}
              </>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}