import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { get, patch } from '@/lib/api'
import { normalizePaginated, unwrapData } from '@/lib/normalize-api'

export interface AdminStats {
  total_organizations: number
  total_users: number
  total_companies: number
  total_contacts: number
  total_searches_today: number
  total_exports_pending: number
}

export interface AuditLog {
  id: string
  action: string
  resource_type: string
  resource_id?: string
  user_id?: string
  ip_address?: string
  created_at: string
}

export interface FeatureFlag {
  id: string
  key: string
  name: string
  description?: string
  is_enabled: boolean
  rollout_percentage: number
  updated_at: string
}

export interface SystemSetting {
  id: string
  key: string
  value: unknown
  description?: string
  is_public: boolean
  is_editable: boolean
  updated_at: string
}

export function useAdminStats() {
  return useQuery({
    queryKey: ['admin', 'stats'],
    queryFn: async () => {
      const raw = await get<{ data: AdminStats }>('/admin/stats')
      return unwrapData(raw) as AdminStats
    },
    staleTime: 60_000,
  })
}

export function useAuditLogs(page = 1) {
  return useQuery({
    queryKey: ['admin', 'audit-logs', page],
    queryFn: async () => {
      const raw = await get<Record<string, unknown>>('/admin/audit-logs', {
        params: { page, per_page: 25 },
      })
      return normalizePaginated<AuditLog>(raw as never)
    },
    staleTime: 30_000,
  })
}

export function useFeatureFlags() {
  return useQuery({
    queryKey: ['admin', 'feature-flags'],
    queryFn: async () => {
      const raw = await get<{ data: FeatureFlag[] }>('/admin/feature-flags')
      return unwrapData(raw) as FeatureFlag[]
    },
    staleTime: 60_000,
  })
}

export function useUpdateFeatureFlag() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ key, is_enabled }: { key: string; is_enabled: boolean }) =>
      patch(`/admin/feature-flags/${key}`, { is_enabled }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin', 'feature-flags'] }),
  })
}

export function useSystemSettings() {
  return useQuery({
    queryKey: ['admin', 'settings'],
    queryFn: async () => {
      const raw = await get<{ data: SystemSetting[] }>('/admin/settings')
      return unwrapData(raw) as SystemSetting[]
    },
    staleTime: 60_000,
  })
}

export function useUpdateSystemSetting() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ key, value }: { key: string; value: unknown }) =>
      patch(`/admin/settings/${key}`, { value }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin', 'settings'] }),
  })
}