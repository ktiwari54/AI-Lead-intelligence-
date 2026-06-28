'use client'

import Link from 'next/link'
import { HelpCircle, BookOpen, Keyboard, MessageCircle, Mail, ExternalLink } from 'lucide-react'
import { PageHeader } from '@/components/enterprise/PageHeader'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { useKeyboardShortcutsStore } from '@/stores/keyboard-shortcuts-store'

const GUIDES = [
  { title: 'Lead Discovery', description: 'Search in plain English, parse intent, and run the discovery pipeline.', href: '/search' },
  { title: 'AI Scoring', description: 'Score companies and contacts with confidence breakdowns.', href: '/ai-scoring' },
  { title: 'CRM Pipeline', description: 'Drag deals between stages and track open tasks.', href: '/crm' },
  { title: 'Imports & Exports', description: 'Bulk import CSV data and export scored leads.', href: '/imports' },
]

const SHORTCUTS = [
  { keys: '⌘K', action: 'Command palette' },
  { keys: '⌘J', action: 'AI Assistant' },
  { keys: '⌘B', action: 'Toggle sidebar' },
  { keys: '?', action: 'Keyboard shortcuts' },
]

export default function HelpPage() {
  const openShortcuts = useKeyboardShortcutsStore((s) => s.setOpen)

  return (
    <div className="page-container max-w-4xl space-y-6">
      <PageHeader
        title="Help & Support"
        description="Documentation, keyboard shortcuts, and ways to get assistance."
      />

      <div className="grid gap-4 sm:grid-cols-2">
        {GUIDES.map((guide) => (
          <Link key={guide.href} href={guide.href}>
            <Card className="h-full transition-colors hover:border-primary/40">
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-2 text-base">
                  <BookOpen className="h-4 w-4 text-primary" />
                  {guide.title}
                </CardTitle>
                <CardDescription>{guide.description}</CardDescription>
              </CardHeader>
              <CardContent>
                <span className="inline-flex items-center gap-1 text-xs font-medium text-primary">
                  Open guide <ExternalLink className="h-3 w-3" />
                </span>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-base">
            <Keyboard className="h-4 w-4 text-muted-foreground" />
            Keyboard Shortcuts
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {SHORTCUTS.map((s) => (
            <div key={s.keys} className="flex items-center justify-between rounded-lg border border-border px-4 py-2.5">
              <span className="text-sm text-foreground">{s.action}</span>
              <kbd className="rounded border border-border bg-muted px-2 py-0.5 font-mono text-xs">{s.keys}</kbd>
            </div>
          ))}
          <button
            onClick={() => openShortcuts(true)}
            className="mt-2 text-sm font-medium text-primary hover:underline"
          >
            View all shortcuts →
          </button>
        </CardContent>
      </Card>

      <div className="grid gap-4 sm:grid-cols-2">
        <Card>
          <CardContent className="flex items-start gap-4 p-5">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10">
              <MessageCircle className="h-5 w-5 text-primary" />
            </div>
            <div>
              <p className="font-semibold text-foreground">AI Assistant</p>
              <p className="mt-1 text-sm text-muted-foreground">Ask questions about leads, scoring, and next best actions.</p>
              <Link href="/ai" className="mt-2 inline-block text-sm font-medium text-primary hover:underline">
                Open AI Assistant
              </Link>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-start gap-4 p-5">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10">
              <Mail className="h-5 w-5 text-primary" />
            </div>
            <div>
              <p className="font-semibold text-foreground">Contact Support</p>
              <p className="mt-1 text-sm text-muted-foreground">Enterprise customers get priority support via email.</p>
              <a href="mailto:support@aileadintel.com" className="mt-2 inline-block text-sm font-medium text-primary hover:underline">
                support@aileadintel.com
              </a>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card className="border-dashed">
        <CardContent className="flex items-center gap-3 p-5 text-sm text-muted-foreground">
          <HelpCircle className="h-5 w-5 shrink-0 text-primary" />
          Full documentation is available in <code className="rounded bg-muted px-1.5 py-0.5 text-xs">docs/frontend-v3/</code> in the repository.
        </CardContent>
      </Card>
    </div>
  )
}