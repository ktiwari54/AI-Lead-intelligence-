'use client'

import { useState } from 'react'
import { Search, Plug, CheckCircle2, AlertCircle, Clock, Zap, Star, Filter } from 'lucide-react'
import { toast } from 'sonner'
import { PageHeader } from '@/components/enterprise/PageHeader'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'

type ConnectorStatus = 'connected' | 'disconnected' | 'error' | 'pending'
type ConnectorCategory = 'all' | 'data' | 'crm' | 'email' | 'enrichment' | 'export'

interface Connector {
  id: string
  name: string
  description: string
  category: ConnectorCategory
  status: ConnectorStatus
  logo: string
  featured?: boolean
  recordsAdded?: number
  lastSync?: string
  docsUrl?: string
}

const CONNECTORS: Connector[] = [
  { id: 'apollo', name: 'Apollo.io', description: 'B2B contact and company data with 275M+ contacts.', category: 'data', status: 'connected', logo: '🚀', featured: true, recordsAdded: 14200, lastSync: '2026-06-28T08:00:00Z' },
  { id: 'hunter', name: 'Hunter.io', description: 'Email finder and verification for domain-level prospecting.', category: 'enrichment', status: 'connected', logo: '🎯', recordsAdded: 8900, lastSync: '2026-06-28T07:30:00Z' },
  { id: 'clearbit', name: 'Clearbit', description: 'Company and contact enrichment from 100+ data sources.', category: 'enrichment', status: 'error', logo: '🔷', featured: true },
  { id: 'hubspot', name: 'HubSpot CRM', description: 'Sync leads, contacts, and deals with HubSpot.', category: 'crm', status: 'connected', logo: '🧡', featured: true, recordsAdded: 3400, lastSync: '2026-06-28T06:00:00Z' },
  { id: 'salesforce', name: 'Salesforce', description: 'Two-way sync of leads, accounts, opportunities.', category: 'crm', status: 'disconnected', logo: '☁️', featured: true },
  { id: 'pipedrive', name: 'Pipedrive', description: 'Sales CRM with pipeline and deal management sync.', category: 'crm', status: 'disconnected', logo: '🟢' },
  { id: 'outreach', name: 'Outreach', description: 'Sales engagement sequences from AI-scored leads.', category: 'email', status: 'pending', logo: '📧' },
  { id: 'gmail', name: 'Gmail / Google Workspace', description: 'Log emails and sync contacts from Gmail.', category: 'email', status: 'disconnected', logo: '📬' },
  { id: 'outlook', name: 'Microsoft Outlook', description: 'Sync emails and calendar from Microsoft 365.', category: 'email', status: 'disconnected', logo: '💌' },
  { id: 'slack', name: 'Slack', description: 'Get real-time alerts for scored leads and deal updates.', category: 'export', status: 'connected', logo: '💬', recordsAdded: 0, lastSync: '2026-06-28T09:15:00Z' },
  { id: 'webhook', name: 'Custom Webhook', description: 'Push any event to your own HTTP endpoint.', category: 'export', status: 'disconnected', logo: '🔗' },
  { id: 'snowflake', name: 'Snowflake', description: 'Export scored lead data to your data warehouse.', category: 'export', status: 'disconnected', logo: '❄️' },
]

const CATEGORIES: { value: ConnectorCategory; label: string }[] = [
  { value: 'all', label: 'All' },
  { value: 'data', label: 'Data Providers' },
  { value: 'enrichment', label: 'Enrichment' },
  { value: 'crm', label: 'CRM' },
  { value: 'email', label: 'Email & Outreach' },
  { value: 'export', label: 'Export & Sync' },
]

const STATUS_CONFIG: Record<ConnectorStatus, { label: string; icon: typeof CheckCircle2; class: string; badge: 'success' | 'danger' | 'warning' | 'secondary' }> = {
  connected: { label: 'Connected', icon: CheckCircle2, class: 'text-emerald-500', badge: 'success' },
  error: { label: 'Error', icon: AlertCircle, class: 'text-destructive', badge: 'danger' },
  pending: { label: 'Pending', icon: Clock, class: 'text-warning', badge: 'warning' },
  disconnected: { label: 'Not connected', icon: Plug, class: 'text-muted-foreground', badge: 'secondary' },
}

function relativeTime(iso: string) {
  const diff = Date.now() - new Date(iso).getTime()
  const h = Math.floor(diff / 3600000)
  const m = Math.floor(diff / 60000)
  return h > 0 ? `${h}h ago` : `${m}m ago`
}

export default function ConnectorMarketplacePage() {
  const [connectors, setConnectors] = useState(CONNECTORS)
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState<ConnectorCategory>('all')
  const [connecting, setConnecting] = useState<string | null>(null)

  const filtered = connectors.filter(c => {
    const matchCat = category === 'all' || c.category === category
    const matchSearch = !search || c.name.toLowerCase().includes(search.toLowerCase()) || c.description.toLowerCase().includes(search.toLowerCase())
    return matchCat && matchSearch
  })

  const connected = connectors.filter(c => c.status === 'connected').length
  const errors = connectors.filter(c => c.status === 'error').length

  const handleConnect = async (id: string) => {
    setConnecting(id)
    await new Promise(r => setTimeout(r, 1500))
    setConnectors(prev => prev.map(c => c.id === id ? { ...c, status: 'connected' as ConnectorStatus, lastSync: new Date().toISOString(), recordsAdded: Math.floor(Math.random() * 5000) + 100 } : c))
    setConnecting(null)
    toast.success(`${connectors.find(c => c.id === id)?.name} connected successfully`)
  }

  const handleDisconnect = (id: string) => {
    setConnectors(prev => prev.map(c => c.id === id ? { ...c, status: 'disconnected' as ConnectorStatus, lastSync: undefined, recordsAdded: undefined } : c))
    toast.success(`${connectors.find(c => c.id === id)?.name} disconnected`)
  }

  return (
    <div className="page-container space-y-6">
      <PageHeader
        title="Connector Marketplace"
        description="Connect data providers, CRMs, and export destinations to power your lead pipeline."
        badge={`${connected} active`}
      />

      {/* Health bar */}
      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <CardContent className="flex items-center gap-4 p-4">
            <CheckCircle2 className="h-8 w-8 text-emerald-500 shrink-0" />
            <div>
              <p className="text-2xl font-bold text-foreground">{connected}</p>
              <p className="text-xs text-muted-foreground">Active connectors</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center gap-4 p-4">
            <Zap className="h-8 w-8 text-primary shrink-0" />
            <div>
              <p className="text-2xl font-bold text-foreground">
                {connectors.reduce((s, c) => s + (c.recordsAdded ?? 0), 0).toLocaleString()}
              </p>
              <p className="text-xs text-muted-foreground">Records synced total</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center gap-4 p-4">
            <AlertCircle className={`h-8 w-8 shrink-0 ${errors > 0 ? 'text-destructive' : 'text-muted-foreground'}`} />
            <div>
              <p className={`text-2xl font-bold ${errors > 0 ? 'text-destructive' : 'text-foreground'}`}>{errors}</p>
              <p className="text-xs text-muted-foreground">Connectors with errors</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-48 max-w-xs">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            className="input-base pl-9 text-sm"
            placeholder="Search connectors..."
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>
        <div className="flex flex-wrap gap-2">
          {CATEGORIES.map(cat => (
            <button
              key={cat.value}
              onClick={() => setCategory(cat.value)}
              className={`rounded-lg border px-3 py-1.5 text-sm font-medium transition-colors ${
                category === cat.value
                  ? 'border-primary bg-primary text-primary-foreground'
                  : 'border-border bg-card text-muted-foreground hover:border-primary/40'
              }`}
            >
              {cat.label}
            </button>
          ))}
        </div>
      </div>

      {/* Featured */}
      {category === 'all' && !search && (
        <div>
          <div className="mb-3 flex items-center gap-2">
            <Star className="h-4 w-4 text-amber-400" />
            <h2 className="text-sm font-semibold text-foreground">Featured</h2>
          </div>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {connectors.filter(c => c.featured).map(c => <ConnectorCard key={c.id} connector={c} connecting={connecting} onConnect={handleConnect} onDisconnect={handleDisconnect} />)}
          </div>
        </div>
      )}

      {/* All */}
      <div>
        {(category !== 'all' || search) && (
          <p className="mb-3 text-sm text-muted-foreground">{filtered.length} connector{filtered.length !== 1 ? 's' : ''}</p>
        )}
        {category === 'all' && !search && <h2 className="mb-3 text-sm font-semibold text-foreground">All Connectors</h2>}
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map(c => <ConnectorCard key={c.id} connector={c} connecting={connecting} onConnect={handleConnect} onDisconnect={handleDisconnect} />)}
        </div>
      </div>
    </div>
  )
}

function ConnectorCard({
  connector: c,
  connecting,
  onConnect,
  onDisconnect,
}: {
  connector: Connector
  connecting: string | null
  onConnect: (id: string) => void
  onDisconnect: (id: string) => void
}) {
  const status = STATUS_CONFIG[c.status]
  const StatusIcon = status.icon
  const isConnecting = connecting === c.id

  return (
    <Card className="h-full transition-colors hover:border-primary/30">
      <CardContent className="flex h-full flex-col p-5 gap-4">
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl border border-border bg-muted text-2xl">
              {c.logo}
            </div>
            <div>
              <p className="font-semibold text-foreground leading-snug">{c.name}</p>
              <Badge variant={status.badge} className="mt-0.5 text-[10px]">{status.label}</Badge>
            </div>
          </div>
        </div>

        <p className="text-sm text-muted-foreground flex-1">{c.description}</p>

        {c.status === 'connected' && (
          <div className="rounded-lg bg-muted/50 p-3 text-xs text-muted-foreground space-y-1">
            {c.recordsAdded != null && (
              <div className="flex justify-between">
                <span>Records synced</span>
                <span className="font-medium text-foreground">{c.recordsAdded.toLocaleString()}</span>
              </div>
            )}
            {c.lastSync && (
              <div className="flex justify-between">
                <span>Last sync</span>
                <span className="font-medium text-foreground">{relativeTime(c.lastSync)}</span>
              </div>
            )}
          </div>
        )}

        {c.status === 'error' && (
          <div className="rounded-lg border border-destructive/20 bg-destructive/5 p-3 text-xs text-destructive">
            Authentication failed. Reconnect to restore sync.
          </div>
        )}

        <div className="flex gap-2">
          {c.status === 'connected' || c.status === 'error' ? (
            <>
              <Button variant="outline" size="sm" className="flex-1" onClick={() => onDisconnect(c.id)}>
                Disconnect
              </Button>
              {c.status === 'error' && (
                <Button size="sm" className="flex-1" onClick={() => onConnect(c.id)} disabled={isConnecting}>
                  {isConnecting ? 'Reconnecting...' : 'Reconnect'}
                </Button>
              )}
            </>
          ) : (
            <Button size="sm" className="flex-1" onClick={() => onConnect(c.id)} disabled={isConnecting || c.status === 'pending'}>
              {isConnecting ? 'Connecting...' : c.status === 'pending' ? 'Pending approval' : 'Connect'}
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
