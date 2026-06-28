'use client'

import { Suspense, useState, useEffect, useCallback } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { Clock, Star, ChevronDown, ChevronUp, Building2, Users, TrendingUp } from 'lucide-react'
import { PageHeader } from '@/components/enterprise/PageHeader'
import { AISearchBar } from '@/features/discovery/AISearchBar'
import { ParsedIntentPreview } from '@/features/discovery/ParsedIntentPreview'
import { SearchProgress } from '@/features/discovery/SearchProgress'
import { parseSearchIntent } from '@/lib/parse-search-intent'
import { useSearchHistory, useSavedSearches } from '@/hooks/useSearch'

const EXAMPLE_QUERIES = [
  'SaaS companies in Austin',
  'VP Sales at fintech startups',
  'Logistics companies in Dubai',
  'Healthcare CTOs using AWS',
]

function LeadDiscoveryContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [query, setQuery] = useState('')
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [showProgress, setShowProgress] = useState(false)
  const [industry, setIndustry] = useState('')
  const [country, setCountry] = useState('')
  const [minEmployees, setMinEmployees] = useState('')
  const [maxEmployees, setMaxEmployees] = useState('')

  const { data: history = [] } = useSearchHistory()
  const { data: saved = [] } = useSavedSearches()

  useEffect(() => {
    const q = searchParams.get('q')
    if (q) setQuery(q)
  }, [searchParams])

  const parsedIntent = query.trim().length > 3 ? parseSearchIntent(query) : null

  const runSearch = useCallback(() => {
    if (!query.trim()) return
    setShowProgress(true)
    const params = new URLSearchParams({ q: query.trim() })
    if (industry) params.set('industry', industry)
    if (country) params.set('country', country)
    if (minEmployees) params.set('min_employees', minEmployees)
    if (maxEmployees) params.set('max_employees', maxEmployees)
    router.push(`/search/results?${params.toString()}`)
  }, [query, industry, country, minEmployees, maxEmployees, router])

  return (
    <div className="page-container max-w-5xl">
      <PageHeader
        title="Lead Discovery"
        description="Describe your ideal customer in plain English. AI parses intent, runs the discovery pipeline, and returns scored leads."
        badge="AI-first"
      />

      {/* Hero search */}
      <section className="relative overflow-hidden rounded-2xl border border-border bg-gradient-to-br from-slate-50 via-white to-indigo-50/40 p-6 md:p-10">
        <div className="absolute -right-16 -top-16 h-64 w-64 rounded-full bg-blue-400/10 blur-3xl" />
        <div className="absolute -bottom-20 -left-10 h-48 w-48 rounded-full bg-indigo-400/10 blur-3xl" />

        <div className="relative">
          <div className="mt-2">
            <AISearchBar
              value={query}
              onChange={setQuery}
              onSubmit={runSearch}
              loading={showProgress}
              size="hero"
            />
          </div>

          <div className="mt-4 flex flex-wrap gap-2">
            <span className="text-xs text-muted-foreground">Try:</span>
            {EXAMPLE_QUERIES.map((example) => (
              <button
                key={example}
                type="button"
                onClick={() => setQuery(example)}
                className="rounded-full border border-border bg-card px-3 py-1 text-xs font-medium text-foreground transition-colors hover:border-primary/40 hover:bg-primary/5 hover:text-primary"
              >
                {example}
              </button>
            ))}
          </div>
        </div>
      </section>

      <ParsedIntentPreview
        intent={parsedIntent}
        onSearch={runSearch}
        onEditFilters={() => setShowAdvanced((v) => !v)}
        loading={showProgress}
      />

      <SearchProgress
        active={showProgress}
        onComplete={() => setShowProgress(false)}
      />

      {/* Stats row */}
      <div className="grid gap-4 sm:grid-cols-3">
        {[
          { icon: Building2, label: 'Companies', value: '3 providers', sub: 'Apollo, Clearbit, Mock' },
          { icon: Users, label: 'Contacts', value: 'Verified', sub: 'Email + title enrichment' },
          { icon: TrendingUp, label: 'Confidence', value: '0–99 score', sub: 'Explainable per hit' },
        ].map(({ icon: Icon, label, value, sub }) => (
          <div
            key={label}
            className="rounded-2xl border border-border bg-card p-5 shadow-sm transition-shadow hover:shadow-md"
          >
            <div className="flex items-center gap-3">
              <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10">
                <Icon className="h-5 w-5 text-primary" />
              </span>
              <div>
                <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{label}</p>
                <p className="text-lg font-semibold text-foreground">{value}</p>
                <p className="text-xs text-muted-foreground">{sub}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Advanced filters */}
      <div className="overflow-hidden rounded-2xl border border-border bg-card shadow-sm">
        <button
          type="button"
          onClick={() => setShowAdvanced((v) => !v)}
          className="flex w-full items-center justify-between px-5 py-4 text-sm font-semibold text-foreground hover:bg-muted/50"
        >
          Advanced Filters
          {showAdvanced ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </button>
        {showAdvanced && (
          <div className="grid gap-4 border-t border-border bg-muted/20 p-5 sm:grid-cols-2">
            <div>
              <label className="text-xs font-medium text-muted-foreground">Industry</label>
              <input
                value={industry}
                onChange={(e) => setIndustry(e.target.value)}
                className="input-base mt-1.5"
                placeholder="SaaS, Logistics..."
              />
            </div>
            <div>
              <label className="text-xs font-medium text-muted-foreground">Country</label>
              <input
                value={country}
                onChange={(e) => setCountry(e.target.value)}
                className="input-base mt-1.5"
                placeholder="US, AE, GB..."
              />
            </div>
            <div>
              <label className="text-xs font-medium text-muted-foreground">Min Employees</label>
              <input
                type="number"
                value={minEmployees}
                onChange={(e) => setMinEmployees(e.target.value)}
                className="input-base mt-1.5"
              />
            </div>
            <div>
              <label className="text-xs font-medium text-muted-foreground">Max Employees</label>
              <input
                type="number"
                value={maxEmployees}
                onChange={(e) => setMaxEmployees(e.target.value)}
                className="input-base mt-1.5"
              />
            </div>
          </div>
        )}
      </div>

      {/* History & saved */}
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="rounded-2xl border border-border bg-card p-5 shadow-sm">
          <div className="mb-4 flex items-center gap-2">
            <Clock className="h-4 w-4 text-primary" />
            <h3 className="text-sm font-semibold text-foreground">Recent Searches</h3>
          </div>
          {history.length === 0 ? (
            <p className="text-sm text-muted-foreground">Your search history will appear here</p>
          ) : (
            <ul className="space-y-2">
              {history.slice(0, 5).map((item) => {
                const q = String((item.filters as { query?: string })?.query ?? 'Search')
                return (
                  <li key={item.id}>
                    <button
                      type="button"
                      onClick={() => { setQuery(q); runSearch() }}
                      className="w-full rounded-lg px-2 py-2 text-left text-sm text-foreground transition-colors hover:bg-muted truncate"
                    >
                      {q}
                      {item.result_count != null && (
                        <span className="ml-1 text-xs text-muted-foreground">
                          ({item.result_count} results)
                        </span>
                      )}
                    </button>
                  </li>
                )
              })}
            </ul>
          )}
        </div>

        <div className="rounded-2xl border border-border bg-card p-5 shadow-sm">
          <div className="mb-4 flex items-center gap-2">
            <Star className="h-4 w-4 text-warning" />
            <h3 className="text-sm font-semibold text-foreground">Saved Searches</h3>
          </div>
          {saved.length === 0 ? (
            <p className="text-sm text-muted-foreground">Save a search from results to see it here</p>
          ) : (
            <ul className="space-y-2">
              {saved.slice(0, 5).map((item) => (
                <li key={item.id}>
                  <button
                    type="button"
                    onClick={() => {
                      const q = String((item.filters as { query?: string })?.query ?? item.name)
                      setQuery(q)
                      runSearch()
                    }}
                    className="flex w-full items-center gap-2 rounded-lg px-2 py-2 text-sm text-foreground transition-colors hover:bg-muted"
                  >
                    <Star className="h-3.5 w-3.5 fill-warning text-warning" />
                    {item.name}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  )
}

export default function LeadDiscoveryPage() {
  return (
    <Suspense fallback={<div className="h-64 animate-pulse rounded-2xl bg-muted" />}>
      <LeadDiscoveryContent />
    </Suspense>
  )
}