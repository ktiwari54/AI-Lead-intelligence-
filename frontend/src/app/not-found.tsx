import Link from 'next/link'
import { Sparkles, Home } from 'lucide-react'

export default function RootNotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-b from-slate-50 to-white px-6 text-center">
      <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10 mb-6">
        <Sparkles className="h-8 w-8 text-primary" />
      </div>

      <p className="text-sm font-semibold uppercase tracking-widest text-primary mb-2">404</p>
      <h1 className="text-3xl font-bold text-foreground mb-3">Page not found</h1>
      <p className="text-muted-foreground max-w-sm mb-8">
        This page doesn&apos;t exist. Let&apos;s get you back to the platform.
      </p>

      <Link
        href="/dashboard"
        className="inline-flex items-center gap-2 rounded-lg bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground shadow-sm hover:bg-primary/90 transition-colors"
      >
        <Home className="h-4 w-4" />
        Back to Dashboard
      </Link>
    </div>
  )
}
