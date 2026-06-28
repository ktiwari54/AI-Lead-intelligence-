import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { get, post, del } from '@/lib/api'
import { unwrapData } from '@/lib/normalize-api'
import { ParsedIntent, intentToSearchPayload, intentToDiscoveryPayload } from '@/lib/parse-search-intent'

const SEARCH_PATHS = ['/search/', '/search/search/'] as const
const DISCOVERY_PATH = '/discovery/execute'

export interface SearchHit {
  id: string
  entity_type: 'company' | 'contact' | string
  score: number
  data: Record<string, unknown>
  highlight?: Record<string, string[]>
  confidence?: number
  source_trust?: number
  explanation?: Record<string, unknown>
}

export interface SearchResult {
  total: number
  page: number
  page_size: number
  hits: SearchHit[]
  took_ms: number
  job_id?: string
}

export interface DiscoveryJobStatus {
  id: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'partial'
  query?: string
  entity_type?: string
  stages?: Record<string, string>
  progress_pct?: number
  result_count?: number
  error_message?: string
  poll_url?: string
}

export interface SavedSearch {
  id: string
  name: string
  description?: string
  filters: Record<string, unknown>
  created_at: string
}

export interface SearchHistoryItem {
  id: string
  filters: Record<string, unknown>
  result_count?: number
  created_at: string
}

interface DiscoveryHitRaw {
  id: string
  entity_type: string
  confidence: number
  source_trust?: number
  field_completeness?: number
  data: Record<string, unknown>
  explanation?: Record<string, unknown>
}

interface DiscoveryResultRaw {
  job_id?: string
  total: number
  hits: DiscoveryHitRaw[]
  took_ms: number
  connectors?: Array<{ name: string; success: boolean; latency_ms: number }>
}

function mapDiscoveryHit(hit: DiscoveryHitRaw): SearchHit {
  const confidence = hit.confidence ?? 0.5
  return {
    id: String(hit.id),
    entity_type: hit.entity_type,
    score: Math.round(confidence * 100),
    confidence,
    source_trust: hit.source_trust,
    data: hit.data ?? {},
    explanation: hit.explanation,
  }
}

function mapDiscoveryResult(raw: DiscoveryResultRaw, page = 1, pageSize = 25): SearchResult {
  return {
    total: raw.total ?? raw.hits?.length ?? 0,
    page,
    page_size: pageSize,
    took_ms: raw.took_ms ?? 0,
    job_id: raw.job_id,
    hits: (raw.hits ?? []).map(mapDiscoveryHit),
  }
}

export async function pollDiscoveryJob(jobId: string, attempts = 60): Promise<DiscoveryJobStatus> {
  for (let i = 0; i < attempts; i++) {
    const statusRaw = await get<DiscoveryJobStatus | { data: DiscoveryJobStatus }>(
      `/discovery/jobs/${jobId}`
    )
    const status = unwrapData(statusRaw as DiscoveryJobStatus)
    if (status.status === 'completed' || status.status === 'partial' || status.status === 'failed') {
      return status
    }
    await new Promise((r) => setTimeout(r, 1000))
  }
  throw new Error('Discovery job timed out')
}

export async function fetchDiscoveryResults(jobId: string): Promise<SearchResult> {
  const resultsRaw = await get<DiscoveryResultRaw | { data: DiscoveryResultRaw }>(
    `/discovery/jobs/${jobId}/results`
  )
  const results = unwrapData(resultsRaw as DiscoveryResultRaw)
  return mapDiscoveryResult({ ...results, job_id: jobId })
}

async function postDiscovery(payload: object): Promise<SearchResult | { job: DiscoveryJobStatus }> {
  const raw = await post<DiscoveryResultRaw | DiscoveryJobStatus | { data: DiscoveryResultRaw | DiscoveryJobStatus }>(
    DISCOVERY_PATH,
    payload
  )
  const result = unwrapData(raw as DiscoveryResultRaw | DiscoveryJobStatus)

  if ('hits' in result && Array.isArray((result as DiscoveryResultRaw).hits)) {
    const page = (payload as { filters?: { page?: number } }).filters?.page ?? 1
    return mapDiscoveryResult(result as DiscoveryResultRaw, page)
  }

  const job = result as DiscoveryJobStatus
  return { job: { ...job, id: job.id } }
}

async function runDiscoveryWithPolling(intent: ParsedIntent, page = 1): Promise<SearchResult> {
  const payload = intentToDiscoveryPayload(intent, { async_mode: true, page })
  const response = await postDiscovery(payload)

  if ('hits' in response) {
    return response as SearchResult
  }

  const jobId = response.job.id
  const finalStatus = await pollDiscoveryJob(jobId)
  if (finalStatus.status === 'failed') {
    throw new Error(finalStatus.error_message ?? 'Discovery job failed')
  }
  return fetchDiscoveryResults(jobId)
}

async function postSearch(payload: object): Promise<SearchResult> {
  let lastError: unknown
  for (const path of SEARCH_PATHS) {
    try {
      const raw = await post<SearchResult | { data: SearchResult }>(path, payload)
      const result = unwrapData(raw as SearchResult)
      return {
        ...result,
        hits: (result.hits ?? []).map((h) => ({
          ...h,
          id: String(h.id),
          confidence: Math.min(0.99, 0.7 + (h.score ?? 0) / 300),
        })),
      }
    } catch (e) {
      lastError = e
    }
  }
  throw lastError
}

export function useDiscoveryJob(jobId: string | null) {
  return useQuery({
    queryKey: ['discovery', 'job', jobId],
    queryFn: async () => {
      const raw = await get<DiscoveryJobStatus | { data: DiscoveryJobStatus }>(`/discovery/jobs/${jobId}`)
      return unwrapData(raw as DiscoveryJobStatus)
    },
    enabled: !!jobId,
    refetchInterval: (query) => {
      const status = query.state.data?.status
      if (!status || status === 'completed' || status === 'failed' || status === 'partial') return false
      return 1000
    },
  })
}

/** Async discovery with live job polling — for results page UI. */
export function useDiscoverySearch() {
  const [jobId, setJobId] = useState<string | null>(null)

  const startMutation = useMutation({
    mutationFn: async (intent: ParsedIntent) => {
      const payload = intentToDiscoveryPayload(intent, { async_mode: true })
      const raw = await post<DiscoveryJobStatus | { data: DiscoveryJobStatus }>(DISCOVERY_PATH, payload)
      const job = unwrapData(raw as DiscoveryJobStatus)
      return job.id
    },
    onSuccess: (id) => setJobId(id),
  })

  const jobQuery = useDiscoveryJob(jobId)

  const resultsQuery = useQuery({
    queryKey: ['discovery', 'results', jobId],
    queryFn: () => fetchDiscoveryResults(jobId!),
    enabled:
      !!jobId &&
      (jobQuery.data?.status === 'completed' || jobQuery.data?.status === 'partial'),
  })

  const reset = () => setJobId(null)

  return {
    jobId,
    jobStatus: jobQuery.data,
    results: resultsQuery.data,
    isLoading:
      startMutation.isPending ||
      (!!jobId && !resultsQuery.data && jobQuery.data?.status !== 'failed'),
    isFailed: jobQuery.data?.status === 'failed',
    error: jobQuery.data?.error_message ?? startMutation.error,
    start: startMutation.mutate,
    reset,
  }
}



export function useExecuteSearch() {
  return useMutation({
    mutationFn: async (payload: object & { _intent?: ParsedIntent }) => {
      const { _intent, ...rest } = payload
      if (_intent) {
        try {
          return await runDiscoveryWithPolling(_intent, (rest as { page?: number }).page ?? 1)
        } catch {
          return postSearch(rest)
        }
      }
      return postSearch(rest)
    },
  })
}

export function useAISearch() {
  return useMutation({
    mutationFn: async (intent: ParsedIntent) => {
      try {
        return await runDiscoveryWithPolling(intent)
      } catch {
        return postSearch(intentToSearchPayload(intent))
      }
    },
  })
}

export function useDiscoveryPreview() {
  return useMutation({
    mutationFn: async (query: string) => {
      const raw = await post<{ data?: { intent?: Record<string, unknown> } }>('/discovery/preview', { query })
      return unwrapData(raw as { intent?: Record<string, unknown> })
    },
  })
}

export function useSemanticCompanySearch() {
  return useMutation({
    mutationFn: async (query: string) => {
      const raw = await get<{ data: { results: SearchHit[]; total: number } }>(
        '/ai/search/companies',
        { params: { q: query, limit: 20 } }
      )
      const data = unwrapData(raw as { data: { results: SearchHit[]; total: number } })
      return {
        total: data.total,
        page: 1,
        page_size: 20,
        took_ms: 0,
        hits: data.results.map((r) => ({
          id: String(r.id),
          entity_type: 'company',
          score: (r as { similarity?: number }).similarity
            ? ((r as { similarity?: number }).similarity ?? 0) * 100
            : r.score ?? 0,
          data: r.data ?? {},
          confidence: (r as { similarity?: number }).similarity,
        })),
      } satisfies SearchResult
    },
  })
}

export function useSearchHistory() {
  return useQuery({
    queryKey: ['search', 'history'],
    queryFn: async () => {
      try {
        const raw = await get<{ data?: SearchHistoryItem[]; items?: SearchHistoryItem[] }>('/search/history')
        return raw.data ?? raw.items ?? []
      } catch {
        return [] as SearchHistoryItem[]
      }
    },
    staleTime: 60_000,
  })
}

export function useSavedSearches() {
  return useQuery({
    queryKey: ['search', 'saved'],
    queryFn: async () => {
      try {
        const raw = await get<SavedSearch[] | { data: SavedSearch[] }>('/search/saved')
        return Array.isArray(raw) ? raw : (raw.data ?? [])
      } catch {
        return [] as SavedSearch[]
      }
    },
    staleTime: 60_000,
  })
}

export function useSaveSearch() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: { name: string; filters: Record<string, unknown> }) =>
      post<SavedSearch>('/search/saved', data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['search', 'saved'] }),
  })
}

export function useDeleteSavedSearch() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => del<void>(`/search/saved/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['search', 'saved'] }),
  })
}