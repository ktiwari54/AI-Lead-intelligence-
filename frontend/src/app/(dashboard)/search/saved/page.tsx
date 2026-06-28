'use client'

import Link from 'next/link'
import { Bookmark, Search, Plus } from 'lucide-react'
import { useSavedSearches } from '@/hooks/useSearch'
import { PageHeader } from '@/components/enterprise/PageHeader'
import { EmptyState } from '@/components/enterprise/EmptyState'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/Button'
import { Skeleton } from '@/components/ui/skeleton'

export default function SavedSearchesPage() {
  const { data: saved = [], isLoading } = useSavedSearches()

  return (
    <div className="page-container">
      <PageHeader
        title="Saved Searches"
        description="Pinned discovery queries you run frequently. Launch, edit filters, or share with your team."
        actions={
          <Button asChild>
            <Link href="/search">
              <Plus className="mr-2 h-4 w-4" />
              New search
            </Link>
          </Button>
        }
      />

      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-32 rounded-xl" />
          ))}
        </div>
      ) : saved.length === 0 ? (
        <EmptyState
          icon={Bookmark}
          title="No saved searches yet"
          description="Run a discovery search and save it from the results page to build your library of go-to queries."
          action={{ label: 'Start discovery', onClick: () => { window.location.href = '/search' } }}
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {saved.map((item) => {
            const q = String((item.filters as { query?: string })?.query ?? item.name)
            return (
              <Card key={item.id} className="transition-shadow hover:shadow-md">
                <CardContent className="flex flex-col gap-4 p-5">
                  <div className="flex items-start gap-3">
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10">
                      <Bookmark className="h-4 w-4 text-primary" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <h3 className="truncate font-semibold text-foreground">{item.name}</h3>
                      <p className="mt-1 line-clamp-2 text-sm text-muted-foreground">{q}</p>
                    </div>
                  </div>
                  <Button variant="outline" size="sm" asChild className="w-full">
                    <Link href={`/search/results?q=${encodeURIComponent(q)}`}>
                      <Search className="mr-2 h-4 w-4" />
                      Run search
                    </Link>
                  </Button>
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}
    </div>
  )
}