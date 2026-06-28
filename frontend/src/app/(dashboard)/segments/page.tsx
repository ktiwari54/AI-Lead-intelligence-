'use client'

import { Target, Sparkles } from 'lucide-react'
import { PageHeader } from '@/components/enterprise/PageHeader'
import { Card, CardContent } from '@/components/ui/card'
import Badge from '@/components/ui/Badge'
import Button from '@/components/ui/Button'

const MOCK_SEGMENTS = [
  { id: '1', name: 'High-intent SaaS', rules: 'Industry = SaaS · Score ≥ 75', count: 284, auto: true },
  { id: '2', name: 'Enterprise 500+', rules: 'Employees ≥ 500 · Country = US', count: 156, auto: true },
  { id: '3', name: 'Needs nurture', rules: 'Score 50–74 · Status = contacted', count: 412, auto: true },
]

export default function SegmentsPage() {
  return (
    <div className="page-container space-y-6">
      <PageHeader
        title="Segments"
        description="Dynamic audiences that auto-update when records match your filter criteria."
        badge={`${MOCK_SEGMENTS.length} active`}
        actions={
          <Button disabled>
            <Target className="mr-2 h-4 w-4" />
            Create segment
          </Button>
        }
      />

      <div className="space-y-3">
        {MOCK_SEGMENTS.map((seg) => (
          <Card key={seg.id}>
            <CardContent className="flex items-center justify-between gap-4 p-5">
              <div className="flex items-start gap-4">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary/10">
                  <Target className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="font-semibold text-foreground">{seg.name}</p>
                    {seg.auto && <Badge variant="primary">Auto-sync</Badge>}
                  </div>
                  <p className="mt-1 text-sm text-muted-foreground">{seg.rules}</p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-2xl font-bold text-foreground">{seg.count}</p>
                <p className="text-xs text-muted-foreground">records</p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card className="border-dashed">
        <CardContent className="flex items-center gap-3 p-5 text-sm text-muted-foreground">
          <Sparkles className="h-5 w-5 text-primary" />
          Segments power targeted discovery, batch scoring, and scheduled exports.
        </CardContent>
      </Card>
    </div>
  )
}