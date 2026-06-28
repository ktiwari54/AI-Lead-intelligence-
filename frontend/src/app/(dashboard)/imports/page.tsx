'use client'

import { ImportWizard } from '@/features/imports/ImportWizard'
import { PageHeader } from '@/components/enterprise/PageHeader'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import Badge from '@/components/ui/Badge'
import { Clock } from 'lucide-react'

const RECENT_IMPORTS = [
  { name: 'companies_2026-06-15.csv', rows: 1250, status: 'Completed' },
  { name: 'contacts_batch_2.csv', rows: 430, status: 'Completed' },
  { name: 'leads_q2.csv', rows: 89, status: 'Failed' },
]

export default function ImportsPage() {
  const statusVariant: Record<string, 'success' | 'danger'> = {
    Completed: 'success',
    Failed: 'danger',
  }

  return (
    <div className="page-container mx-auto max-w-3xl space-y-6">
      <PageHeader
        title="Import Data"
        description="Upload CSV files to bulk-import companies or contacts into your workspace."
      />

      <ImportWizard />

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-base">
            <Clock className="h-4 w-4 text-muted-foreground" />
            Recent Imports
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {RECENT_IMPORTS.map((item) => (
            <div key={item.name} className="flex items-center justify-between rounded-lg border border-border px-4 py-3 text-sm">
              <span className="font-medium text-foreground">{item.name}</span>
              <div className="flex items-center gap-2">
                <span className="text-muted-foreground">{item.rows} rows</span>
                <Badge variant={statusVariant[item.status] ?? 'gray'}>{item.status}</Badge>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  )
}