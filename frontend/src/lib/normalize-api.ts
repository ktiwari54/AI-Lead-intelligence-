import { PaginatedResponse } from '@/types'

export interface ApiPaginatedRaw<T> {
  success?: boolean
  data?: T[]
  items?: T[]
  total: number
  page: number
  per_page?: number
  page_size?: number
  pages?: number
  total_pages?: number
}

export interface ApiEnvelope<T> {
  success?: boolean
  data?: T
}

export function normalizePaginated<T>(raw: ApiPaginatedRaw<T>): PaginatedResponse<T> {
  const items = raw.data ?? raw.items ?? []
  const perPage = raw.per_page ?? raw.page_size ?? 25
  const totalPages = (raw.pages ?? raw.total_pages ?? Math.ceil(raw.total / perPage)) || 0

  return {
    items,
    total: raw.total,
    page: raw.page,
    per_page: perPage,
    total_pages: totalPages,
  }
}

export function unwrapData<T>(raw: T | ApiEnvelope<T>): T {
  if (raw && typeof raw === 'object' && 'data' in raw && (raw as ApiEnvelope<T>).data !== undefined) {
    return (raw as ApiEnvelope<T>).data as T
  }
  return raw as T
}