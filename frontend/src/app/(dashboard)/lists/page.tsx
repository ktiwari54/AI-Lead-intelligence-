'use client'

import Link from 'next/link'
import { List, Plus, Building2, Users } from 'lucide-react'
import { PageHeader } from '@/components/enterprise/PageHeader'
import { Card, CardContent } from '@/components/ui/card'
import Badge from '@/components/ui/Badge'
import Button from '@/components/ui/Button'

const MOCK_LISTS = [
  { id: '1', name: 'Q3 Enterprise Targets', entities: 142, type: 'company', updated: '2026-06-27' },
  { id: '2', name: 'SaaS VP Sales', entities: 58, type: 'contact', updated: '2026-06-25' },
  { id: '3', name: 'Austin Fintech', entities: 31, type: 'company', updated: '2026-06-20' },
]

export default function ListsPage() {
  return (
    <div className="page-container space-y-6">
      <PageHeader
        title="Lists"
        description="Static collections of companies and contacts for campaigns, outreach, and exports."
        badge={`${MOCK_LISTS.length} lists`}
        actions={
          <Button disabled>
            <Plus className="mr-2 h-4 w-4" />
            Create list
          </Button>
        }
      />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {MOCK_LISTS.map((list) => (
          <Link key={list.id} href={`/search`}>
            <Card className="h-full transition-colors hover:border-primary/40">
              <CardContent className="p-5">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10">
                    <List className="h-5 w-5 text-primary" />
                  </div>
                  <Badge variant="secondary">{list.type}</Badge>
                </div>
                <p className="mt-3 font-semibold text-foreground">{list.name}</p>
                <div className="mt-2 flex items-center gap-3 text-xs text-muted-foreground">
                  <span className="inline-flex items-center gap-1">
                    {list.type === 'company' ? <Building2 className="h-3 w-3" /> : <Users className="h-3 w-3" />}
                    {list.entities} records
                  </span>
                  <span>Updated {list.updated}</span>
                </div>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  )
}