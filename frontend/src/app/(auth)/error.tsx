'use client'

import { useEffect } from 'react'
import Link from 'next/link'
import { AlertTriangle } from 'lucide-react'

export default function AuthError({
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
    <div className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-b from-slate-50 to-white px-6 text-center">
      <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-destructive/10 mb-6">
        <AlertTriangle className="h-8 w-8 text-destructive" />
      </div>

      <h1 className="text-2xl font-bold text-foreground mb-2">Something went wrong</h1>
      <p className="text-muted-foreground max-w-sm mb-8 text-sm">
        An unexpected error occurred. Please try again or contact support if the problem persists.
      </p>

      <div className="flex items-center gap-3">
        <button
          onClick={reset}
          className="rounded-lg border border-border bg-card px-4 py-2 text-sm font-medium text-foreground hover:bg-accent transition-colors"
        >
          Try again
        </button>
        <Link
          href="/login"
          className="rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90 transition-colors"
        >
          Back to login
        </Link>
      </div>
    </div>
  )
}
