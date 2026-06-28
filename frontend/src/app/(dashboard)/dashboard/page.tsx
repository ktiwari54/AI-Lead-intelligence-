'use client'

import Link from 'next/link'
import {
  Building2,
  Users,
  Sparkles,
  CreditCard,
  Search,
  Upload,
  Download,
  RotateCcw,
  ArrowRight,
  Brain,
} from 'lucide-react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
} from 'recharts'
import { useCurrentUser } from '@/hooks/useAuth'
import { useDashboardStats, useLeadVelocity, useCRMFunnel } from '@/hooks/useAnalytics'
import { DashboardGrid } from '@/components/dashboard/DashboardGrid'
import { CountryMapWidget } from '@/components/dashboard/CountryMapWidget'
import { useDashboardStore } from '@/stores/dashboard-store'
import { PageHeader } from '@/components/enterprise/PageHeader'
import { MetricCard } from '@/components/enterprise/MetricCard'

import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'

const recentActivity = [
  { action: 'Discovery completed', target: 'SaaS companies in Austin', time: '2m ago', type: 'search' },
  { action: 'AI score generated', target: 'CloudForge Analytics', time: '15m ago', type: 'ai' },
  { action: 'Contact enriched', target: 'Jordan Reeves', time: '1h ago', type: 'contact' },
  { action: 'Export finished', target: '250 companies', time: '3h ago', type: 'export' },
]

export default function DashboardPage() {
  const { data: user } = useCurrentUser()
  const stats = useDashboardStats()
  const velocity = useLeadVelocity(30)
  const funnel = useCRMFunnel()
  const resetLayout = useDashboardStore((s) => s.resetLayout)

  const velocityData = velocity.data?.companies.map((c, i) => ({
    date: c.date.slice(5),
    companies: c.value,
    contacts: velocity.data?.contacts[i]?.value ?? 0,
  })) ?? []

  const widgets = {
    kpis: (
      <div className="grid h-full grid-cols-2 gap-3 lg:grid-cols-4">
        <MetricCard embedded title="Companies" value={stats.data?.total_companies ?? '—'} icon={Building2} loading={stats.isLoading} trend={{ value: 12, label: 'vs last month' }} />
        <MetricCard embedded title="Contacts" value={stats.data?.total_contacts ?? '—'} icon={Users} loading={stats.isLoading} trend={{ value: 8, label: 'vs last month' }} />
        <MetricCard embedded title="AI Scores" value={stats.data?.ai_scores_generated ?? '—'} icon={Sparkles} loading={stats.isLoading} />
        <MetricCard embedded title="Credits" value={stats.data?.credits_remaining ?? user?.organization?.credits ?? '—'} icon={CreditCard} loading={stats.isLoading} subtitle="Remaining balance" />
      </div>
    ),
    velocity: (
      <div className="flex h-full min-h-[200px] flex-col">
        <p className="mb-3 text-xs text-muted-foreground">30-day company & contact growth</p>
        {velocity.isLoading ? (
          <div className="flex-1 animate-pulse rounded-lg bg-muted" />
        ) : (
          <ResponsiveContainer width="100%" height="100%" minHeight={180}>
            <LineChart data={velocityData}>
              <XAxis dataKey="date" tick={{ fontSize: 11 }} stroke="rgb(var(--muted-foreground))" />
              <YAxis tick={{ fontSize: 11 }} width={32} stroke="rgb(var(--muted-foreground))" />
              <Tooltip contentStyle={{ borderRadius: 8, border: '1px solid rgb(var(--border))', background: 'rgb(var(--card))' }} />
              <Line type="monotone" dataKey="companies" stroke="rgb(var(--primary))" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="contacts" stroke="rgb(var(--success))" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    ),
    'quick-actions': (
      <div className="space-y-2">
          {[
            { href: '/search', icon: Search, label: 'Lead Discovery', sub: 'AI-powered search', badge: 'AI' },
            { href: '/ai', icon: Brain, label: 'AI Assistant', sub: 'Chat & recommendations' },
            { href: '/imports', icon: Upload, label: 'Import Data', sub: 'Upload CSV' },
            { href: '/exports', icon: Download, label: 'Export Data', sub: 'Download leads' },
          ].map((a) => (
            <Link
              key={a.href + a.label}
              href={a.href}
              className="group flex items-center gap-3 rounded-xl border border-border p-3 transition-all hover:border-primary/30 hover:bg-accent/50"
            >
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 transition-colors group-hover:bg-primary/15">
                <a.icon className="h-4 w-4 text-primary" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <p className="text-sm font-semibold text-foreground">{a.label}</p>
                  {a.badge && <Badge variant="secondary" className="h-5 text-[10px]">{a.badge}</Badge>}
                </div>
                <p className="text-xs text-muted-foreground">{a.sub}</p>
              </div>
              <ArrowRight className="h-4 w-4 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100" />
            </Link>
          ))}
      </div>
    ),
    activity: (
      <ul className="space-y-3">
        {recentActivity.map((item, i) => (
          <li key={i} className="flex items-start justify-between gap-3 rounded-lg border border-border/60 bg-muted/20 px-3 py-2.5">
            <div>
              <p className="text-xs text-muted-foreground">{item.action}</p>
              <p className="text-sm font-medium text-foreground">{item.target}</p>
            </div>
            <span className="shrink-0 text-xs text-muted-foreground">{item.time}</span>
          </li>
        ))}
      </ul>
    ),
    'country-map': (
      <CountryMapWidget />
    ),
    pipeline: (
      <div className="flex h-full min-h-[200px] flex-col">
        {funnel.data && (
          <p className="mb-3 text-xs text-muted-foreground">
            {funnel.data.total_deals} deals · ${funnel.data.total_value?.toLocaleString()}
          </p>
        )}
        {funnel.isLoading ? (
          <div className="flex-1 animate-pulse rounded-lg bg-muted" />
        ) : funnel.data ? (
          <ResponsiveContainer width="100%" height="100%" minHeight={180}>
            <BarChart data={funnel.data.stages} layout="vertical">
              <XAxis type="number" tick={{ fontSize: 10 }} />
              <YAxis type="category" dataKey="label" tick={{ fontSize: 10 }} width={72} />
              <Tooltip contentStyle={{ borderRadius: 8, border: '1px solid rgb(var(--border))', background: 'rgb(var(--card))' }} />
              <Bar dataKey="value" fill="rgb(var(--primary))" radius={[0, 6, 6, 0]} />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <p className="text-sm text-muted-foreground">No pipeline data yet</p>
        )}
      </div>
    ),
  }

  return (
    <div className="page-container">
      <PageHeader
        title={`Good ${new Date().getHours() < 12 ? 'morning' : 'afternoon'}, ${user?.full_name?.split(' ')[0] ?? 'there'}`}
        description="Your command center for lead discovery, intelligence, and pipeline health."
        badge="Enterprise v3"
        actions={
          <Button variant="outline" size="sm" onClick={resetLayout}>
            <RotateCcw className="mr-2 h-4 w-4" />
            Reset layout
          </Button>
        }
      />
      <DashboardGrid children={widgets} />
    </div>
  )
}