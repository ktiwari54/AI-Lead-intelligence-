'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { FileQuestion, Home, ArrowLeft } from 'lucide-react'
import { Button } from '@/components/ui/Button'

export default function NotFound() {
  const router = useRouter()

  return (
    <div className="page-container flex min-h-[60vh] flex-col items-center justify-center text-center">
      <div className="flex h-20 w-20 items-center justify-center rounded-2xl bg-muted mb-6">
        <FileQuestion className="h-10 w-10 text-muted-foreground" />
      </div>

      <h1 className="text-2xl font-bold text-foreground mb-2">Page not found</h1>
      <p className="text-muted-foreground max-w-md mb-8">
        The page you were looking for doesn&apos;t exist or has been moved.
        Double-check the URL or navigate back to safety.
      </p>

      <div className="flex items-center gap-3">
        <Button variant="outline" onClick={() => router.back()}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Go back
        </Button>
        <Button asChild>
          <Link href="/dashboard">
            <Home className="mr-2 h-4 w-4" />
            Dashboard
          </Link>
        </Button>
      </div>
    </div>
  )
}
