import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { get, post } from '@/lib/api'
import { getToken, setToken, clearToken, setUser, clearUser } from '@/lib/auth'
import { LoginRequest, TokenResponse, User } from '@/types'

export function useCurrentUser() {
  return useQuery<User>({
    queryKey: ['currentUser'],
    queryFn: () => get<User>('/users/me'),
    enabled: typeof window !== 'undefined' && getToken() !== null,
    staleTime: 5 * 60 * 1000,
    retry: false,
  })
}

export function useLogin() {
  const queryClient = useQueryClient()
  const router = useRouter()

  return useMutation<TokenResponse, Error, LoginRequest>({
    mutationFn: (credentials) =>
      post<TokenResponse>('/auth/login', credentials),
    onSuccess: (data) => {
      setToken(data.access_token)
      setUser(data.user)
      queryClient.setQueryData(['currentUser'], data.user)
      router.push('/dashboard')
    },
  })
}

export function useLogout() {
  const queryClient = useQueryClient()
  const router = useRouter()

  return () => {
    clearToken()
    clearUser()
    queryClient.clear()
    router.push('/login')
  }
}
