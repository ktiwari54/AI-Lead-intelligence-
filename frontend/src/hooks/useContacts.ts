import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { get, post, patch, del } from '@/lib/api'
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
  return useQuery<PaginatedResponse<Contact>>({
    queryKey: ['contacts', filters],
    queryFn: () =>
      get<PaginatedResponse<Contact>>('/contacts', { params: filters }),
    staleTime: 2 * 60 * 1000,
  })
}

export function useContact(id: string) {
  return useQuery<Contact>({
    queryKey: ['contacts', id],
    queryFn: () => get<Contact>(`/contacts/${id}`),
    enabled: Boolean(id),
    staleTime: 2 * 60 * 1000,
  })
}

export function useCreateContact() {
  const queryClient = useQueryClient()

  return useMutation<Contact, Error, Partial<Contact>>({
    mutationFn: (data) => post<Contact>('/contacts', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contacts'] })
    },
  })
}

export function useUpdateContact() {
  const queryClient = useQueryClient()

  return useMutation<Contact, Error, { id: string; data: Partial<Contact> }>({
    mutationFn: ({ id, data }) => patch<Contact>(`/contacts/${id}`, data),
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
