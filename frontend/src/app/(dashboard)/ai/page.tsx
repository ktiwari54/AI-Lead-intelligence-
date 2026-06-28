'use client'

import Link from 'next/link'
import { Pin, Plus } from 'lucide-react'
import { AIChat } from '@/features/ai/AIChat'
import { useAIAssistantStore } from '@/stores/ai-assistant-store'
import { PageHeader } from '@/components/enterprise/PageHeader'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import Button from '@/components/ui/Button'

const QUICK_ACTIONS = [
  { label: 'Score this company', query: 'Score this company' },
  { label: 'Find similar companies', query: 'Find similar companies' },
  { label: 'Draft outreach email', query: 'Draft an outreach email' },
  { label: 'Summarize', query: 'Summarize this record' },
]

export default function AIAssistantPage() {
  const { entityContext, pinnedChats, clearMessages, pinChat } = useAIAssistantStore()

  return (
    <div className="page-container mx-auto max-w-6xl space-y-6">
      <PageHeader
        title="AI Assistant"
        description="Discover leads, score prospects, and get actionable recommendations."
        badge="AI-first"
        actions={
          <>
            <Button variant="secondary" size="sm" onClick={() => pinChat('Current chat')}>
              <Pin className="h-4 w-4 mr-1" />
              Pin
            </Button>
            <Button variant="secondary" size="sm" onClick={clearMessages}>
              <Plus className="h-4 w-4 mr-1" />
              New Chat
            </Button>
          </>
        }
      />

      <div className="grid gap-6 lg:grid-cols-[1fr_280px]">
        <Card className="flex h-[calc(100vh-220px)] flex-col overflow-hidden">
          <AIChat className="flex-1" showContext={false} />
        </Card>

        <aside className="space-y-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base">Context</CardTitle>
            </CardHeader>
            <CardContent>
            {entityContext.name ? (
              <dl className="space-y-2 text-sm">
                <div>
                  <dt className="text-xs text-muted-foreground">Entity</dt>
                  <dd className="font-medium text-foreground">{entityContext.name}</dd>
                </div>
                {entityContext.score != null && (
                  <div>
                    <dt className="text-xs text-muted-foreground">Score</dt>
                    <dd className="font-medium text-foreground">{entityContext.score}</dd>
                  </div>
                )}
                {entityContext.id && entityContext.type && (
                  <Link
                    href={`/${entityContext.type === 'company' ? 'companies' : 'contacts'}/${entityContext.id}`}
                    className="text-xs text-primary hover:underline"
                  >
                    Open 360° view
                  </Link>
                )}
              </dl>
            ) : (
              <p className="text-xs text-muted-foreground">
                Open a company or contact 360° page to attach context.
              </p>
            )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base">Quick Actions</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-1.5">
                {QUICK_ACTIONS.map((a) => (
                  <li key={a.label}>
                    <button
                      type="button"
                      className="w-full rounded-md px-2 py-1.5 text-left text-xs text-muted-foreground hover:bg-accent hover:text-foreground"
                    >
                      {a.label}
                    </button>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>

          {pinnedChats.length > 0 && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base">Pinned Chats</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-1">
                  {pinnedChats.map((c) => (
                    <li key={c.id} className="truncate text-xs text-muted-foreground">
                      {c.title}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}
        </aside>
      </div>
    </div>
  )
}