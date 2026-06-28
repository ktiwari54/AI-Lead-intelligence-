'use client'

import { Suspense, useState, useEffect, useMemo } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { ArrowLeft, Sparkles } from 'lucide-react'
import { toast } from 'sonner'
import { parseSearchIntent, intentToSearchPayload } from '@/lib/parse-search-intent'
import {
  useDiscoverySearch,
  useSemanticCompanySearch,
  useSaveSearch,
  SearchHit,
} from '@/hooks/useSearch'
import { useScoreCompany, useScoreContact } from '@/hooks/useAI'
import { PageHeader } from '@/components/enterprise/PageHeader'
import { BulkActionBar } from '@/components/data-table/BulkActionBar'
import { ScoreGauge } from '@/components/ui/ScoreGauge'
import { Card, CardContent } from '@/components/ui/card'
import Badge from '@/components/ui/Badge'
import Pagination from '@/components/ui/Pagination'
import Modal from '@/components/ui/Modal'
import Button from '@/components/ui/Button'
import { exportToCsv, getSelectedIds } from '@/lib/bulk-actions'
import { SearchProgress } from '@/features/discovery/SearchProgress'

function hitName(hit: SearchHit): string {
  const d = hit.data
  if (hit.entity_type === 'contact') {
    return `${d.first_name ?? ''} ${d.last_name ?? ''}`.trim() || 'Unknown'
  }
  return String(d.company_name ?? d.name ?? 'Unknown')
}

function hitSubtitle(hit: SearchHit): string {
  const d = hit.data
  if (hit.entity_type === 'contact') return String(d.designation ?? d.title ?? '')
  return String(d.domain ?? d.industry ?? '')
}

function SearchResultsContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const query = searchParams.get('q') ?? ''
  const [page, setPage] = useState(1)
  const [selection, setSelection] = useState<Record<string, boolean>>({})
  const [saveOpen, setSaveOpen] = useState(false)
  const [saveName, setSaveName] = useState('')

  const discovery = useDiscoverySearch()
  const semanticSearch = useSemanticCompanySearch()
  const saveSearch = useSaveSearch()
  const scoreCompany = useScoreCompany()
  const scoreContact = useScoreContact()

  const intent = useMemo(() => (query ? parseSearchIntent(query) : null), [query])

  useEffect(() => {
    if (!query || !intent) return
    if (searchParams.get('industry')) intent.industries = [searchParams.get('industry')!]
    if (searchParams.get('country')) intent.countries = [searchParams.get('country')!]
    if (searchParams.get('min_employees')) intent.min_employees = Number(searchParams.get('min_employees'))
    if (searchParams.get('max_employees')) intent.max_employees = Number(searchParams.get('max_employees'))

    discovery.reset()
    discovery.start(intent)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [query, page])

  const results = discovery.results
  const hits = results?.hits ?? []
  const selectedIds = getSelectedIds(selection)
  const selectedHits = hits.filter((h) => selectedIds.includes(h.id))

  const toggleAll = () => {
    if (selectedIds.length === hits.length) {
      setSelection({})
    } else {
      const next: Record<string, boolean> = {}
      hits.forEach((h) => { next[h.id] = true })
      setSelection(next)
    }
  }

  const handleExport = () => {
    exportToCsv(
      selectedHits.map((h) => ({
        name: hitName(h),
        type: h.entity_type,
        score: h.score,
        confidence: h.confidence ?? '',
      })),
      [
        { key: 'name', label: 'Name' },
        { key: 'type', label: 'Type' },
        { key: 'score', label: 'Score' },
        { key: 'confidence', label: 'Confidence' },
      ],
      `search-results-${Date.now()}.csv`
    )
    toast.success(`Exported ${selectedIds.length} results`)
  }

  const handleScore = async () => {
    await Promise.all(
      selectedHits.map((h) =>
        h.entity_type === 'company'
          ? scoreCompany.mutateAsync({ companyId: h.id })
          : scoreContact.mutateAsync({ contactId: h.id })
      )
    )
    toast.success('Scoring queued for selected results')
  }

  const totalPages = results ? Math.ceil(results.total / results.page_size) : 1

  const resultDescription = (() => {
    if (results) {
      const suffix = query ? ` — "${query}"` : ''
      return `${results.total} results · ${results.took_ms}ms · Discovery${suffix}`
    }
    if (discovery.isLoading) return 'Running discovery pipeline...'
    if (discovery.isFailed) return 'Discovery failed — check connector health and retry.'
    return 'Enter a query on Lead Discovery to begin.'
  })()

  return (
    <div className="page-container space-y-6">
      <button
        onClick={() => router.push('/search')}
        className="flex items-center gap-1 text-sm text-muted-foreground transition-colors hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" />
        Lead Discovery
      </button>

      {(discovery.isLoading || discovery.jobStatus) && (
        <SearchProgress
          active={discovery.isLoading}
          stages={discovery.jobStatus?.stages}
          progressPct={discovery.jobStatus?.progress_pct}
        />
      )}

      <PageHeader
        title="Search Results"
        description={resultDescription}
        badge={results ? `${results.total} hits` : undefined}
        actions={
          <>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => semanticSearch.mutate(query)}
              loading={semanticSearch.isPending}
            >
              <Sparkles className="h-4 w-4 mr-1" />
              Semantic
            </Button>
            <Button variant="secondary" size="sm" onClick={() => setSaveOpen(true)}>
              Save Search
            </Button>
          </>
        }
      />

      <Card className="overflow-hidden">
        <CardContent className="p-0">
        <div className="flex items-center gap-3 border-b border-border px-4 py-3">
          <input
            type="checkbox"
            checked={hits.length > 0 && selectedIds.length === hits.length}
            onChange={toggleAll}
            className="h-4 w-4 rounded border-border"
          />
          <span className="text-sm text-muted-foreground">
            {selectedIds.length > 0 ? `${selectedIds.length} selected` : 'Select all'}
          </span>
        </div>

        {discovery.isLoading ? (
          <div className="p-8 space-y-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="h-12 animate-pulse rounded bg-muted" />
            ))}
          </div>
        ) : hits.length === 0 ? (
          <p className="px-4 py-12 text-center text-sm text-muted-foreground">No results found</p>
        ) : (
          <table className="w-full">
            <thead className="bg-muted/50">
              <tr>
                <th className="w-10 px-4 py-2" />
                <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Name</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Type</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Industry</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Score</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Conf.</th>
                <th className="px-4 py-2" />
              </tr>
            </thead>
            <tbody>
              {(semanticSearch.data?.hits ?? hits).map((hit) => (
                <tr key={hit.id} className="border-t border-border hover:bg-muted/30">
                  <td className="px-4 py-2.5">
                    <input
                      type="checkbox"
                      checked={!!selection[hit.id]}
                      onChange={() =>
                        setSelection((s) => ({ ...s, [hit.id]: !s[hit.id] }))
                      }
                      className="h-4 w-4 rounded border-border"
                    />
                  </td>
                  <td className="px-4 py-2.5">
                    <p className="text-sm font-medium text-foreground">{hitName(hit)}</p>
                    <p className="text-xs text-muted-foreground">{hitSubtitle(hit)}</p>
                  </td>
                  <td className="px-4 py-2.5">
                    <Badge variant={hit.entity_type === 'company' ? 'primary' : 'success'}>
                      {hit.entity_type}
                    </Badge>
                  </td>
                  <td className="px-4 py-2.5 text-sm text-muted-foreground">
                    {String(hit.data.industry ?? '—')}
                  </td>
                  <td className="px-4 py-2.5">
                    <ScoreGauge score={hit.score} size={36} />
                  </td>
                  <td className="px-4 py-2.5 text-sm text-foreground">
                    {hit.confidence != null ? hit.confidence.toFixed(2) : '—'}
                  </td>
                  <td className="px-4 py-2.5">
                    <Link
                      href={
                        hit.entity_type === 'company'
                          ? `/companies/${hit.id}`
                          : `/contacts/${hit.id}`
                      }
                      className="text-xs text-primary hover:underline"
                    >
                      Open 360°
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {results && totalPages > 1 && (
          <div className="border-t border-border px-4 py-3">
            <Pagination
              page={page}
              totalPages={totalPages}
              total={results.total}
              perPage={results.page_size}
              onPageChange={setPage}
              onPerPageChange={() => {}}
            />
          </div>
        )}
        </CardContent>
      </Card>

      <BulkActionBar
        selectedCount={selectedIds.length}
        onClear={() => setSelection({})}
        actions={[
          { label: 'Export', onClick: handleExport },
          { label: 'Score', onClick: handleScore },
        ]}
      />

      <Modal
        open={saveOpen}
        onClose={() => setSaveOpen(false)}
        title="Save Search"
        footer={
          <div className="flex justify-end gap-3">
            <Button variant="secondary" onClick={() => setSaveOpen(false)}>Cancel</Button>
            <Button
              onClick={async () => {
                await saveSearch.mutateAsync({
                  name: saveName,
                  filters: intentToSearchPayload(intent!),
                })
                setSaveOpen(false)
                toast.success('Search saved')
              }}
              loading={saveSearch.isPending}
              disabled={!saveName.trim()}
            >
              Save
            </Button>
          </div>
        }
      >
        <input
          value={saveName}
          onChange={(e) => setSaveName(e.target.value)}
          placeholder="Search name..."
          className="input-base w-full"
        />
      </Modal>
    </div>
  )
}

export default function SearchResultsPage() {
  return (
    <Suspense fallback={<div className="h-64 animate-pulse rounded-xl bg-muted" />}>
      <SearchResultsContent />
    </Suspense>
  )
}