import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { get, post, del } from '@/lib/api'
import { normalizePaginated, unwrapData } from '@/lib/normalize-api'

export interface ExportJob {
  id: string
  name: string
  format: string
  entity_type: string
  status: string
  filters: Record<string, unknown>
  row_count?: number
  created_at: string
}

export interface ImportJob {
  id: string
  name: string
  entity_type: string
  status: string
  total_rows?: number
  processed_rows?: number
  failed_rows?: number
  mapping: Record<string, string>
  created_at: string
}

export function useExports(page = 1) {
  return useQuery({
    queryKey: ['exports', page],
    queryFn: async () => {
      const raw = await get<Record<string, unknown>>('/exports/', { params: { page, page_size: 25 } })
      const paginated = normalizePaginated<ExportJob>(raw as never)
      return paginated
    },
    staleTime: 30_000,
  })
}

export function useCreateExport() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (data: {
      name: string
      format: 'CSV' | 'JSON' | 'EXCEL'
      entity_type: 'companies' | 'contacts' | 'leads'
      filters?: Record<string, unknown>
    }) => {
      const raw = await post<ExportJob | { data: ExportJob }>('/exports/', data)
      return unwrapData(raw)
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['exports'] }),
  })
}

export function useExport(id: string) {
  return useQuery({
    queryKey: ['exports', id],
    queryFn: async () => {
      const raw = await get<ExportJob | { data: ExportJob }>(`/exports/${id}`)
      return unwrapData(raw)
    },
    enabled: Boolean(id),
    refetchInterval: (query) =>
      query.state.data?.status === 'COMPLETED' || query.state.data?.status === 'FAILED'
        ? false
        : 3000,
  })
}

export function useDeleteExport() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => del<void>(`/exports/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['exports'] }),
  })
}

export function useCreateImport() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (data: {
      name: string
      entity_type: 'companies' | 'contacts'
      mapping: Record<string, string>
    }) => {
      const raw = await post<ImportJob | { data: ImportJob }>('/exports/imports', data)
      return unwrapData(raw)
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['imports'] }),
  })
}

export function useImportJob(id: string) {
  return useQuery({
    queryKey: ['imports', id],
    queryFn: async () => {
      const raw = await get<ImportJob | { data: ImportJob }>(`/exports/imports/${id}`)
      return unwrapData(raw)
    },
    enabled: Boolean(id),
    refetchInterval: (query) =>
      query.state.data?.status === 'COMPLETED' || query.state.data?.status === 'FAILED'
        ? false
        : 2000,
  })
}

export function getExportDownloadUrl(id: string) {
  const base = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'
  return `${base}/exports/${id}/download`
}