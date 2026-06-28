import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { get, post } from '@/lib/api'
import { unwrapData } from '@/lib/normalize-api'
import { getToken, setToken, clearToken, setUser, clearUser } from '@/lib/auth'

async function establishSession(): Promise<void> {
  await fetch('/api/auth/session', { method: 'POST', credentials: 'include' })
}

async function clearSession(): Promise<void> {
  await fetch('/api/auth/session', { method: 'DELETE', credentials: 'include' })
}
import { LoginRequest, TokenResponse, User } from '@/types'

interface ApiEnvelope<T> {
  success?: boolean
  data?: T
}

function extractErrorMessage(error: unknown): string {
  if (error && typeof error === 'object' && 'response' in error) {
    const response = (error as { response?: { data?: { detail?: string | Array<{ msg?: string }> } } }).response
    const detail = response?.data?.detail
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail) && detail[0]?.msg) return detail[0].msg
  }
  if (error instanceof Error) return error.message
  return 'Invalid email or password. Please try again.'
}

export function useCurrentUser() {
  return useQuery<User>({
    queryKey: ['currentUser'],
    queryFn: async () => {
      const raw = await get<User | ApiEnvelope<User>>('/users/me')
      return unwrapData(raw)
    },
    enabled: typeof window !== 'undefined' && getToken() !== null,
    staleTime: 5 * 60 * 1000,
    retry: false,
  })
}

export function useLogin(redirectTo = '/dashboard') {
  const queryClient = useQueryClient()
  const router = useRouter()

  return useMutation<TokenResponse, Error, LoginRequest>({
    mutationFn: async (credentials) => {
      try {
        const raw = await post<TokenResponse | ApiEnvelope<TokenResponse>>('/auth/login', credentials)
        return unwrapData(raw)
      } catch (error) {
        throw new Error(extractErrorMessage(error))
      }
    },
    onSuccess: async (tokens) => {
      setToken(tokens.access_token)
      try {
        const userRaw = await get<User | ApiEnvelope<User>>('/users/me')
        const user = unwrapData(userRaw)
        setUser(user)
        queryClient.setQueryData(['currentUser'], user)
      } catch {
        // Token is valid; profile can load on next navigation
      }
      await establishSession()
      if (typeof window !== 'undefined') {
        window.location.assign(redirectTo)
      } else {
        router.push(redirectTo)
      }
    },
  })
}

export interface RegisterRequest {
  organization_name: string
  first_name: string
  last_name: string
  email: string
  password: string
  timezone?: string
}

export function useRegister(redirectTo = '/dashboard') {
  const queryClient = useQueryClient()
  const router = useRouter()

  return useMutation<TokenResponse, Error, RegisterRequest>({
    mutationFn: async (data) => {
      try {
        const raw = await post<TokenResponse | ApiEnvelope<TokenResponse>>('/auth/register', data)
        return unwrapData(raw)
      } catch (error) {
        throw new Error(extractErrorMessage(error))
      }
    },
    onSuccess: async (tokens) => {
      setToken(tokens.access_token)
      try {
        const userRaw = await get<User | ApiEnvelope<User>>('/users/me')
        const user = unwrapData(userRaw)
        setUser(user)
        queryClient.setQueryData(['currentUser'], user)
      } catch {
        // Profile loads on next navigation
      }
      await establishSession()
      if (typeof window !== 'undefined') {
        window.location.assign(redirectTo)
      } else {
        router.push(redirectTo)
      }
    },
  })
}

export function useLogout() {
  const queryClient = useQueryClient()
  const router = useRouter()

  return async () => {
    clearToken()
    clearUser()
    queryClient.clear()
    await clearSession()
    router.push('/login')
  }
}