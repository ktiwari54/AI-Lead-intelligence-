'use client'

import { useState, useMemo } from 'react'
import { useRouter } from 'next/navigation'
import { Plus, Building2 } from 'lucide-react'
import { toast } from 'sonner'
import { useCompanies, useDeleteCompany } from '@/hooks/useCompanies'
import { useDataTable } from '@/hooks/useDataTable'
import { useScoreCompany } from '@/hooks/useAI'
import { Company } from '@/types'
import { EntityDataTable } from '@/components/data-table/EntityDataTable'
import { BulkActionBar } from '@/components/data-table/BulkActionBar'
import { createCompanyColumns } from '@/features/companies/columns'
import { getSelectedIds, exportToCsv } from '@/lib/bulk-actions'
import { PageHeader } from '@/components/enterprise/PageHeader'
import { EmptyState } from '@/components/enterprise/EmptyState'
import { Card, CardContent } from '@/components/ui/card'
import Button from '@/components/ui/Button'
import Modal from '@/components/ui/Modal'
import Pagination from '@/components/ui/Pagination'

const COLUMN_ORDER = ['select', 'name', 'industry', 'country', 'employee_count', 'annual_revenue', 'score', 'status', 'actions']

export default function CompaniesPage() {
  const router = useRouter()
  const [page, setPage] = useState(1)
  const [perPage, setPerPage] = useState(25)
  const [search, setSearch] = useState('')
  const [deleteTarget, setDeleteTarget] = useState<Company | null>(null)
  const [bulkDeleteOpen, setBulkDeleteOpen] = useState(false)

  const tableState = useDataTable(COLUMN_ORDER)

  const { data, isLoading } = useCompanies({
    page,
    per_page: perPage,
    search: search || undefined,
  })

  const deleteCompany = useDeleteCompany()
  const scoreCompany = useScoreCompany()

  const columns = useMemo(
    () => createCompanyColumns({ onDelete: setDeleteTarget }),
    []
  )

  const items = data?.items ?? []
  const selectedIds = getSelectedIds(tableState.rowSelection)
  const selectedItems = items.filter((c) => selectedIds.includes(c.id))

  const handleDelete = async () => {
    if (!deleteTarget) return
    await deleteCompany.mutateAsync(deleteTarget.id)
    setDeleteTarget(null)
    tableState.clearSelection()
    toast.success('Company deleted')
  }

  const handleBulkDelete = async () => {
    await Promise.all(selectedIds.map((id) => deleteCompany.mutateAsync(id)))
    setBulkDeleteOpen(false)
    tableState.clearSelection()
    toast.success(`Deleted ${selectedIds.length} companies`)
  }

  const handleBulkExport = () => {
    exportToCsv(
      selectedItems as unknown as Record<string, unknown>[],
      [
        { key: 'name', label: 'Name' },
        { key: 'domain', label: 'Domain' },
        { key: 'industry', label: 'Industry' },
        { key: 'country', label: 'Country' },
        { key: 'employee_count', label: 'Employees' },
        { key: 'status', label: 'Status' },
      ],
      `companies-export-${Date.now()}.csv`
    )
    toast.success(`Exported ${selectedIds.length} companies`)
  }

  const handleBulkScore = async () => {
    toast.promise(
      Promise.all(selectedIds.map((id) => scoreCompany.mutateAsync({ companyId: id }))),
      {
        loading: `Scoring ${selectedIds.length} companies...`,
        success: 'Scoring complete',
        error: 'Some scores failed',
      }
    )
  }

  return (
    <div className="page-container space-y-6">
      <PageHeader
        title="Companies"
        description="Manage your company database, track lead scores, and run bulk AI operations."
        badge={`${data?.total ?? 0} records`}
        actions={
          <Button href="/companies/new" size="md">
            <Plus className="h-4 w-4 mr-1.5" />
            Add Company
          </Button>
        }
      />

      <Card>
        <CardContent className="p-0">
      <EntityDataTable
        data={items}
        columns={columns}
        loading={isLoading}
        entityType="company"
        searchValue={search}
        onSearchChange={(v) => { setSearch(v); setPage(1) }}
        searchPlaceholder="Search companies..."
        tableState={tableState}
        onRowClick={(company) => router.push(`/companies/${company.id}`)}
        getRowId={(row) => row.id}
        emptyState={
          <EmptyState
            icon={Building2}
            title="No companies found"
            description="Try adjusting your search or add your first company to get started."
          />
        }
      />
        </CardContent>
      </Card>

      {data && data.total_pages > 1 && (
        <Pagination
          page={page}
          totalPages={data.total_pages}
          total={data.total}
          perPage={perPage}
          onPageChange={setPage}
          onPerPageChange={(v) => { setPerPage(v); setPage(1) }}
        />
      )}

      <BulkActionBar
        selectedCount={tableState.selectedCount}
        onClear={tableState.clearSelection}
        actions={[
          { label: 'Export', onClick: handleBulkExport },
          { label: 'Score', onClick: handleBulkScore },
          { label: 'Delete', onClick: () => setBulkDeleteOpen(true), variant: 'danger' },
        ]}
      />

      <Modal
        open={deleteTarget !== null}
        onClose={() => setDeleteTarget(null)}
        title="Delete Company"
        footer={
          <div className="flex justify-end gap-3">
            <Button variant="secondary" onClick={() => setDeleteTarget(null)}>Cancel</Button>
            <Button variant="danger" onClick={handleDelete} loading={deleteCompany.isPending}>
              Delete
            </Button>
          </div>
        }
      >
        <p className="text-sm text-muted-foreground">
          Delete <span className="font-semibold text-foreground">{deleteTarget?.name}</span>?
          This cannot be undone.
        </p>
      </Modal>

      <Modal
        open={bulkDeleteOpen}
        onClose={() => setBulkDeleteOpen(false)}
        title="Delete Selected Companies"
        footer={
          <div className="flex justify-end gap-3">
            <Button variant="secondary" onClick={() => setBulkDeleteOpen(false)}>Cancel</Button>
            <Button variant="danger" onClick={handleBulkDelete} loading={deleteCompany.isPending}>
              Delete {selectedIds.length}
            </Button>
          </div>
        }
      >
        <p className="text-sm text-muted-foreground">
          Delete {selectedIds.length} selected companies? This cannot be undone.
        </p>
      </Modal>
    </div>
  )
}