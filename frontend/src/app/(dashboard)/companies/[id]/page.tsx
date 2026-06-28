'use client'

import { useState, useEffect } from 'react'
import { useAIAssistantStore } from '@/stores/ai-assistant-store'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import { Users, Cpu, Clock, ExternalLink, MapPin, TrendingUp } from 'lucide-react'
import { toast } from 'sonner'
import { useCompany } from '@/hooks/useCompanies'
import { useContacts } from '@/hooks/useContacts'
import { useScoreCompany } from '@/hooks/useAI'
import { Entity360Layout } from '@/components/entity/Entity360Layout'
import { EntityHeader, Globe as GlobeIcon, MapPin as MapPinIcon } from '@/components/entity/EntityHeader'
import { AISummaryPanel } from '@/components/entity/AISummaryPanel'
import Badge from '@/components/ui/Badge'
import Button from '@/components/ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

const TABS = [
  { id: 'overview', label: 'Overview' },
  { id: 'contacts', label: 'Contacts' },
  { id: 'tech', label: 'Technologies' },
  { id: 'locations', label: 'Locations' },
  { id: 'growth', label: 'Growth' },
  { id: 'timeline', label: 'Timeline' },
]

const MOCK_TECH = ['React', 'AWS', 'PostgreSQL', 'Docker', 'Kubernetes']
const MOCK_LOCATIONS = [
  { city: 'San Francisco', country: 'United States', type: 'HQ', employees: 120 },
  { city: 'Austin', country: 'United States', type: 'Office', employees: 45 },
  { city: 'London', country: 'United Kingdom', type: 'Office', employees: 28 },
]
const MOCK_GROWTH = [
  { period: 'Q1 2026', headcount: '+12%', revenue: '+8%' },
  { period: 'Q4 2025', headcount: '+9%', revenue: '+15%' },
  { period: 'Q3 2025', headcount: '+6%', revenue: '+11%' },
]
const MOCK_TIMELINE = [
  { date: '2026-06-15', event: 'Lead score updated to 82', type: 'score' },
  { date: '2026-06-10', event: 'Added to Enterprise pipeline', type: 'crm' },
  { date: '2026-06-01', event: 'Company enriched from LinkedIn', type: 'enrichment' },
  { date: '2026-05-20', event: 'Record created', type: 'system' },
]

function scoreToRecommendation(score?: number): 'pursue' | 'nurture' | 'deprioritize' {
  if (score == null) return 'nurture'
  if (score >= 75) return 'pursue'
  if (score >= 50) return 'nurture'
  return 'deprioritize'
}

export default function Company360Page() {
  const params = useParams()
  const id = String(params.id)
  const [activeTab, setActiveTab] = useState('overview')

  const { data: company, isLoading, error } = useCompany(id)
  const { data: contactsData } = useContacts({ company_id: id, per_page: 50 })
  const scoreCompany = useScoreCompany()
  const setEntityContext = useAIAssistantStore((s) => s.setEntityContext)

  useEffect(() => {
    if (company) {
      setEntityContext({
        type: 'company',
        id: company.id,
        name: company.name,
        score: company.lead_score?.score,
      })
    }
  }, [company, setEntityContext])

  const handleScore = async () => {
    toast.promise(scoreCompany.mutateAsync({ companyId: id }), {
      loading: 'Scoring company...',
      success: 'Score updated',
      error: 'Scoring failed',
    })
  }

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="h-4 w-32 animate-pulse rounded bg-muted" />
        <div className="h-28 animate-pulse rounded-xl bg-muted" />
        <div className="h-64 animate-pulse rounded-xl bg-muted" />
      </div>
    )
  }

  if (error || !company) {
    return (
      <div className="rounded-xl border border-border bg-card p-8 text-center">
        <p className="text-sm text-muted-foreground">Company not found</p>
        <Button href="/companies" variant="secondary" className="mt-4">
          Back to Companies
        </Button>
      </div>
    )
  }

  const score = company.lead_score?.score
  const location = [company.city, company.country].filter(Boolean).join(', ')
  const tabs = TABS.map((t) =>
    t.id === 'contacts' ? { ...t, count: contactsData?.total } : t
  )

  return (
    <Entity360Layout
      backHref="/companies"
      backLabel="Companies"
      header={
        <EntityHeader
          type="company"
          title={company.name}
          subtitle={company.domain}
          score={score}
          meta={[
            ...(company.industry ? [{ icon: GlobeIcon, label: company.industry }] : []),
            ...(location ? [{ icon: MapPinIcon, label: location }] : []),
          ]}
          actions={
            <div className="flex gap-2">
              <Button size="sm" variant="secondary" onClick={handleScore} loading={scoreCompany.isPending}>
                Score
              </Button>
              {company.website && (
                <a href={company.website} target="_blank" rel="noopener noreferrer">
                  <Button size="sm" variant="secondary">
                    <ExternalLink className="h-4 w-4" />
                  </Button>
                </a>
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
          summary={company.description ?? company.lead_score?.reasoning}
          recommendations={[
            { action: 'Contact VP Engineering', reason: 'High fit for enterprise SaaS' },
            { action: 'Review tech stack overlap', reason: 'Uses AWS and React' },
          ]}
          crmStatus="Synced to CRM 2 hours ago"
          tags={company.tags}
          onScore={handleScore}
          loading={scoreCompany.isPending}
        />
      }
    >
      {activeTab === 'overview' && (
        <div className="space-y-6">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base">Description</CardTitle>
            </CardHeader>
            <CardContent>
            <p className="text-sm text-muted-foreground leading-relaxed">
              {company.description ?? 'No description available. Run enrichment to populate firmographic data.'}
            </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base">Firmographics</CardTitle>
            </CardHeader>
            <CardContent>
            <dl className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              <div>
                <dt className="text-xs text-muted-foreground">Employees</dt>
                <dd className="mt-0.5 text-sm font-medium text-foreground">
                  {company.employee_count?.toLocaleString() ?? '—'}
                </dd>
              </div>
              <div>
                <dt className="text-xs text-muted-foreground">Annual Revenue</dt>
                <dd className="mt-0.5 text-sm font-medium text-foreground">
                  {company.annual_revenue != null
                    ? `$${(company.annual_revenue / 1_000_000).toFixed(1)}M`
                    : '—'}
                </dd>
              </div>
              <div>
                <dt className="text-xs text-muted-foreground">Founded</dt>
                <dd className="mt-0.5 text-sm font-medium text-foreground">
                  {company.founded_year ?? '—'}
                </dd>
              </div>
              <div>
                <dt className="text-xs text-muted-foreground">Industry</dt>
                <dd className="mt-0.5 text-sm font-medium text-foreground">
                  {company.industry ?? '—'}
                </dd>
              </div>
              <div>
                <dt className="text-xs text-muted-foreground">Status</dt>
                <dd className="mt-0.5">
                  <Badge variant="primary">
                    {company.status.charAt(0).toUpperCase() + company.status.slice(1)}
                  </Badge>
                </dd>
              </div>
              <div>
                <dt className="text-xs text-muted-foreground">Phone</dt>
                <dd className="mt-0.5 text-sm font-medium text-foreground">
                  {company.phone ?? '—'}
                </dd>
              </div>
            </dl>
            </CardContent>
          </Card>

          {(company.linkedin_url || company.website) && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base">Social Links</CardTitle>
              </CardHeader>
              <CardContent>
              <div className="flex gap-3">
                {company.linkedin_url && (
                  <a
                    href={company.linkedin_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-primary hover:underline"
                  >
                    LinkedIn
                  </a>
                )}
                {company.website && (
                  <a
                    href={company.website}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-primary hover:underline"
                  >
                    Website
                  </a>
                )}
              </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {activeTab === 'contacts' && (
        <Card className="overflow-hidden">
          <div className="flex items-center gap-2 border-b border-border px-4 py-3">
            <Users className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm font-medium text-foreground">
              {contactsData?.total ?? 0} contacts at {company.name}
            </span>
          </div>
          {contactsData?.items.length === 0 ? (
            <p className="px-4 py-8 text-center text-sm text-muted-foreground">
              No contacts linked to this company
            </p>
          ) : (
            <table className="w-full">
              <thead className="bg-muted/50">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Name</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Title</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Email</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Score</th>
                </tr>
              </thead>
              <tbody>
                {contactsData?.items.map((contact) => (
                  <tr key={contact.id} className="border-t border-border hover:bg-muted/30">
                    <td className="px-4 py-2.5">
                      <Link href={`/contacts/${contact.id}`} className="text-sm font-medium text-foreground hover:text-primary">
                        {contact.first_name} {contact.last_name}
                      </Link>
                    </td>
                    <td className="px-4 py-2.5 text-sm text-muted-foreground">{contact.title ?? '—'}</td>
                    <td className="px-4 py-2.5 text-sm text-muted-foreground">{contact.email ?? '—'}</td>
                    <td className="px-4 py-2.5 text-sm text-foreground">
                      {contact.lead_score?.score ?? '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Card>
      )}

      {activeTab === 'tech' && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-base">
              <Cpu className="h-4 w-4 text-muted-foreground" />
              Technology Stack
            </CardTitle>
          </CardHeader>
          <CardContent>
          <div className="flex flex-wrap gap-2">
            {MOCK_TECH.map((tech) => (
              <Badge key={tech} variant="gray">{tech}</Badge>
            ))}
          </div>
          <p className="mt-4 text-xs text-muted-foreground">
            Tech stack data will be populated via enrichment integrations.
          </p>
          </CardContent>
        </Card>
      )}

      {activeTab === 'locations' && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-base">
              <MapPin className="h-4 w-4 text-muted-foreground" />
              Office Locations
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {MOCK_LOCATIONS.map((loc) => (
              <div key={loc.city} className="flex items-center justify-between rounded-lg border border-border px-4 py-3">
                <div>
                  <p className="text-sm font-medium text-foreground">{loc.city}, {loc.country}</p>
                  <p className="text-xs text-muted-foreground">{loc.type}</p>
                </div>
                <Badge variant="secondary">{loc.employees} employees</Badge>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {activeTab === 'growth' && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-base">
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
              Growth Metrics
            </CardTitle>
          </CardHeader>
          <CardContent>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left text-xs text-muted-foreground">
                  <th className="pb-2 font-medium">Period</th>
                  <th className="pb-2 font-medium">Headcount</th>
                  <th className="pb-2 font-medium">Revenue</th>
                </tr>
              </thead>
              <tbody>
                {MOCK_GROWTH.map((row) => (
                  <tr key={row.period} className="border-b border-border last:border-0">
                    <td className="py-3 text-foreground">{row.period}</td>
                    <td className="py-3 text-success">{row.headcount}</td>
                    <td className="py-3 text-success">{row.revenue}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>
      )}

      {activeTab === 'timeline' && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-base">
              <Clock className="h-4 w-4 text-muted-foreground" />
              Activity Timeline
            </CardTitle>
          </CardHeader>
          <CardContent>
          <ul className="space-y-4">
            {MOCK_TIMELINE.map((item, i) => (
              <li key={i} className="flex gap-3">
                <div className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-primary" />
                <div>
                  <p className="text-sm text-foreground">{item.event}</p>
                  <p className="text-xs text-muted-foreground">{item.date}</p>
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