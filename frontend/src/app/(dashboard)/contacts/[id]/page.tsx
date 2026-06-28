'use client'

import { useState, useEffect } from 'react'
import { useAIAssistantStore } from '@/stores/ai-assistant-store'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import {
  Mail,
  Phone,
  Building2,
  Activity,
  StickyNote,
  CheckSquare,
  CheckCircle2,
  Video,
  Clock,
  ArrowUpRight,
} from 'lucide-react'
import { toast } from 'sonner'
import { useContact } from '@/hooks/useContacts'
import { useScoreContact } from '@/hooks/useAI'
import { Entity360Layout } from '@/components/entity/Entity360Layout'
import { EntityHeader } from '@/components/entity/EntityHeader'
import { AISummaryPanel } from '@/components/entity/AISummaryPanel'
import Badge from '@/components/ui/Badge'
import Button from '@/components/ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'

const TABS = [
  { id: 'overview', label: 'Overview' },
  { id: 'activity', label: 'Activity' },
  { id: 'emails', label: 'Emails' },
  { id: 'calls', label: 'Calls' },
  { id: 'meetings', label: 'Meetings' },
  { id: 'notes', label: 'Notes' },
  { id: 'tasks', label: 'Tasks' },
]

const MOCK_ACTIVITY = [
  { date: '2026-06-18', type: 'email', description: 'Follow-up email sent' },
  { date: '2026-06-12', type: 'call', description: 'Discovery call — 30 min' },
  { date: '2026-06-05', type: 'meeting', description: 'Product demo scheduled' },
]

const MOCK_EMAILS = [
  { subject: 'Re: Enterprise pricing', date: '2026-06-18', direction: 'outbound', status: 'opened' },
  { subject: 'Introduction — AI Lead Intelligence', date: '2026-06-10', direction: 'outbound', status: 'replied' },
  { subject: 'Thanks for connecting', date: '2026-06-02', direction: 'inbound', status: 'read' },
]

const MOCK_CALLS = [
  { title: 'Discovery call', date: '2026-06-12', duration: '32 min', outcome: 'Positive' },
  { title: 'Voicemail follow-up', date: '2026-06-08', duration: '4 min', outcome: 'No answer' },
]

const MOCK_MEETINGS = [
  { title: 'Product demo', date: '2026-06-25', time: '10:00 AM', status: 'scheduled' },
  { title: 'Technical deep-dive', date: '2026-07-02', time: '2:00 PM', status: 'proposed' },
]

const MOCK_NOTES = [
  { author: 'Alex Chen', date: '2026-06-15', text: 'Interested in enterprise plan. Follow up after Q3 budget review.' },
  { author: 'Jordan Lee', date: '2026-06-01', text: 'Met at SaaStr conference. Strong technical background.' },
]

const MOCK_TASKS = [
  { title: 'Send pricing proposal', due: '2026-07-01', priority: 'high', done: false },
  { title: 'Schedule technical deep-dive', due: '2026-06-25', priority: 'medium', done: false },
  { title: 'Connect on LinkedIn', due: '2026-06-10', priority: 'low', done: true },
]

function scoreToRecommendation(score?: number): 'pursue' | 'nurture' | 'deprioritize' {
  if (score == null) return 'nurture'
  if (score >= 75) return 'pursue'
  if (score >= 50) return 'nurture'
  return 'deprioritize'
}

const priorityVariant: Record<string, 'danger' | 'warning' | 'gray'> = {
  high: 'danger',
  medium: 'warning',
  low: 'gray',
}

const emailStatusVariant: Record<string, 'success' | 'primary' | 'secondary'> = {
  opened: 'primary',
  replied: 'success',
  read: 'secondary',
}

function Contact360Skeleton() {
  return (
    <div className="page-container space-y-6">
      <Skeleton className="h-4 w-24" />
      <Skeleton className="h-28 rounded-xl" />
      <Skeleton className="h-10 w-full max-w-md" />
      <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
        <Skeleton className="h-64 rounded-xl" />
        <Skeleton className="h-80 rounded-xl" />
      </div>
    </div>
  )
}

export default function Contact360Page() {
  const params = useParams()
  const id = String(params.id)
  const [activeTab, setActiveTab] = useState('overview')

  const { data: contact, isLoading, error } = useContact(id)
  const scoreContact = useScoreContact()
  const setEntityContext = useAIAssistantStore((s) => s.setEntityContext)

  useEffect(() => {
    if (contact) {
      setEntityContext({
        type: 'contact',
        id: contact.id,
        name: `${contact.first_name} ${contact.last_name}`,
        score: contact.lead_score?.score,
      })
    }
  }, [contact, setEntityContext])

  const handleScore = async () => {
    toast.promise(scoreContact.mutateAsync({ contactId: id }), {
      loading: 'Scoring contact...',
      success: 'Score updated',
      error: 'Scoring failed',
    })
  }

  if (isLoading) return <Contact360Skeleton />

  if (error || !contact) {
    return (
      <div className="page-container">
        <Card className="p-8 text-center">
          <p className="text-sm text-muted-foreground">Contact not found</p>
          <Button href="/contacts" variant="secondary" className="mt-4">
            Back to Contacts
          </Button>
        </Card>
      </div>
    )
  }

  const score = contact.lead_score?.score
  const fullName = `${contact.first_name} ${contact.last_name}`
  const openTasks = MOCK_TASKS.filter((t) => !t.done).length
  const tabs = TABS.map((t) => (t.id === 'tasks' ? { ...t, count: openTasks } : t))

  return (
    <Entity360Layout
      backHref="/contacts"
      backLabel="Contacts"
      header={
        <EntityHeader
          type="contact"
          title={fullName}
          subtitle={contact.title}
          score={score}
          meta={[
            ...(contact.email ? [{ icon: Mail, label: contact.email }] : []),
            ...(contact.phone ? [{ icon: Phone, label: contact.phone }] : []),
            ...(contact.company ? [{ icon: Building2, label: contact.company.name }] : []),
          ]}
          actions={
            <div className="flex gap-2">
              <Button size="sm" variant="secondary" onClick={handleScore} loading={scoreContact.isPending}>
                Score
              </Button>
              {contact.email && (
                <Button size="sm" variant="secondary" href={`mailto:${contact.email}`}>
                  <Mail className="h-4 w-4" />
                </Button>
              )}
            </div>
          }
        />
      }
      tabs={tabs}
      activeTab={activeTab}
      onTabChange={setActiveTab}
      sidePanel={
        <AISummaryPanel
          score={score}
          recommendation={scoreToRecommendation(score)}
          summary={`${fullName} is a ${contact.title ?? 'contact'}${contact.company ? ` at ${contact.company.name}` : ''}. Run AI scoring for personalized insights.`}
          recommendations={[
            { action: 'Send personalized outreach', reason: 'High seniority and company fit' },
            { action: 'Invite to product webinar', reason: 'Engagement signals detected' },
          ]}
          tags={contact.tags}
          onScore={handleScore}
          loading={scoreContact.isPending}
        />
      }
    >
      {activeTab === 'overview' && (
        <div className="space-y-6">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base">Contact Details</CardTitle>
            </CardHeader>
            <CardContent>
              <dl className="grid gap-4 sm:grid-cols-2">
                <div>
                  <dt className="text-xs text-muted-foreground">Email</dt>
                  <dd className="mt-0.5 flex items-center gap-1.5 text-sm font-medium text-foreground">
                    {contact.email ? (
                      <>
                        <a href={`mailto:${contact.email}`} className="text-primary hover:underline">
                          {contact.email}
                        </a>
                        <CheckCircle2 className="h-3.5 w-3.5 text-success" />
                      </>
                    ) : (
                      '—'
                    )}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs text-muted-foreground">Phone</dt>
                  <dd className="mt-0.5 text-sm font-medium text-foreground">{contact.phone ?? '—'}</dd>
                </div>
                <div>
                  <dt className="text-xs text-muted-foreground">Title</dt>
                  <dd className="mt-0.5 text-sm font-medium text-foreground">{contact.title ?? '—'}</dd>
                </div>
                <div>
                  <dt className="text-xs text-muted-foreground">Department</dt>
                  <dd className="mt-0.5 text-sm font-medium text-foreground">{contact.department ?? '—'}</dd>
                </div>
                <div>
                  <dt className="text-xs text-muted-foreground">Company</dt>
                  <dd className="mt-0.5 text-sm font-medium text-foreground">
                    {contact.company ? (
                      <Link href={`/companies/${contact.company_id}`} className="text-primary hover:underline">
                        {contact.company.name}
                      </Link>
                    ) : (
                      '—'
                    )}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs text-muted-foreground">Status</dt>
                  <dd className="mt-0.5">
                    <Badge variant="primary">
                      {contact.status.charAt(0).toUpperCase() + contact.status.slice(1)}
                    </Badge>
                  </dd>
                </div>
              </dl>
            </CardContent>
          </Card>

          {contact.linkedin_url && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base">Social</CardTitle>
              </CardHeader>
              <CardContent>
                <a
                  href={contact.linkedin_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-sm text-primary hover:underline"
                >
                  LinkedIn Profile
                  <ArrowUpRight className="h-3.5 w-3.5" />
                </a>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {activeTab === 'activity' && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-base">
              <Activity className="h-4 w-4 text-muted-foreground" />
              Communication Timeline
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-4">
              {MOCK_ACTIVITY.map((item, i) => (
                <li key={i} className="flex gap-3 border-b border-border pb-4 last:border-0 last:pb-0">
                  <div className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-primary" />
                  <div>
                    <p className="text-sm text-foreground">{item.description}</p>
                    <p className="text-xs capitalize text-muted-foreground">
                      {item.type} · {item.date}
                    </p>
                  </div>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {activeTab === 'emails' && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-base">
              <Mail className="h-4 w-4 text-muted-foreground" />
              Email History
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {MOCK_EMAILS.map((email) => (
              <div
                key={email.subject}
                className="flex items-center justify-between rounded-lg border border-border px-4 py-3"
              >
                <div>
                  <p className="text-sm font-medium text-foreground">{email.subject}</p>
                  <p className="text-xs text-muted-foreground">
                    {email.direction} · {email.date}
                  </p>
                </div>
                <Badge variant={emailStatusVariant[email.status]}>{email.status}</Badge>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {activeTab === 'calls' && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-base">
              <Phone className="h-4 w-4 text-muted-foreground" />
              Call Log
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {MOCK_CALLS.map((call) => (
              <div
                key={call.title}
                className="flex items-center justify-between rounded-lg border border-border px-4 py-3"
              >
                <div>
                  <p className="text-sm font-medium text-foreground">{call.title}</p>
                  <p className="text-xs text-muted-foreground">
                    {call.date} · {call.duration}
                  </p>
                </div>
                <Badge variant={call.outcome === 'Positive' ? 'success' : 'gray'}>{call.outcome}</Badge>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {activeTab === 'meetings' && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-base">
              <Video className="h-4 w-4 text-muted-foreground" />
              Meetings
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {MOCK_MEETINGS.map((meeting) => (
              <div
                key={meeting.title}
                className="flex items-center justify-between rounded-lg border border-border px-4 py-3"
              >
                <div>
                  <p className="text-sm font-medium text-foreground">{meeting.title}</p>
                  <p className="flex items-center gap-1 text-xs text-muted-foreground">
                    <Clock className="h-3 w-3" />
                    {meeting.date} at {meeting.time}
                  </p>
                </div>
                <Badge variant={meeting.status === 'scheduled' ? 'primary' : 'warning'}>
                  {meeting.status}
                </Badge>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {activeTab === 'notes' && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-base">
              <StickyNote className="h-4 w-4 text-muted-foreground" />
              Notes
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-4">
              {MOCK_NOTES.map((note, i) => (
                <li key={i} className="rounded-lg bg-muted/50 p-4">
                  <p className="text-sm text-foreground">{note.text}</p>
                  <p className="mt-2 text-xs text-muted-foreground">
                    {note.author} · {note.date}
                  </p>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {activeTab === 'tasks' && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-base">
              <CheckSquare className="h-4 w-4 text-muted-foreground" />
              Tasks
              <Badge variant="secondary" className="ml-1">
                {openTasks} open
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-3">
              {MOCK_TASKS.map((task, i) => (
                <li
                  key={i}
                  className="flex items-center justify-between rounded-lg border border-border px-4 py-3"
                >
                  <div className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      checked={task.done}
                      readOnly
                      className="h-4 w-4 rounded border-border"
                    />
                    <span
                      className={
                        task.done
                          ? 'text-sm text-muted-foreground line-through'
                          : 'text-sm text-foreground'
                      }
                    >
                      {task.title}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant={priorityVariant[task.priority]}>{task.priority}</Badge>
                    <span className="text-xs text-muted-foreground">{task.due}</span>
                  </div>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </Entity360Layout>
  )
}