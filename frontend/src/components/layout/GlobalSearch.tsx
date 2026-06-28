'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { Search, Sparkles } from 'lucide-react'
import { cn } from '@/lib/utils'

const AI_PLACEHOLDERS = [
  'Find logistics companies in Dubai with verified emails',
  'VP of Engineering at Series B fintech companies in NYC',
  'SaaS companies in California with 50-500 employees',
  'CTOs at healthcare startups using AWS',
  'Marketing directors at e-commerce companies in Europe',
]

export function GlobalSearch({ className }: { className?: string }) {
  const router = useRouter()
  const [query, setQuery] = useState('')
  const [placeholderIndex, setPlaceholderIndex] = useState(0)
  const [focused, setFocused] = useState(false)

  useEffect(() => {
    const interval = setInterval(() => {
      setPlaceholderIndex((i) => (i + 1) % AI_PLACEHOLDERS.length)
    }, 4000)
    return () => clearInterval(interval)
  }, [])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return
    router.push(`/search?q=${encodeURIComponent(query.trim())}`)
  }

  const looksLikeNL = query.length > 10 && /\s/.test(query)

  return (
    <form onSubmit={handleSubmit} className={cn('relative flex-1 max-w-2xl', className)}>
      <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
      <input
        type="search"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        placeholder={AI_PLACEHOLDERS[placeholderIndex]}
        className={cn(
          'h-10 w-full rounded-lg border border-input bg-muted/50 pl-9 pr-20 text-sm transition-all',
          'placeholder:text-muted-foreground',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:border-primary',
          focused && 'bg-background shadow-sm'
        )}
        aria-label="Global search"
      />
      <div className="absolute right-2 top-1/2 flex -translate-y-1/2 items-center gap-1.5">
        {looksLikeNL && (
          <span className="flex items-center gap-1 rounded-md bg-primary/10 px-1.5 py-0.5 text-xs text-primary">
            <Sparkles className="h-3 w-3" />
            AI
          </span>
        )}
        <kbd className="hidden sm:inline-flex h-5 items-center rounded border border-border bg-muted px-1.5 text-[10px] font-medium text-muted-foreground">
          ⌘K
        </kbd>
      </div>
    </form>
  )
}