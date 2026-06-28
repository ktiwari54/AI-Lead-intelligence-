'use client'

import { useState } from 'react'
import { Video, Plus, Calendar, Clock, User } from 'lucide-react'
import { PageHeader } from '@/components/enterprise/PageHeader'
import { EmptyState } from '@/components/enterprise/EmptyState'
import { Card, CardContent } from '@/components/ui/card'
import Badge from '@/components/ui/Badge'
import Button from '@/components/ui/Button'

interface Meeting {
  id: string
  title: string
  contact: string
  company: string
  date: string
  time: string
  duration: string
  status: 'scheduled' | 'completed' | 'cancelled' | 'proposed'
}

const MOCK_MEETINGS: Meeting[] = [
  { id: '1', title: 'Product demo', contact: 'Sarah Kim', company: 'Nexus Systems', date: '2026-07-02', time: '10:00 AM', duration: '45 min', status: 'scheduled' },
  { id: '2', title: 'Technical deep-dive', contact: 'Jordan Reeves', company: 'CloudForge', date: '2026-07-05', time: '2:00 PM', duration: '60 min', status: 'proposed' },
  { id: '3', title: 'Quarterly business review', contact: 'Alex Morgan', company: 'Acme Corp', date: '2026-06-20', time: '11:00 AM', duration: '30 min', status: 'completed' },
]

const STATUS_VARIANT: Record<Meeting['status'], 'primary' | 'success' | 'danger' | 'warning'> = {
  scheduled: 'primary',
  proposed: 'warning',
  completed: 'success',
  cancelled: 'danger',
}

export default function MeetingsPage() {
  const [view, setView] = useState<'upcoming' | 'past'>('upcoming')

  const today = '2026-06-28'
  const upcoming = MOCK_MEETINGS.filter((m) => m.date >= today && m.status !== 'completed')
  const past = MOCK_MEETINGS.filter((m) => m.date < today || m.status === 'completed')
  const meetings = view === 'upcoming' ? upcoming : past

  return (
    <div className="page-container space-y-6">
      <PageHeader
        title="Meetings"
        description="Schedule and track product demos, discovery calls, and reviews."
        badge={`${upcoming.length} upcoming`}
        actions={
          <Button disabled>
            <Plus className="mr-2 h-4 w-4" />
            Schedule meeting
          </Button>
        }
      />

      <div className="flex gap-1 border-b border-border">
        {(['upcoming', 'past'] as const).map((v) => (
          <button
            key={v}
            onClick={() => setView(v)}
            className={`shrink-0 border-b-2 px-4 py-2.5 text-sm font-medium capitalize transition-colors ${
              view === v ? 'border-primary text-primary' : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            {v}
          </button>
        ))}
      </div>

      {meetings.length === 0 ? (
        <EmptyState
          icon={Video}
          title="No meetings"
          description="Scheduled meetings will appear here with contact and company context."
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {meetings.map((m) => (
            <Card key={m.id}>
              <CardContent className="p-5">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10">
                      <Video className="h-4 w-4 text-primary" />
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-foreground">{m.title}</p>
                      <p className="text-xs text-muted-foreground">{m.company}</p>
                    </div>
                  </div>
                  <Badge variant={STATUS_VARIANT[m.status]}>{m.status}</Badge>
                </div>
                <div className="mt-4 space-y-1.5 text-xs text-muted-foreground">
                  <p className="flex items-center gap-1.5">
                    <User className="h-3.5 w-3.5" />
                    {m.contact}
                  </p>
                  <p className="flex items-center gap-1.5">
                    <Calendar className="h-3.5 w-3.5" />
                    {m.date} at {m.time}
                  </p>
                  <p className="flex items-center gap-1.5">
                    <Clock className="h-3.5 w-3.5" />
                    {m.duration}
                  </p>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}