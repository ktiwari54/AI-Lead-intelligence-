'use client'

import { useEffect, useState } from 'react'
import { Search, Sparkles, ArrowRight } from 'lucide-react'
import { cn } from '@/lib/utils'

const PLACEHOLDERS = [
  'Find logistics companies in Dubai with verified emails',
  'VP of Engineering at Series B fintech companies in NYC',
  'SaaS companies in Austin with 50-500 employees',
  'CTOs at healthcare startups using AWS',
]

interface AISearchBarProps {
  value: string
  onChange: (value: string) => void
  onSubmit: () => void
  loading?: boolean
  className?: string
  size?: 'default' | 'hero'
}

export function AISearchBar({
  value,
  onChange,
  onSubmit,
  loading,
  className,
  size = 'default',
}: AISearchBarProps) {
  const [placeholderIndex, setPlaceholderIndex] = useState(0)
  const [focused, setFocused] = useState(false)
  const looksLikeNL = value.length > 10 && /\s/.test(value)
  const isHero = size === 'hero'

  useEffect(() => {
    const t = setInterval(() => setPlaceholderIndex((i) => (i + 1) % PLACEHOLDERS.length), 4000)
    return () => clearInterval(t)
  }, [])

  return (
    <form
      onSubmit={(e) => { e.preventDefault(); onSubmit() }}
      className={cn('relative', className)}
    >
      <div
        className={cn(
          'absolute -inset-0.5 rounded-2xl bg-gradient-to-r from-blue-500/40 via-indigo-500/40 to-cyan-500/40 opacity-0 blur transition-opacity duration-300',
          (focused || value.length > 0) && 'opacity-100'
        )}
      />
      <div
        className={cn(
          'relative flex items-center gap-3 rounded-2xl border border-border bg-card shadow-lg transition-shadow',
          isHero ? 'px-5 py-4' : 'px-4 py-3',
          focused && 'border-primary/40 shadow-xl'
        )}
      >
        <div className={cn(
          'flex shrink-0 items-center justify-center rounded-xl bg-primary/10',
          isHero ? 'h-12 w-12' : 'h-10 w-10'
        )}>
          <Search className={cn('text-primary', isHero ? 'h-5 w-5' : 'h-4 w-4')} />
        </div>

        <input
          type="search"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          placeholder={PLACEHOLDERS[placeholderIndex]}
          className={cn(
            'min-w-0 flex-1 bg-transparent text-foreground placeholder:text-muted-foreground focus:outline-none',
            isHero ? 'text-lg' : 'text-base'
          )}
          aria-label="AI lead discovery search"
        />

        <div className="flex shrink-0 items-center gap-2">
          {(looksLikeNL || value.length > 0) && (
            <span className="hidden items-center gap-1 rounded-full bg-primary/10 px-2.5 py-1 text-xs font-semibold text-primary sm:flex">
              <Sparkles className="h-3.5 w-3.5" />
              AI parsed
            </span>
          )}
          <button
            type="submit"
            disabled={!value.trim() || loading}
            className={cn(
              'inline-flex items-center gap-2 rounded-xl bg-primary font-semibold text-primary-foreground shadow-md shadow-primary/25 transition-all hover:bg-primary/90 disabled:opacity-50',
              isHero ? 'px-6 py-3 text-sm' : 'px-4 py-2 text-sm'
            )}
          >
            {loading ? 'Searching...' : 'Discover'}
            {!loading && <ArrowRight className="h-4 w-4" />}
          </button>
        </div>
      </div>
    </form>
  )
}