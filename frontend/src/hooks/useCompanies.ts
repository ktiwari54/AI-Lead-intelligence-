import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { get, post, patch, del } from '@/lib/api'
import { normalizePaginated, unwrapData } from '@/lib/normalize-api'
import { mapCompany } from '@/lib/mappers'
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

const COMPANIES_PATH = '/companies/companies'

export function useCompanies(filters: CompanyFilters = {}) {
  const params = {
    page: filters.page,
    page_size: filters.per_page,
    query: filters.search,
    industry: filters.industry,
    country: filters.country,
  }

  return useQuery<PaginatedResponse<Company>>({
    queryKey: ['companies', filters],
    queryFn: async () => {
      const raw = await get<Record<string, unknown>>(COMPANIES_PATH, { params })
      const paginated = normalizePaginated<Record<string, unknown>>(raw as never)
      return {
        ...paginated,
        items: paginated.items.map(mapCompany),
      }
    },
    staleTime: 2 * 60 * 1000,
  })
}

export function useCompany(id: string) {
  return useQuery<Company>({
    queryKey: ['companies', id],
    queryFn: async () => {
      const raw = await get<Record<string, unknown>>(`${COMPANIES_PATH}/${id}`)
      return mapCompany(unwrapData(raw) as Record<string, unknown>)
    },
    enabled: Boolean(id),
    staleTime: 2 * 60 * 1000,
  })
}

export function useCreateCompany() {
  const queryClient = useQueryClient()

  return useMutation<Company, Error, Partial<Company>>({
    mutationFn: async (data) => {
      const raw = await post<Record<string, unknown>>(COMPANIES_PATH, {
        company_name: data.name,
        domain: data.domain,
        description: data.description,
        employee_count: data.employee_count,
      })
      return mapCompany(unwrapData(raw) as Record<string, unknown>)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['companies'] })
    },
  })
}

export function useUpdateCompany() {
  const queryClient = useQueryClient()

  return useMutation<Company, Error, { id: string; data: Partial<Company> }>({
    mutationFn: async ({ id, data }) => {
      const raw = await patch<Record<string, unknown>>(`${COMPANIES_PATH}/${id}`, {
        company_name: data.name,
        domain: data.domain,
        description: data.description,
        employee_count: data.employee_count,
      })
      return mapCompany(unwrapData(raw) as Record<string, unknown>)
    },
    onSuccess: (updated) => {
      queryClient.invalidateQueries({ queryKey: ['companies'] })
      queryClient.setQueryData(['companies', updated.id], updated)
    },
  })
}

export function useDeleteCompany() {
  const queryClient = useQueryClient()

  return useMutation<void, Error, string>({
    mutationFn: (id) => del<void>(`${COMPANIES_PATH}/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['companies'] })
    },
  })
}