'use client'

import { ColumnDef } from '@tanstack/react-table'
import Link from 'next/link'
import { MoreHorizontal, Trash2, ExternalLink } from 'lucide-react'
import { Company } from '@/types'
import Badge from '@/components/ui/Badge'
import { ScoreGauge } from '@/components/ui/ScoreGauge'

const statusVariant: Record<Company['status'], 'primary' | 'success' | 'warning' | 'danger' | 'gray'> = {
  new: 'primary',
  contacted: 'warning',
  qualified: 'success',
  unqualified: 'danger',
  customer: 'success',
}

export function createCompanyColumns(options: {
  onDelete: (company: Company) => void
}): ColumnDef<Company, unknown>[] {
  return [
    {
      id: 'select',
      header: ({ table }) => (
        <input
          type="checkbox"
          checked={table.getIsAllPageRowsSelected()}
          onChange={table.getToggleAllPageRowsSelectedHandler()}
          className="h-4 w-4 rounded border-border"
          aria-label="Select all"
        />
      ),
      cell: ({ row }) => (
        <input
          type="checkbox"
          checked={row.getIsSelected()}
          onChange={row.getToggleSelectedHandler()}
          onClick={(e) => e.stopPropagation()}
          className="h-4 w-4 rounded border-border"
          aria-label="Select row"
        />
      ),
      size: 48,
      enableSorting: false,
      enableResizing: false,
    },
    {
      accessorKey: 'name',
      header: 'Company',
      size: 220,
      cell: ({ row }) => (
        <div>
          <Link
            href={`/companies/${row.original.id}`}
            onClick={(e) => e.stopPropagation()}
            className="font-medium text-foreground hover:text-primary"
          >
            {row.original.name}
          </Link>
          {row.original.domain && (
            <p className="text-xs text-muted-foreground">{row.original.domain}</p>
          )}
        </div>
      ),
    },
    {
      accessorKey: 'industry',
      header: 'Industry',
      size: 140,
      cell: ({ getValue }) => (
        <span className="text-muted-foreground">{String(getValue() ?? '—')}</span>
      ),
    },
    {
      accessorKey: 'country',
      header: 'Country',
      size: 100,
      cell: ({ getValue }) => (
        <span className="text-muted-foreground">{String(getValue() ?? '—')}</span>
      ),
    },
    {
      accessorKey: 'employee_count',
      header: 'Employees',
      size: 110,
      cell: ({ getValue }) => {
        const v = getValue() as number | undefined
        return <span>{v != null ? v.toLocaleString() : '—'}</span>
      },
    },
    {
      accessorKey: 'annual_revenue',
      header: 'Revenue',
      size: 110,
      cell: ({ getValue }) => {
        const v = getValue() as number | undefined
        return <span>{v != null ? `$${(v / 1_000_000).toFixed(1)}M` : '—'}</span>
      },
    },
    {
      id: 'score',
      header: 'Score',
      size: 80,
      accessorFn: (row) => row.lead_score?.score,
      cell: ({ row }) =>
        row.original.lead_score ? (
          <div className="flex items-center gap-2">
            <ScoreGauge score={row.original.lead_score.score} size={36} />
          </div>
        ) : (
          <span className="text-muted-foreground">—</span>
        ),
    },
    {
      accessorKey: 'status',
      header: 'Status',
      size: 100,
      cell: ({ getValue }) => {
        const status = getValue() as Company['status']
        return (
          <Badge variant={statusVariant[status]}>
            {status.charAt(0).toUpperCase() + status.slice(1)}
          </Badge>
        )
      },
    },
    {
      id: 'actions',
      header: '',
      size: 48,
      enableSorting: false,
      cell: ({ row }) => (
        <div className="flex items-center justify-end gap-1" onClick={(e) => e.stopPropagation()}>
          <Link
            href={`/companies/${row.original.id}`}
            className="rounded-md p-1.5 text-muted-foreground hover:bg-accent hover:text-foreground"
            title="Open 360°"
          >
            <ExternalLink className="h-4 w-4" />
          </Link>
          <button
            onClick={() => options.onDelete(row.original)}
            className="rounded-md p-1.5 text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
            title="Delete"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      ),
    },
  ]
}