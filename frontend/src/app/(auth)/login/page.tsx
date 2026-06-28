'use client'

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import Link from 'next/link'
import { useSearchParams } from 'next/navigation'
import { Suspense } from 'react'
import { Sparkles, Shield, Zap, Target, AlertCircle, Loader2 } from 'lucide-react'
import { useLogin } from '@/hooks/useAuth'

const loginSchema = z.object({
  email: z.string().email('Please enter a valid email address'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
})

type LoginFormValues = z.infer<typeof loginSchema>

const DEV_EMAIL = process.env.NEXT_PUBLIC_DEV_EMAIL ?? ''
const DEV_PASSWORD = process.env.NEXT_PUBLIC_DEV_PASSWORD ?? ''
const SHOW_DEV_PANEL = process.env.NODE_ENV === 'development' && !!DEV_EMAIL

function LoginForm() {
  const searchParams = useSearchParams()
  const redirectTo = searchParams.get('from') || '/dashboard'
  const login = useLogin(redirectTo)

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: '', password: '' },
  })

  const fillDevCredentials = () => {
    setValue('email', DEV_EMAIL, { shouldValidate: true })
    setValue('password', DEV_PASSWORD, { shouldValidate: true })
  }

  const onSubmit = async (values: LoginFormValues) => {
    await login.mutateAsync(values)
  }

  return (
    <div className="flex min-h-screen">
      {/* Brand panel */}
      <div className="relative hidden w-[45%] overflow-hidden bg-gradient-to-br from-slate-950 via-blue-950 to-indigo-900 lg:flex lg:flex-col lg:justify-between lg:p-12">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_rgba(59,130,246,0.25),_transparent_50%)]" />
        <div className="absolute -left-20 top-1/3 h-72 w-72 rounded-full bg-blue-500/20 blur-3xl" />
        <div className="absolute -right-10 bottom-20 h-64 w-64 rounded-full bg-indigo-400/20 blur-3xl" />

        <div className="relative">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-white/10 backdrop-blur">
              <Sparkles className="h-6 w-6 text-blue-200" />
            </div>
            <span className="text-xl font-semibold tracking-tight text-white">AI Lead Intelligence</span>
          </div>
        </div>

        <div className="relative space-y-8">
          <div>
            <h2 className="text-4xl font-bold leading-tight text-white">
              Find your next
              <span className="block bg-gradient-to-r from-blue-200 to-cyan-200 bg-clip-text text-transparent">
                high-intent leads
              </span>
            </h2>
            <p className="mt-4 max-w-md text-base leading-relaxed text-blue-100/80">
              AI-powered discovery across licensed data providers. Search in plain English,
              score confidence, and export to your CRM.
            </p>
          </div>

          <ul className="space-y-4">
            {[
              { icon: Zap, text: 'Natural language search with live pipeline progress' },
              { icon: Target, text: 'Confidence scoring on every company & contact hit' },
              { icon: Shield, text: 'Tenant-isolated, API-only — no unauthorized scraping' },
            ].map(({ icon: Icon, text }) => (
              <li key={text} className="flex items-start gap-3 text-sm text-blue-100/90">
                <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-white/10">
                  <Icon className="h-4 w-4 text-cyan-200" />
                </span>
                {text}
              </li>
            ))}
          </ul>
        </div>

        <p className="relative text-xs text-blue-200/50">© 2026 AI Lead Intelligence Platform</p>
      </div>

      {/* Form panel */}
      <div className="flex flex-1 items-center justify-center bg-gradient-to-b from-slate-50 to-white px-6 py-12">
        <div className="w-full max-w-md">
          <div className="mb-8 lg:hidden">
            <div className="flex items-center gap-2">
              <Sparkles className="h-6 w-6 text-primary" />
              <span className="text-lg font-semibold text-foreground">AI Lead Intelligence</span>
            </div>
          </div>

          <div className="mb-8">
            <h1 className="text-2xl font-bold tracking-tight text-foreground">Welcome back</h1>
            <p className="mt-2 text-sm text-muted-foreground">
              Sign in to start discovering leads.{' '}
              <Link href="/register" className="font-medium text-primary hover:underline">
                Create account
              </Link>
            </p>
          </div>

          {SHOW_DEV_PANEL && (
            <div className="mb-6 rounded-xl border border-dashed border-primary/30 bg-primary/5 p-4">
              <p className="text-xs font-medium uppercase tracking-wide text-primary">Local dev account</p>
              <p className="mt-1 text-sm text-muted-foreground">
                <span className="font-mono text-foreground">{DEV_EMAIL}</span>
              </p>
              <button
                type="button"
                onClick={fillDevCredentials}
                className="mt-3 text-sm font-medium text-primary hover:underline"
              >
                Fill credentials →
              </button>
            </div>
          )}

          <div className="rounded-2xl border border-border bg-card p-8 shadow-xl shadow-slate-200/50">
            <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-5">
              <div>
                <label htmlFor="email" className="mb-1.5 block text-sm font-medium text-foreground">
                  Email
                </label>
                <input
                  id="email"
                  type="email"
                  autoComplete="email"
                  {...register('email')}
                  className="input-base h-11"
                  placeholder="you@company.com"
                />
                {errors.email && (
                  <p className="mt-1.5 flex items-center gap-1 text-xs text-destructive">
                    <AlertCircle className="h-3.5 w-3.5" />
                    {errors.email.message}
                  </p>
                )}
              </div>

              <div>
                <label htmlFor="password" className="mb-1.5 block text-sm font-medium text-foreground">
                  Password
                </label>
                <input
                  id="password"
                  type="password"
                  autoComplete="current-password"
                  {...register('password')}
                  className="input-base h-11"
                  placeholder="••••••••"
                />
                {errors.password && (
                  <p className="mt-1.5 flex items-center gap-1 text-xs text-destructive">
                    <AlertCircle className="h-3.5 w-3.5" />
                    {errors.password.message}
                  </p>
                )}
              </div>

              {login.isError && (
                <div className="flex items-start gap-2 rounded-lg border border-destructive/20 bg-destructive/5 p-3">
                  <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-destructive" />
                  <p className="text-sm text-destructive">
                    {(login.error as Error)?.message || 'Sign in failed. Please try again.'}
                  </p>
                </div>
              )}

              <button
                type="submit"
                disabled={isSubmitting || login.isPending}
                className="btn h-11 w-full rounded-lg bg-primary text-sm font-semibold text-primary-foreground shadow-md shadow-primary/20 hover:bg-primary/90"
              >
                {login.isPending ? (
                  <span className="flex items-center gap-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Signing in...
                  </span>
                ) : (
                  'Sign in'
                )}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  )
}

export default function LoginPage() {
  return (
    <Suspense fallback={<div className="flex min-h-screen items-center justify-center">Loading...</div>}>
      <LoginForm />
    </Suspense>
  )
}