'use client'

import { useState } from 'react'
import { Code2, Key, BookOpen, Terminal, Zap, Globe, Copy, Check, ExternalLink, ChevronRight, Webhook } from 'lucide-react'
import { toast } from 'sonner'
import { PageHeader } from '@/components/enterprise/PageHeader'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/Badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

const BASE_URL = 'https://api.aileadintel.com/v1'

const ENDPOINTS = [
  {
    group: 'Companies',
    color: 'text-blue-500',
    routes: [
      { method: 'GET', path: '/companies', desc: 'List companies with filters and pagination' },
      { method: 'GET', path: '/companies/:id', desc: 'Get company by ID with full profile' },
      { method: 'POST', path: '/companies', desc: 'Create a new company record' },
      { method: 'PATCH', path: '/companies/:id', desc: 'Update company fields' },
      { method: 'DELETE', path: '/companies/:id', desc: 'Delete a company record' },
    ],
  },
  {
    group: 'Contacts',
    color: 'text-emerald-500',
    routes: [
      { method: 'GET', path: '/contacts', desc: 'List contacts with filters' },
      { method: 'GET', path: '/contacts/:id', desc: 'Get contact by ID' },
      { method: 'POST', path: '/contacts', desc: 'Create a new contact' },
      { method: 'PATCH', path: '/contacts/:id', desc: 'Update contact fields' },
      { method: 'DELETE', path: '/contacts/:id', desc: 'Delete a contact' },
    ],
  },
  {
    group: 'AI & Scoring',
    color: 'text-violet-500',
    routes: [
      { method: 'POST', path: '/ai/score/company', desc: 'Generate lead score for a company' },
      { method: 'POST', path: '/ai/score/contact', desc: 'Generate lead score for a contact' },
      { method: 'POST', path: '/ai/chat', desc: 'Send message to AI assistant' },
      { method: 'GET', path: '/ai/recommendations', desc: 'Get AI-ranked lead recommendations' },
    ],
  },
  {
    group: 'Discovery',
    color: 'text-orange-500',
    routes: [
      { method: 'POST', path: '/discovery/search', desc: 'Run a natural language lead discovery' },
      { method: 'GET', path: '/discovery/searches', desc: 'List saved searches' },
      { method: 'POST', path: '/discovery/searches', desc: 'Save a search query' },
    ],
  },
  {
    group: 'Exports',
    color: 'text-pink-500',
    routes: [
      { method: 'POST', path: '/exports', desc: 'Create an export job (CSV, XLSX, JSON)' },
      { method: 'GET', path: '/exports/:id', desc: 'Get export job status and download URL' },
      { method: 'GET', path: '/exports', desc: 'List all export jobs' },
    ],
  },
]

const METHOD_COLORS: Record<string, string> = {
  GET: 'bg-blue-500/10 text-blue-600',
  POST: 'bg-emerald-500/10 text-emerald-600',
  PATCH: 'bg-amber-500/10 text-amber-600',
  DELETE: 'bg-red-500/10 text-red-600',
  PUT: 'bg-violet-500/10 text-violet-600',
}

const CODE_EXAMPLES = {
  curl: `curl -X GET "${BASE_URL}/companies" \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -G --data-urlencode "search=SaaS" \\
  --data-urlencode "page=1" \\
  --data-urlencode "page_size=25"`,
  python: `import requests

client = requests.Session()
client.headers.update({
    "Authorization": "Bearer YOUR_API_KEY",
    "Content-Type": "application/json",
})

response = client.get(
    "${BASE_URL}/companies",
    params={"search": "SaaS", "page": 1, "page_size": 25}
)
companies = response.json()`,
  typescript: `import axios from 'axios'

const client = axios.create({
  baseURL: '${BASE_URL}',
  headers: { Authorization: \`Bearer \${process.env.API_KEY}\` },
})

const { data } = await client.get('/companies', {
  params: { search: 'SaaS', page: 1, page_size: 25 },
})`,
  node: `const fetch = require('node-fetch')

const res = await fetch('${BASE_URL}/companies?search=SaaS', {
  headers: {
    Authorization: \`Bearer \${process.env.API_KEY}\`,
    'Content-Type': 'application/json',
  },
})
const { data } = await res.json()`,
}

const WEBHOOKS = [
  { event: 'company.created', desc: 'Fired when a new company is added' },
  { event: 'company.scored', desc: 'Fired when a company receives an AI score' },
  { event: 'contact.created', desc: 'Fired when a new contact is added' },
  { event: 'contact.scored', desc: 'Fired when a contact receives an AI score' },
  { event: 'export.completed', desc: 'Fired when an export job finishes' },
  { event: 'search.completed', desc: 'Fired when a discovery pipeline completes' },
]

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false)
  const copy = () => {
    navigator.clipboard.writeText(text)
    setCopied(true)
    toast.success('Copied to clipboard')
    setTimeout(() => setCopied(false), 2000)
  }
  return (
    <button onClick={copy} className="rounded-lg p-1.5 text-muted-foreground hover:bg-white/10 hover:text-white transition-colors">
      {copied ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
    </button>
  )
}

export default function DeveloperPortalPage() {
  const [codeTab, setCodeTab] = useState<'curl' | 'python' | 'typescript' | 'node'>('curl')

  return (
    <div className="page-container max-w-6xl space-y-8">
      <PageHeader
        title="Developer Portal"
        description="REST API reference, SDKs, webhooks, and code examples for integrating AI Lead Intelligence."
        badge="API v1"
      />

      {/* Quick links */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[
          { icon: BookOpen, label: 'API Reference', sub: 'Full endpoint docs', href: '#reference' },
          { icon: Key, label: 'API Keys', sub: 'Manage credentials', href: '/settings' },
          { icon: Webhook, label: 'Webhooks', sub: 'Event subscriptions', href: '#webhooks' },
          { icon: Terminal, label: 'Code Examples', sub: 'SDKs & snippets', href: '#examples' },
        ].map(({ icon: Icon, label, sub, href }) => (
          <a key={label} href={href} className="group block">
            <Card className="h-full transition-colors hover:border-primary/40">
              <CardContent className="flex items-center gap-4 p-5">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary/10 transition-colors group-hover:bg-primary/20">
                  <Icon className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <p className="font-semibold text-foreground">{label}</p>
                  <p className="text-xs text-muted-foreground">{sub}</p>
                </div>
                <ChevronRight className="ml-auto h-4 w-4 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100" />
              </CardContent>
            </Card>
          </a>
        ))}
      </div>

      {/* Base URL + Auth */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Globe className="h-4 w-4 text-muted-foreground" />
            Base URL & Authentication
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-3 rounded-xl bg-slate-950 px-4 py-3">
            <code className="flex-1 font-mono text-sm text-emerald-400">{BASE_URL}</code>
            <CopyButton text={BASE_URL} />
          </div>
          <p className="text-sm text-muted-foreground">
            All API requests must include an <code className="rounded bg-muted px-1.5 py-0.5 text-xs font-mono">Authorization: Bearer YOUR_API_KEY</code> header.
            Generate API keys in <a href="/settings" className="text-primary hover:underline">Settings → API Keys</a>.
          </p>
          <div className="rounded-xl border border-border bg-muted/30 p-4 text-sm">
            <p className="font-semibold text-foreground mb-2">Rate Limits</p>
            <div className="grid grid-cols-3 gap-4 text-xs text-muted-foreground">
              <div><p className="font-medium text-foreground">Free</p><p>100 req/min</p></div>
              <div><p className="font-medium text-foreground">Professional</p><p>1,000 req/min</p></div>
              <div><p className="font-medium text-foreground">Enterprise</p><p>Unlimited</p></div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Code Examples */}
      <Card id="examples">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Terminal className="h-4 w-4 text-muted-foreground" />
            Code Examples
          </CardTitle>
          <CardDescription>Listing companies across different languages</CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs value={codeTab} onValueChange={v => setCodeTab(v as typeof codeTab)}>
            <TabsList>
              <TabsTrigger value="curl">cURL</TabsTrigger>
              <TabsTrigger value="python">Python</TabsTrigger>
              <TabsTrigger value="typescript">TypeScript</TabsTrigger>
              <TabsTrigger value="node">Node.js</TabsTrigger>
            </TabsList>
            {(['curl', 'python', 'typescript', 'node'] as const).map(lang => (
              <TabsContent key={lang} value={lang}>
                <div className="relative rounded-xl bg-slate-950 overflow-hidden">
                  <div className="flex items-center justify-between border-b border-white/10 px-4 py-2">
                    <span className="text-xs text-slate-400">{lang}</span>
                    <CopyButton text={CODE_EXAMPLES[lang]} />
                  </div>
                  <pre className="overflow-x-auto p-4 text-sm text-slate-200 leading-relaxed">
                    <code>{CODE_EXAMPLES[lang]}</code>
                  </pre>
                </div>
              </TabsContent>
            ))}
          </Tabs>
        </CardContent>
      </Card>

      {/* API Reference */}
      <div id="reference" className="space-y-4">
        <h2 className="text-base font-semibold text-foreground">API Reference</h2>
        {ENDPOINTS.map(group => (
          <Card key={group.group}>
            <CardHeader className="pb-3">
              <CardTitle className={`text-sm font-semibold ${group.color}`}>{group.group}</CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <div className="divide-y divide-border">
                {group.routes.map(route => (
                  <div key={route.path} className="flex items-center gap-4 px-6 py-3 hover:bg-muted/30 transition-colors">
                    <span className={`shrink-0 rounded-md px-2 py-0.5 text-xs font-bold font-mono ${METHOD_COLORS[route.method] ?? 'bg-muted text-foreground'}`}>
                      {route.method}
                    </span>
                    <code className="flex-1 font-mono text-sm text-foreground">{BASE_URL}{route.path}</code>
                    <span className="text-sm text-muted-foreground hidden md:block">{route.desc}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Webhooks */}
      <Card id="webhooks">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Zap className="h-4 w-4 text-muted-foreground" />
            Webhooks
          </CardTitle>
          <CardDescription>Subscribe to platform events for real-time integrations</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="rounded-xl border border-border divide-y divide-border overflow-hidden">
            {WEBHOOKS.map(wh => (
              <div key={wh.event} className="flex items-center justify-between gap-4 px-4 py-3 hover:bg-muted/30 transition-colors">
                <code className="font-mono text-sm text-foreground">{wh.event}</code>
                <span className="text-sm text-muted-foreground">{wh.desc}</span>
              </div>
            ))}
          </div>
          <p className="text-sm text-muted-foreground">
            Configure webhook endpoints in <a href="/settings" className="text-primary hover:underline">Settings → Integrations</a>.
            All events are signed with HMAC-SHA256 using your webhook secret.
          </p>
        </CardContent>
      </Card>

      {/* SDKs */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Code2 className="h-4 w-4 text-muted-foreground" />
            Official SDKs
          </CardTitle>
        </CardHeader>
        <CardContent className="grid gap-3 sm:grid-cols-3">
          {[
            { lang: 'Python', pkg: 'pip install ai-lead-intel', status: 'stable' },
            { lang: 'TypeScript / Node.js', pkg: 'npm install @ai-lead-intel/sdk', status: 'stable' },
            { lang: 'Go', pkg: 'go get github.com/aileadintel/sdk-go', status: 'beta' },
          ].map(sdk => (
            <div key={sdk.lang} className="rounded-xl border border-border p-4 space-y-2">
              <div className="flex items-center justify-between">
                <p className="text-sm font-semibold text-foreground">{sdk.lang}</p>
                <Badge variant={sdk.status === 'stable' ? 'success' : 'warning'} className="text-[10px]">{sdk.status}</Badge>
              </div>
              <div className="flex items-center gap-2 rounded-lg bg-muted px-3 py-2">
                <code className="flex-1 text-xs font-mono text-foreground">{sdk.pkg}</code>
                <CopyButton text={sdk.pkg} />
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  )
}
