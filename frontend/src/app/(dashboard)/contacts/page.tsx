'use client'

import { useState, useMemo } from 'react'
import { useRouter } from 'next/navigation'
import { Plus, Users, Filter } from 'lucide-react'
import { toast } from 'sonner'
import { useContacts, useDeleteContact } from '@/hooks/useContacts'
import { useDataTable } from '@/hooks/useDataTable'
import { useScoreContact } from '@/hooks/useAI'
import { Contact } from '@/types'
import { EntityDataTable } from '@/components/data-table/EntityDataTable'
import { BulkActionBar } from '@/components/data-table/BulkActionBar'
import { createContactColumns } from '@/features/contacts/columns'
import { getSelectedIds, exportToCsv } from '@/lib/bulk-actions'
import { PageHeader } from '@/components/enterprise/PageHeader'
import { EmptyState } from '@/components/enterprise/EmptyState'
import { Card, CardContent } from '@/components/ui/card'
import Button from '@/components/ui/Button'
import Modal from '@/components/ui/Modal'
import Pagination from '@/components/ui/Pagination'

const COLUMN_ORDER = ['select', 'name', 'title', 'company', 'department', 'email', 'score', 'status', 'actions']

const DEPARTMENTS = [
  'Engineering', 'Sales', 'Marketing', 'Finance', 'HR', 'Operations', 'Product', 'Legal',
]

export default function ContactsPage() {
  const router = useRouter()
  const [page, setPage] = useState(1)
  const [perPage, setPerPage] = useState(25)
  const [search, setSearch] = useState('')
  const [department, setDepartment] = useState('')
  const [deleteTarget, setDeleteTarget] = useState<Contact | null>(null)
  const [bulkDeleteOpen, setBulkDeleteOpen] = useState(false)

  const tableState = useDataTable(COLUMN_ORDER)

  const { data, isLoading } = useContacts({
    page,
    per_page: perPage,
    search: search || undefined,
    department: department || undefined,
  })

  const deleteContact = useDeleteContact()
  const scoreContact = useScoreContact()

  const columns = useMemo(
    () => createContactColumns({ onDelete: setDeleteTarget }),
    []
  )

  const items = data?.items ?? []
  const selectedIds = getSelectedIds(tableState.rowSelection)
  const selectedItems = items.filter((c) => selectedIds.includes(c.id))

  const handleDelete = async () => {
    if (!deleteTarget) return
    await deleteContact.mutateAsync(deleteTarget.id)
    setDeleteTarget(null)
    tableState.clearSelection()
    toast.success('Contact deleted')
  }

  const handleBulkDelete = async () => {
    await Promise.all(selectedIds.map((id) => deleteContact.mutateAsync(id)))
    setBulkDeleteOpen(false)
    tableState.clearSelection()
    toast.success(`Deleted ${selectedIds.length} contacts`)
  }

  const handleBulkExport = () => {
    exportToCsv(
      selectedItems.map((c) => ({
        first_name: c.first_name,
        last_name: c.last_name,
        email: c.email ?? '',
        title: c.title ?? '',
        department: c.department ?? '',
        company: c.company?.name ?? '',
        status: c.status,
      })),
      [
        { key: 'first_name', label: 'First Name' },
        { key: 'last_name', label: 'Last Name' },
        { key: 'email', label: 'Email' },
        { key: 'title', label: 'Title' },
        { key: 'department', label: 'Department' },
        { key: 'company', label: 'Company' },
        { key: 'status', label: 'Status' },
      ],
      `contacts-export-${Date.now()}.csv`
    )
    toast.success(`Exported ${selectedIds.length} contacts`)
  }

  const handleBulkScore = async () => {
    toast.promise(
      Promise.all(selectedIds.map((id) => scoreContact.mutateAsync({ contactId: id }))),
      {
        loading: `Scoring ${selectedIds.length} contacts...`,
        success: 'Scoring complete',
        error: 'Some scores failed',
      }
    )
  }

  return (
    <div className="page-container space-y-6">
      <PageHeader
        title="Contacts"
        description="Browse contacts, filter by department, and score leads with AI."
        badge={`${data?.total ?? 0} records`}
        actions={
          <Button href="/contacts/new" size="md">
            <Plus className="h-4 w-4 mr-1.5" />
            Add Contact
          </Button>
        }
      />

      <Card>
        <CardContent className="p-0">
      <EntityDataTable
        data={items}
        columns={columns}
        loading={isLoading}
        entityType="contact"
        searchValue={search}
        onSearchChange={(v) => { setSearch(v); setPage(1) }}
        searchPlaceholder="Search contacts..."
        tableState={tableState}
        onRowClick={(contact) => router.push(`/contacts/${contact.id}`)}
        getRowId={(row) => row.id}
        toolbarExtra={
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-muted-foreground" />
            <select
              value={department}
              onChange={(e) => { setDepartment(e.target.value); setPage(1) }}
              className="input-base text-sm"
            >
              <option value="">All Departments</option>
              {DEPARTMENTS.map((dept) => (
                <option key={dept} value={dept}>{dept}</option>
              ))}
            </select>
          </div>
        }
        emptyState={
          <EmptyState
            icon={Users}
            title="No contacts found"
            description="Try adjusting filters or add contacts from discovery results."
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
        title="Delete Contact"
        footer={
          <div className="flex justify-end gap-3">
            <Button variant="secondary" onClick={() => setDeleteTarget(null)}>Cancel</Button>
            <Button variant="danger" onClick={handleDelete} loading={deleteContact.isPending}>
              Delete
            </Button>
          </div>
        }
      >
        <p className="text-sm text-muted-foreground">
          Delete{' '}
          <span className="font-semibold text-foreground">
            {deleteTarget?.first_name} {deleteTarget?.last_name}
          </span>?
          This cannot be undone.
        </p>
      </Modal>

      <Modal
        open={bulkDeleteOpen}
        onClose={() => setBulkDeleteOpen(false)}
        title="Delete Selected Contacts"
        footer={
          <div className="flex justify-end gap-3">
            <Button variant="secondary" onClick={() => setBulkDeleteOpen(false)}>Cancel</Button>
            <Button variant="danger" onClick={handleBulkDelete} loading={deleteContact.isPending}>
              Delete {selectedIds.length}
            </Button>
          </div>
        }
      >
        <p className="text-sm text-muted-foreground">
          Delete {selectedIds.length} selected contacts? This cannot be undone.
        </p>
      </Modal>
    </div>
  )
}