import { clsx } from 'clsx'
import { ChevronLeftIcon, ChevronRightIcon } from '@heroicons/react/24/outline'

interface PaginationProps {
  page: number
  totalPages: number
  total: number
  perPage: number
  onPageChange: (page: number) => void
  onPerPageChange: (perPage: number) => void
}

const PER_PAGE_OPTIONS = [10, 25, 50, 100]

export default function Pagination({
  page,
  totalPages,
  total,
  perPage,
  onPageChange,
  onPerPageChange,
}: PaginationProps) {
  const start = (page - 1) * perPage + 1
  const end = Math.min(page * perPage, total)

  return (
    <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
      <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
        <span>
          Showing <span className="font-medium text-gray-700 dark:text-gray-200">{start}</span> to{' '}
          <span className="font-medium text-gray-700 dark:text-gray-200">{end}</span> of{' '}
          <span className="font-medium text-gray-700 dark:text-gray-200">{total}</span> results
        </span>
        <select
          value={perPage}
          onChange={(e) => onPerPageChange(Number(e.target.value))}
          className="ml-2 text-xs border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 px-2 py-1 focus:outline-none focus:ring-1 focus:ring-primary-500"
        >
          {PER_PAGE_OPTIONS.map((opt) => (
            <option key={opt} value={opt}>{opt} / page</option>
          ))}
        </select>
      </div>

      <div className="flex items-center gap-1">
        <button
          onClick={() => onPageChange(page - 1)}
          disabled={page <= 1}
          className={clsx(
            'p-1.5 rounded-lg border transition-colors text-gray-500 dark:text-gray-400',
            page <= 1
              ? 'border-gray-200 dark:border-gray-800 opacity-40 cursor-not-allowed'
              : 'border-gray-300 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800'
          )}
        >
          <ChevronLeftIcon className="h-4 w-4" />
        </button>

        {Array.from({ length: Math.min(totalPages, 7) }, (_, i) => {
          let p: number
          if (totalPages <= 7) {
            p = i + 1
          } else if (page <= 4) {
            p = i + 1
            if (i === 6) p = totalPages
          } else if (page >= totalPages - 3) {
            p = totalPages - 6 + i
            if (i === 0) p = 1
          } else {
            const mid = [1, page - 1, page, page + 1, totalPages]
            p = [1, page - 1, page, page + 1, totalPages][i] ?? i + 1
            if (i === 5) p = totalPages - 1
            if (i === 6) p = totalPages
          }

          return (
            <button
              key={p}
              onClick={() => onPageChange(p)}
              className={clsx(
                'min-w-[32px] h-8 px-2 rounded-lg border text-xs font-medium transition-colors',
                page === p
                  ? 'bg-primary-600 border-primary-600 text-white'
                  : 'border-gray-300 dark:border-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800'
              )}
            >
              {p}
            </button>
          )
        })}

        <button
          onClick={() => onPageChange(page + 1)}
          disabled={page >= totalPages}
          className={clsx(
            'p-1.5 rounded-lg border transition-colors text-gray-500 dark:text-gray-400',
            page >= totalPages
              ? 'border-gray-200 dark:border-gray-800 opacity-40 cursor-not-allowed'
              : 'border-gray-300 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800'
          )}
        >
          <ChevronRightIcon className="h-4 w-4" />
        </button>
      </div>
    </div>
  )
}
