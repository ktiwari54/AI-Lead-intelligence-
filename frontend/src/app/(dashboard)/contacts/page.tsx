'use client'

import { useState } from 'react'
import { useContacts, useDeleteContact } from '@/hooks/useContacts'
import { Contact } from '@/types'
import Badge from '@/components/ui/Badge'
import Button from '@/components/ui/Button'
import Pagination from '@/components/ui/Pagination'
import Modal from '@/components/ui/Modal'
import {
  PlusIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  TrashIcon,
  PencilSquareIcon,
  UsersIcon,
} from '@heroicons/react/24/outline'

export default function ContactsPage() {
  const [page, setPage] = useState(1)
  const [perPage, setPerPage] = useState(25)
  const [search, setSearch] = useState('')
  const [department, setDepartment] = useState('')
  const [deleteTarget, setDeleteTarget] = useState<Contact | null>(null)

  const { data, isLoading } = useContacts({
    page,
    per_page: perPage,
    search: search || undefined,
    department: department || undefined,
  })

  const deleteContact = useDeleteContact()

  const handleDelete = async () => {
    if (!deleteTarget) return
    await deleteContact.mutateAsync(deleteTarget.id)
    setDeleteTarget(null)
  }

  const statusColors: Record<Contact['status'], 'primary' | 'success' | 'warning' | 'danger' | 'gray'> = {
    new: 'primary',
    contacted: 'warning',
    qualified: 'success',
    unqualified: 'danger',
    customer: 'success',
  }

  const DEPARTMENTS = [
    'Engineering', 'Sales', 'Marketing', 'Finance', 'HR', 'Operations', 'Product', 'Legal',
  ]

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Contacts</h1>
          <p className="mt-0.5 text-sm text-gray-500 dark:text-gray-400">
            {data?.total ?? 0} total contacts
          </p>
        </div>
        <Button href="/contacts/new" size="md">
          <PlusIcon className="h-4 w-4 mr-1.5" />
          Add Contact
        </Button>
      </div>

      {/* Filters */}
      <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-4">
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search contacts..."
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1) }}
              className="input-base pl-9"
            />
          </div>
          <div className="flex items-center gap-2">
            <FunnelIcon className="h-4 w-4 text-gray-400 flex-shrink-0" />
            <select
              value={department}
              onChange={(e) => { setDepartment(e.target.value); setPage(1) }}
              className="input-base"
            >
              <option value="">All Departments</option>
              {DEPARTMENTS.map((dept) => (
                <option key={dept} value={dept}>{dept}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-800">
            <thead className="bg-gray-50 dark:bg-gray-800/50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Name</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Title</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Company</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Department</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Email</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Score</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Status</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
              {isLoading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <tr key={i}>
                    {Array.from({ length: 8 }).map((_, j) => (
                      <td key={j} className="px-4 py-3">
                        <div className="h-4 bg-gray-100 dark:bg-gray-800 rounded animate-pulse" />
                      </td>
                    ))}
                  </tr>
                ))
              ) : data?.items.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-4 py-12 text-center">
                    <UsersIcon className="mx-auto h-10 w-10 text-gray-300 dark:text-gray-700" />
                    <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">No contacts found</p>
                  </td>
                </tr>
              ) : (
                data?.items.map((contact) => (
                  <tr
                    key={contact.id}
                    className="hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
                  >
                    <td className="px-4 py-3">
                      <div>
                        <p className="text-sm font-medium text-gray-900 dark:text-white">
                          {contact.first_name} {contact.last_name}
                        </p>
                        {contact.phone && (
                          <p className="text-xs text-gray-400">{contact.phone}</p>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">{contact.title ?? '—'}</td>
                    <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                      {contact.company?.name ?? '—'}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">{contact.department ?? '—'}</td>
                    <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                      {contact.email ? (
                        <a
                          href={`mailto:${contact.email}`}
                          className="text-primary-600 dark:text-primary-400 hover:underline"
                        >
                          {contact.email}
                        </a>
                      ) : '—'}
                    </td>
                    <td className="px-4 py-3">
                      {contact.lead_score ? (
                        <span className="inline-flex items-center gap-1">
                          <span className="text-sm font-semibold text-gray-900 dark:text-white">
                            {contact.lead_score.score}
                          </span>
                          <Badge
                            variant={
                              contact.lead_score.grade === 'A' ? 'success'
                                : contact.lead_score.grade === 'B' ? 'primary'
                                : contact.lead_score.grade === 'C' ? 'warning'
                                : 'danger'
                            }
                          >
                            {contact.lead_score.grade}
                          </Badge>
                        </span>
                      ) : (
                        <span className="text-sm text-gray-400">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <Badge variant={statusColors[contact.status]}>
                        {contact.status.charAt(0).toUpperCase() + contact.status.slice(1)}
                      </Badge>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-end gap-1">
                        <button
                          className="p-1.5 text-gray-400 hover:text-primary-600 hover:bg-primary-50 dark:hover:bg-primary-950 rounded-lg transition-colors"
                          title="Edit"
                        >
                          <PencilSquareIcon className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => setDeleteTarget(contact)}
                          className="p-1.5 text-gray-400 hover:text-danger-600 hover:bg-danger-50 dark:hover:bg-danger-950 rounded-lg transition-colors"
                          title="Delete"
                        >
                          <TrashIcon className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {data && data.total_pages > 1 && (
          <div className="px-4 py-3 border-t border-gray-100 dark:border-gray-800">
            <Pagination
              page={page}
              totalPages={data.total_pages}
              total={data.total}
              perPage={perPage}
              onPageChange={setPage}
              onPerPageChange={(v) => { setPerPage(v); setPage(1) }}
            />
          </div>
        )}
      </div>

      {/* Delete confirmation modal */}
      <Modal
        open={deleteTarget !== null}
        onClose={() => setDeleteTarget(null)}
        title="Delete Contact"
        footer={
          <div className="flex justify-end gap-3">
            <Button variant="secondary" onClick={() => setDeleteTarget(null)}>
              Cancel
            </Button>
            <Button
              variant="danger"
              onClick={handleDelete}
              loading={deleteContact.isPending}
            >
              Delete
            </Button>
          </div>
        }
      >
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Are you sure you want to delete{' '}
          <span className="font-semibold text-gray-900 dark:text-white">
            {deleteTarget?.first_name} {deleteTarget?.last_name}
          </span>?
          This action cannot be undone.
        </p>
      </Modal>
    </div>
  )
}
