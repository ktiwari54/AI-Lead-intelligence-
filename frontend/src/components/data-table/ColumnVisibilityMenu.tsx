'use client'

import { useState } from 'react'
import { Columns3, Check } from 'lucide-react'
import { Table } from '@tanstack/react-table'
import { cn } from '@/lib/utils'

interface ColumnVisibilityMenuProps<T> {
  table: Table<T>
}

export function ColumnVisibilityMenu<T>({ table }: ColumnVisibilityMenuProps<T>) {
  const [open, setOpen] = useState(false)

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground hover:bg-accent transition-colors"
      >
        <Columns3 className="h-4 w-4" />
        Columns
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-dropdown" onClick={() => setOpen(false)} />
          <div className="absolute right-0 top-full z-dropdown mt-1 w-48 rounded-lg border border-border bg-popover py-1 shadow-md">
            {table
              .getAllColumns()
              .filter((col) => col.getCanHide())
              .map((column) => (
                <button
                  key={column.id}
                  onClick={() => column.toggleVisibility(!column.getIsVisible())}
                  className="flex w-full items-center gap-2 px-3 py-2 text-sm text-foreground hover:bg-accent"
                >
                  <span
                    className={cn(
                      'flex h-4 w-4 items-center justify-center rounded border border-border',
                      column.getIsVisible() && 'bg-primary border-primary'
                    )}
                  >
                    {column.getIsVisible() && <Check className="h-3 w-3 text-primary-foreground" />}
                  </span>
                  {typeof column.columnDef.header === 'string'
                    ? column.columnDef.header
                    : column.id}
                </button>
              ))}
          </div>
        </>
      )}
    </div>
  )
}