'use client'

import { useState } from 'react'
import { Activity, Mail, Phone, Video, Building2, User, Filter } from 'lucide-react'
import { PageHeader } from '@/components/enterprise/PageHeader'
import { Card, CardContent } from '@/components/ui/card'
import Badge from '@/components/ui/Badge'

type ActivityType = 'email' | 'call' | 'meeting' | 'note' | 'score' | 'crm'

interface ActivityItem {
  id: string
  type: ActivityType
  title: string
  description: string
  entity: string
  entityType: 'company' | 'contact'
  date: string
  user: string
}

const MOCK_ACTIVITIES: ActivityItem[] = [
  { id: '1', type: 'email', title: 'Follow-up sent', description: 'Re: Enterprise pricing proposal', entity: 'Jordan Reeves', entityType: 'contact', date: '2026-06-28T10:30:00Z', user: 'Alex Chen' },
  { id: '2', type: 'call', title: 'Discovery call completed', description: '32 min — positive outcome', entity: 'CloudForge Analytics', entityType: 'company', date: '2026-06-27T15:00:00Z', user: 'Alex Chen' },
  { id: '3', type: 'score', title: 'AI score generated', description: 'Lead score updated to 82', entity: 'Nexus Systems', entityType: 'company', date: '2026-06-27T09:15:00Z', user: 'System' },
  { id: '4', type: 'meeting', title: 'Demo scheduled', description: 'Product walkthrough — July 2', entity: 'Sarah Kim', entityType: 'contact', date: '2026-06-26T14:00:00Z', user: 'Jordan Lee' },
  { id: '5', type: 'crm', title: 'Deal stage updated', description: 'Moved to Negotiation — $45K', entity: 'Acme Corp Deal', entityType: 'company', date: '2026-06-26T11:20:00Z', user: 'Alex Chen' },
  { id: '6', type: 'note', title: 'Note added', description: 'Budget review expected Q3', entity: 'Taylor Brooks', entityType: 'contact', date: '2026-06-25T16:45:00Z', user: 'Jordan Lee' },
]

const TYPE_ICON: Record<ActivityType, typeof Activity> = {
  email: Mail,
  call: Phone,
  meeting: Video,
  note: Activity,
  score: Activity,
  crm: Building2,
}

const TYPE_VARIANT: Record<ActivityType, 'primary' | 'success' | 'warning' | 'secondary'> = {
  email: 'primary',
  call: 'success',
  meeting: 'warning',
  note: 'secondary',
  score: 'primary',
  crm: 'secondary',
}

function relativeTime(dateStr: string) {
  const diff = Date.now() - new Date(dateStr).getTime()
  const hours = Math.floor(diff / 3_600_000)
  if (hours < 1) return 'Just now'
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  if (days === 1) return 'Yesterday'
  return `${days}d ago`
}

export default function ActivitiesPage() {
  const [typeFilter, setTypeFilter] = useState<ActivityType | 'all'>('all')

  const items = MOCK_ACTIVITIES.filter((a) => typeFilter === 'all' || a.type === typeFilter)

  return (
    <div className="page-container space-y-6">
      <PageHeader
        title="Activities"
        description="Chronological feed of emails, calls, meetings, scores, and CRM updates."
        badge={`${items.length} recent`}
      />

      <div className="flex flex-wrap items-center gap-2">
        <Filter className="h-4 w-4 text-muted-foreground" />
        {(['all', 'email', 'call', 'meeting', 'score', 'crm', 'note'] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTypeFilter(t)}
            className={`rounded-lg px-3 py-1.5 text-xs font-medium capitalize transition-colors ${
              typeFilter === t ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground hover:text-foreground'
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      <div className="space-y-3">
        {items.map((item) => {
          const Icon = TYPE_ICON[item.type]
          const EntityIcon = item.entityType === 'company' ? Building2 : User
          return (
            <Card key={item.id}>
              <CardContent className="flex items-start gap-4 p-4">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary/10">
                  <Icon className="h-5 w-5 text-primary" />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="text-sm font-semibold text-foreground">{item.title}</p>
                    <Badge variant={TYPE_VARIANT[item.type]}>{item.type}</Badge>
                  </div>
                  <p className="mt-0.5 text-sm text-muted-foreground">{item.description}</p>
                  <div className="mt-2 flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
                    <span className="inline-flex items-center gap-1">
                      <EntityIcon className="h-3 w-3" />
                      {item.entity}
                    </span>
                    <span>{item.user}</span>
                    <span>{relativeTime(item.date)}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>
    </div>
  )
}