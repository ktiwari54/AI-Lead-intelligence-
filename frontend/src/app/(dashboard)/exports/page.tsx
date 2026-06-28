'use client'

import { ExportWizard } from '@/features/exports/ExportWizard'
import { useExports } from '@/hooks/useExports'
import { PageHeader } from '@/components/enterprise/PageHeader'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import Badge from '@/components/ui/Badge'

const STATUS_VARIANT: Record<string, 'success' | 'warning' | 'danger' | 'gray'> = {
  COMPLETED: 'success',
  PENDING: 'warning',
  PROCESSING: 'warning',
  FAILED: 'danger',
}

export default function ExportsPage() {
  const { data: exportsData, isLoading } = useExports()

  return (
    <div className="page-container mx-auto max-w-3xl space-y-6">
      <PageHeader
        title="Export Data"
        description="Download companies, contacts, or leads in CSV, JSON, or Excel format."
      />

      <ExportWizard />

      <Card className="overflow-hidden">
        <CardHeader className="border-b border-border pb-3">
          <CardTitle className="text-base">Export History</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
        {isLoading ? (
          <Skeleton className="m-4 h-32 rounded-lg" />
        ) : exportsData?.items.length === 0 ? (
          <p className="px-4 py-8 text-center text-sm text-muted-foreground">No exports yet</p>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-muted/50">
              <tr>
                <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Name</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Type</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Format</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Status</th>
              </tr>
            </thead>
            <tbody>
              {exportsData?.items.map((job) => (
                <tr key={job.id} className="border-t border-border">
                  <td className="px-4 py-2.5 font-medium text-foreground">{job.name}</td>
                  <td className="px-4 py-2.5 text-muted-foreground capitalize">{job.entity_type}</td>
                  <td className="px-4 py-2.5 text-muted-foreground">{job.format}</td>
                  <td className="px-4 py-2.5">
                    <Badge variant={STATUS_VARIANT[job.status] ?? 'gray'}>{job.status}</Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        </CardContent>
      </Card>
    </div>
  )
}