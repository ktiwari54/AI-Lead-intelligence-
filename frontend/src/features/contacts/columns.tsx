'use client'

import { ColumnDef } from '@tanstack/react-table'
import Link from 'next/link'
import { Trash2, ExternalLink, CheckCircle2 } from 'lucide-react'
import { Contact } from '@/types'
import Badge from '@/components/ui/Badge'
import { ScoreGauge } from '@/components/ui/ScoreGauge'

const statusVariant: Record<Contact['status'], 'primary' | 'success' | 'warning' | 'danger' | 'gray'> = {
  new: 'primary',
  contacted: 'warning',
  qualified: 'success',
  unqualified: 'danger',
  customer: 'success',
}

export function createContactColumns(options: {
  onDelete: (contact: Contact) => void
}): ColumnDef<Contact, unknown>[] {
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
      id: 'name',
      header: 'Contact',
      size: 200,
      accessorFn: (row) => `${row.first_name} ${row.last_name}`,
      cell: ({ row }) => (
        <div>
          <Link
            href={`/contacts/${row.original.id}`}
            onClick={(e) => e.stopPropagation()}
            className="font-medium text-foreground hover:text-primary"
          >
            {row.original.first_name} {row.original.last_name}
          </Link>
          {row.original.phone && (
            <p className="text-xs text-muted-foreground">{row.original.phone}</p>
          )}
        </div>
      ),
    },
    {
      accessorKey: 'title',
      header: 'Title',
      size: 160,
      cell: ({ getValue }) => (
        <span className="text-muted-foreground">{String(getValue() ?? '—')}</span>
      ),
    },
    {
      id: 'company',
      header: 'Company',
      size: 160,
      accessorFn: (row) => row.company?.name,
      cell: ({ row }) => (
        <span className="text-muted-foreground">
          {row.original.company?.name ?? '—'}
        </span>
      ),
    },
    {
      accessorKey: 'department',
      header: 'Department',
      size: 130,
      cell: ({ getValue }) => (
        <span className="text-muted-foreground">{String(getValue() ?? '—')}</span>
      ),
    },
    {
      accessorKey: 'email',
      header: 'Email',
      size: 200,
      cell: ({ getValue }) => {
        const email = getValue() as string | undefined
        return email ? (
          <div className="flex items-center gap-1.5">
            <a
              href={`mailto:${email}`}
              onClick={(e) => e.stopPropagation()}
              className="text-primary hover:underline truncate"
            >
              {email}
            </a>
            <CheckCircle2 className="h-3.5 w-3.5 shrink-0 text-success" />
          </div>
        ) : (
          <span className="text-muted-foreground">—</span>
        )
      },
    },
    {
      id: 'score',
      header: 'Score',
      size: 80,
      accessorFn: (row) => row.lead_score?.score,
      cell: ({ row }) =>
        row.original.lead_score ? (
          <ScoreGauge score={row.original.lead_score.score} size={36} />
        ) : (
          <span className="text-muted-foreground">—</span>
        ),
    },
    {
      accessorKey: 'status',
      header: 'Status',
      size: 100,
      cell: ({ getValue }) => {
        const status = getValue() as Contact['status']
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
            href={`/contacts/${row.original.id}`}
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