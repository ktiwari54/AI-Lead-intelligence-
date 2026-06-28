'use client'

import { useEffect } from 'react'
import { AlertTriangle } from 'lucide-react'
import { EmptyState } from '@/components/enterprise/EmptyState'

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    console.error(error)
  }, [error])

  return (
    <div className="page-container flex min-h-[50vh] items-center justify-center">
      <EmptyState
        icon={AlertTriangle}
        title="Something went wrong"
        description={error.message || 'An unexpected error occurred. Try refreshing the page.'}
        action={{ label: 'Try again', onClick: reset }}
        className="max-w-md"
      />
    </div>
  )
}