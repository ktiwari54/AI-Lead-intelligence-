import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { get, post, patch, del } from '@/lib/api'
import { normalizePaginated, unwrapData } from '@/lib/normalize-api'
import { mapContact } from '@/lib/mappers'
import { Contact, PaginatedResponse } from '@/types'

export interface ContactFilters {
  page?: number
  per_page?: number
  search?: string
  company_id?: string
  department?: string
  status?: string
  title?: string
}

export function useContacts(filters: ContactFilters = {}) {
  const params = {
    page: filters.page,
    per_page: filters.per_page,
    query: filters.search,
    department: filters.department,
    company_id: filters.company_id,
  }

  return useQuery<PaginatedResponse<Contact>>({
    queryKey: ['contacts', filters],
    queryFn: async () => {
      const raw = await get<Record<string, unknown>>('/contacts', { params })
      const paginated = normalizePaginated<Record<string, unknown>>(raw as never)
      return {
        ...paginated,
        items: paginated.items.map(mapContact),
      }
    },
    staleTime: 2 * 60 * 1000,
  })
}

export function useContact(id: string) {
  return useQuery<Contact>({
    queryKey: ['contacts', id],
    queryFn: async () => {
      const raw = await get<Record<string, unknown>>(`/contacts/${id}`)
      return mapContact(unwrapData(raw) as Record<string, unknown>)
    },
    enabled: Boolean(id),
    staleTime: 2 * 60 * 1000,
  })
}

export function useCreateContact() {
  const queryClient = useQueryClient()

  return useMutation<Contact, Error, Partial<Contact>>({
    mutationFn: async (data) => {
      const raw = await post<Record<string, unknown>>('/contacts', data)
      return mapContact(unwrapData(raw) as Record<string, unknown>)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contacts'] })
    },
  })
}

export function useUpdateContact() {
  const queryClient = useQueryClient()

  return useMutation<Contact, Error, { id: string; data: Partial<Contact> }>({
    mutationFn: async ({ id, data }) => {
      const raw = await patch<Record<string, unknown>>(`/contacts/${id}`, data)
      return mapContact(unwrapData(raw) as Record<string, unknown>)
    },
    onSuccess: (updated) => {
      queryClient.invalidateQueries({ queryKey: ['contacts'] })
      queryClient.setQueryData(['contacts', updated.id], updated)
    },
  })
}

export function useDeleteContact() {
  const queryClient = useQueryClient()

  return useMutation<void, Error, string>({
    mutationFn: (id) => del<void>(`/contacts/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contacts'] })
    },
  })
}