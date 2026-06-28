'use client'

import { useState, useRef, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Send, Sparkles, User, Bot } from 'lucide-react'
import { useAIAssistantStore } from '@/stores/ai-assistant-store'
import { parseSearchIntent } from '@/lib/parse-search-intent'
import { cn } from '@/lib/utils'

interface AIChatProps {
  className?: string
  showContext?: boolean
  onNavigate?: () => void
}

function generateResponse(
  input: string,
  ctx: { type: string | null; name: string | null }
): { content: string; suggestions?: string[] } {
  const lower = input.toLowerCase()

  if (lower.includes('find') || lower.includes('search') || lower.includes('discover')) {
    const intent = parseSearchIntent(input)
    return {
      content: `I'll search for ${intent.intent.replace(/_/g, ' ')} matching your criteria.${
        intent.industries.length ? ` Industries: ${intent.industries.join(', ')}.` : ''
      }${
        intent.countries.length ? ` Locations: ${intent.countries.join(', ')}.` : ''
      } Opening Lead Discovery with your query.`,
      suggestions: ['Run search now', 'Refine filters', 'Save this search'],
    }
  }

  if (lower.includes('score')) {
    const target = ctx.name ?? 'this record'
    return {
      content: `I can run AI scoring on ${target}. Scoring evaluates seniority, company fit, engagement signals, and technology alignment.`,
      suggestions: ['Score now', 'View score breakdown', 'Compare to ICP'],
    }
  }

  if (lower.includes('similar') || lower.includes('lookalike')) {
    return {
      content:
        'I can find similar companies using vector embeddings. Results are ranked by semantic similarity to your target company profile.',
      suggestions: ['Find top 10 similar', 'Export similar list', 'Add to pipeline'],
    }
  }

  if (lower.includes('outreach') || lower.includes('email') || lower.includes('draft')) {
    return {
      content:
        'I can draft personalized outreach based on the contact\'s role, company context, and recent activity. Would you like a short intro email or a LinkedIn message?',
      suggestions: ['Draft intro email', 'Draft LinkedIn message', 'Suggest talking points'],
    }
  }

  return {
    content:
      'I can help with lead discovery, scoring, finding similar companies, and drafting outreach. What would you like to do?',
    suggestions: [
      'Find logistics companies in Dubai',
      'Score top leads',
      'Draft outreach email',
    ],
  }
}

export function AIChat({ className, showContext = true, onNavigate }: AIChatProps) {
  const router = useRouter()
  const [input, setInput] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)
  const { messages, entityContext, addMessage } = useAIAssistantStore()

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = () => {
    const text = input.trim()
    if (!text) return
    addMessage({ role: 'user', content: text })
    setInput('')

    setTimeout(() => {
      const response = generateResponse(text, entityContext)
      addMessage({
        role: 'assistant',
        content: response.content,
        suggestions: response.suggestions,
      })

      const lower = text.toLowerCase()
      if (lower.includes('find') || lower.includes('search') || lower.includes('run search')) {
        onNavigate?.()
        router.push(`/search?q=${encodeURIComponent(text)}`)
      }
    }, 400)
  }

  const handleSuggestion = (s: string) => {
    if (s === 'Run search now') {
      const lastUser = [...messages].reverse().find((m) => m.role === 'user')
      if (lastUser) router.push(`/search?q=${encodeURIComponent(lastUser.content)}`)
      onNavigate?.()
      return
    }
    setInput(s)
  }

  return (
    <div className={cn('flex flex-col', className)}>
      <div className="flex-1 overflow-y-auto space-y-4 p-4 min-h-0">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={cn('flex gap-3', msg.role === 'user' ? 'flex-row-reverse' : '')}
          >
            <div
              className={cn(
                'flex h-8 w-8 shrink-0 items-center justify-center rounded-full',
                msg.role === 'user' ? 'bg-primary text-primary-foreground' : 'bg-muted'
              )}
            >
              {msg.role === 'user' ? (
                <User className="h-4 w-4" />
              ) : (
                <Bot className="h-4 w-4 text-primary" />
              )}
            </div>
            <div className={cn('max-w-[85%] space-y-2', msg.role === 'user' ? 'text-right' : '')}>
              <div
                className={cn(
                  'rounded-xl px-4 py-2.5 text-sm leading-relaxed',
                  msg.role === 'user'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted text-foreground'
                )}
              >
                {msg.content}
              </div>
              {msg.suggestions && msg.suggestions.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  {msg.suggestions.map((s) => (
                    <button
                      key={s}
                      type="button"
                      onClick={() => handleSuggestion(s)}
                      className="rounded-full border border-border bg-card px-2.5 py-1 text-xs text-muted-foreground hover:bg-accent hover:text-foreground"
                    >
                      {s}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {showContext && entityContext.name && (
        <div className="border-t border-border px-4 py-2 text-xs text-muted-foreground">
          Context: {entityContext.name}
          {entityContext.score != null && ` · Score: ${entityContext.score}`}
        </div>
      )}

      <div className="border-t border-border p-4">
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Sparkles className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
              placeholder="Ask anything..."
              className="input-base w-full pl-9"
            />
          </div>
          <button
            type="button"
            onClick={handleSend}
            disabled={!input.trim()}
            className="rounded-lg bg-primary px-3 py-2 text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
            aria-label="Send message"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  )
}