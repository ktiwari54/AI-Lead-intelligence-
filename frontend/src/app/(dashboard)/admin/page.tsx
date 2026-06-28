'use client'

import { useState } from 'react'
import {
  useAdminStats,
  useAuditLogs,
  useFeatureFlags,
  useUpdateFeatureFlag,
  useSystemSettings,
  useUpdateSystemSetting,
} from '@/hooks/useAdmin'
import Badge from '@/components/ui/Badge'
import { PageHeader } from '@/components/enterprise/PageHeader'
import { MetricCard } from '@/components/enterprise/MetricCard'
import { Card, CardContent } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Building2, Users, Search, Download } from 'lucide-react'
import { cn } from '@/lib/utils'

const TABS = ['Overview', 'Audit Logs', 'Feature Flags', 'Settings', 'System Health'] as const

export default function AdminPage() {
  const [tab, setTab] = useState<(typeof TABS)[number]>('Overview')
  const stats = useAdminStats()
  const auditLogs = useAuditLogs()
  const flags = useFeatureFlags()
  const settings = useSystemSettings()
  const updateFlag = useUpdateFeatureFlag()
  const updateSetting = useUpdateSystemSetting()

  return (
    <div className="page-container space-y-6">
      <PageHeader
        title="Administration"
        description="System configuration, audit logs, feature flags, and platform health."
        badge="Admin"
      />

      <Tabs value={tab} onValueChange={(v) => setTab(v as (typeof TABS)[number])}>
        <TabsList className="w-full justify-start overflow-x-auto">
          {TABS.map((t) => (
            <TabsTrigger key={t} value={t} className="shrink-0">
              {t}
            </TabsTrigger>
          ))}
        </TabsList>

        <TabsContent value="Overview">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <MetricCard title="Organizations" value={stats.data?.total_organizations ?? '—'} icon={Building2} loading={stats.isLoading} />
          <MetricCard title="Users" value={stats.data?.total_users ?? '—'} icon={Users} loading={stats.isLoading} />
          <MetricCard title="Companies" value={stats.data?.total_companies ?? '—'} icon={Building2} loading={stats.isLoading} />
          <MetricCard title="Contacts" value={stats.data?.total_contacts ?? '—'} icon={Users} loading={stats.isLoading} />
          <MetricCard title="Searches Today" value={stats.data?.total_searches_today ?? '—'} icon={Search} loading={stats.isLoading} />
          <MetricCard title="Pending Exports" value={stats.data?.total_exports_pending ?? '—'} icon={Download} loading={stats.isLoading} />
        </div>
        </TabsContent>

        <TabsContent value="Audit Logs">
        <Card className="overflow-hidden">
          <CardContent className="p-0">
          {auditLogs.isLoading ? (
            <div className="h-48 animate-pulse bg-muted" />
          ) : auditLogs.data?.items.length === 0 ? (
            <p className="p-8 text-center text-sm text-muted-foreground">No audit logs</p>
          ) : (
            <table className="w-full text-sm">
              <thead className="bg-muted/50">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Action</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Resource</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">IP</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Time</th>
                </tr>
              </thead>
              <tbody>
                {auditLogs.data?.items.map((log) => (
                  <tr key={log.id} className="border-t border-border">
                    <td className="px-4 py-2.5 font-medium text-foreground">{log.action}</td>
                    <td className="px-4 py-2.5 text-muted-foreground">
                      {log.resource_type}{log.resource_id ? ` #${log.resource_id.slice(0, 8)}` : ''}
                    </td>
                    <td className="px-4 py-2.5 text-muted-foreground">{log.ip_address ?? '—'}</td>
                    <td className="px-4 py-2.5 text-muted-foreground">
                      {new Date(log.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          </CardContent>
        </Card>
        </TabsContent>

        <TabsContent value="Feature Flags">
        <div className="space-y-3">
          {flags.isLoading ? (
            <div className="h-32 animate-pulse rounded-xl bg-muted" />
          ) : flags.data?.length === 0 ? (
            <p className="text-sm text-muted-foreground">No feature flags configured</p>
          ) : (
            flags.data?.map((flag) => (
              <div key={flag.id} className="flex items-center justify-between rounded-xl border border-border bg-card p-4">
                <div>
                  <p className="font-medium text-foreground">{flag.name}</p>
                  <p className="text-xs text-muted-foreground">{flag.key}</p>
                  {flag.description && (
                    <p className="text-sm text-muted-foreground mt-1">{flag.description}</p>
                  )}
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-xs text-muted-foreground">{flag.rollout_percentage}% rollout</span>
                  <button
                    type="button"
                    onClick={() => updateFlag.mutate({ key: flag.key, is_enabled: !flag.is_enabled })}
                    className={cn(
                      'relative h-6 w-11 rounded-full transition-colors',
                      flag.is_enabled ? 'bg-primary' : 'bg-muted'
                    )}
                  >
                    <span className={cn(
                      'absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform',
                      flag.is_enabled ? 'translate-x-5' : 'translate-x-0.5'
                    )} />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
        </TabsContent>

        <TabsContent value="Settings">
        <div className="space-y-3">
          {settings.isLoading ? (
            <div className="h-32 animate-pulse rounded-xl bg-muted" />
          ) : settings.data?.length === 0 ? (
            <p className="text-sm text-muted-foreground">No system settings</p>
          ) : (
            settings.data?.map((s) => (
              <div key={s.id} className="rounded-xl border border-border bg-card p-4">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="font-medium text-foreground">{s.key}</p>
                    {s.description && <p className="text-xs text-muted-foreground mt-0.5">{s.description}</p>}
                  </div>
                  {s.is_editable ? (
                    <input
                      defaultValue={String(s.value ?? '')}
                      onBlur={(e) => updateSetting.mutate({ key: s.key, value: e.target.value })}
                      className="input-base text-sm w-48"
                    />
                  ) : (
                    <Badge variant="secondary">Read-only</Badge>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
        </TabsContent>

        <TabsContent value="System Health">
        <div className="grid gap-4 sm:grid-cols-2">
          {[
            { service: 'API Server', status: 'Healthy', latency: '12ms' },
            { service: 'Database', status: 'Healthy', latency: '3ms' },
            { service: 'Redis Cache', status: 'Healthy', latency: '1ms' },
            { service: 'OpenSearch', status: 'Degraded', latency: '—' },
            { service: 'Celery Workers', status: 'Healthy', latency: '—' },
            { service: 'AI Scoring', status: 'Healthy', latency: '450ms' },
          ].map((s) => (
            <div key={s.service} className="rounded-xl border border-border bg-card p-4 flex items-center justify-between">
              <div>
                <p className="font-medium text-foreground">{s.service}</p>
                <p className="text-xs text-muted-foreground">{s.latency}</p>
              </div>
              <Badge variant={s.status === 'Healthy' ? 'success' : 'warning'}>{s.status}</Badge>
            </div>
          ))}
        </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}