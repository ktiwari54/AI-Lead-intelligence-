import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { get, post, patch, del } from '@/lib/api'
import { Company, PaginatedResponse } from '@/types'

export interface CompanyFilters {
  page?: number
  per_page?: number
  search?: string
  industry?: string
  country?: string
  status?: string
  min_employees?: number
  max_employees?: number
}

export function useCompanies(filters: CompanyFilters = {}) {
  return useQuery<PaginatedResponse<Company>>({
    queryKey: ['companies', filters],
    queryFn: () =>
      get<PaginatedResponse<Company>>('/companies', { params: filters }),
    staleTime: 2 * 60 * 1000,
  })
}

export function useCompany(id: string) {
  return useQuery<Company>({
    queryKey: ['companies', id],
    queryFn: () => get<Company>(`/companies/${id}`),
    enabled: Boolean(id),
    staleTime: 2 * 60 * 1000,
  })
}

export function useCreateCompany() {
  const queryClient = useQueryClient()

  return useMutation<Company, Error, Partial<Company>>({
    mutationFn: (data) => post<Company>('/companies', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['companies'] })
    },
  })
}

export function useUpdateCompany() {
  const queryClient = useQueryClient()

  return useMutation<Company, Error, { id: string; data: Partial<Company> }>({
    mutationFn: ({ id, data }) => patch<Company>(`/companies/${id}`, data),
    onSuccess: (updated) => {
      queryClient.invalidateQueries({ queryKey: ['companies'] })
      queryClient.setQueryData(['companies', updated.id], updated)
    },
  })
}

export function useDeleteCompany() {
  const queryClient = useQueryClient()

  return useMutation<void, Error, string>({
    mutationFn: (id) => del<void>(`/companies/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['companies'] })
    },
  })
}
