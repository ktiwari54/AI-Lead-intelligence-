'use client'

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import Link from 'next/link'
import { Suspense } from 'react'
import { Sparkles, AlertCircle, Loader2 } from 'lucide-react'
import { useRegister } from '@/hooks/useAuth'

const registerSchema = z.object({
  organization_name: z.string().min(2, 'Organization name is required'),
  first_name: z.string().min(1, 'First name is required'),
  last_name: z.string().min(1, 'Last name is required'),
  email: z.string().email('Please enter a valid email'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
  confirm_password: z.string(),
}).refine((d) => d.password === d.confirm_password, {
  message: 'Passwords do not match',
  path: ['confirm_password'],
})

type RegisterFormValues = z.infer<typeof registerSchema>

function RegisterForm() {
  const registerMutation = useRegister('/dashboard')

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      organization_name: '',
      first_name: '',
      last_name: '',
      email: '',
      password: '',
      confirm_password: '',
    },
  })

  const onSubmit = async (values: RegisterFormValues) => {
    await registerMutation.mutateAsync({
      organization_name: values.organization_name,
      first_name: values.first_name,
      last_name: values.last_name,
      email: values.email,
      password: values.password,
    })
  }

  return (
    <div className="flex min-h-screen">
      <div className="relative hidden w-[40%] overflow-hidden bg-gradient-to-br from-slate-950 via-indigo-950 to-blue-950 lg:flex lg:flex-col lg:justify-between lg:p-12">
        <div className="relative">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-white/10 backdrop-blur">
              <Sparkles className="h-6 w-6 text-indigo-200" />
            </div>
            <span className="text-xl font-semibold text-white">AI Lead Intelligence</span>
          </div>
        </div>
        <div className="relative">
          <h2 className="text-3xl font-bold text-white">Start discovering leads today</h2>
          <p className="mt-3 max-w-sm text-sm leading-relaxed text-indigo-100/80">
            Create your organization workspace and get instant access to AI-powered lead discovery.
          </p>
        </div>
        <p className="relative text-xs text-indigo-200/50">© 2026 AI Lead Intelligence Platform</p>
      </div>

      <div className="flex flex-1 items-center justify-center bg-gradient-to-b from-slate-50 to-white px-6 py-12">
        <div className="w-full max-w-md">
          <div className="mb-8 lg:hidden">
            <div className="flex items-center gap-2">
              <Sparkles className="h-6 w-6 text-primary" />
              <span className="text-lg font-semibold text-foreground">AI Lead Intelligence</span>
            </div>
          </div>

          <div className="mb-8">
            <h1 className="text-2xl font-bold tracking-tight text-foreground">Create account</h1>
            <p className="mt-2 text-sm text-muted-foreground">
              Already have an account?{' '}
              <Link href="/login" className="font-medium text-primary hover:underline">
                Sign in
              </Link>
            </p>
          </div>

          <div className="rounded-2xl border border-border bg-card p-8 shadow-xl shadow-slate-200/50">
            <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
              <div>
                <label className="mb-1.5 block text-sm font-medium text-foreground">Organization</label>
                <input {...register('organization_name')} className="input-base h-11 w-full" placeholder="Acme Inc." />
                {errors.organization_name && <p className="mt-1 text-xs text-destructive">{errors.organization_name.message}</p>}
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-foreground">First name</label>
                  <input {...register('first_name')} className="input-base h-11 w-full" />
                  {errors.first_name && <p className="mt-1 text-xs text-destructive">{errors.first_name.message}</p>}
                </div>
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-foreground">Last name</label>
                  <input {...register('last_name')} className="input-base h-11 w-full" />
                  {errors.last_name && <p className="mt-1 text-xs text-destructive">{errors.last_name.message}</p>}
                </div>
              </div>
              <div>
                <label className="mb-1.5 block text-sm font-medium text-foreground">Email</label>
                <input {...register('email')} type="email" autoComplete="email" className="input-base h-11 w-full" placeholder="you@company.com" />
                {errors.email && <p className="mt-1 text-xs text-destructive">{errors.email.message}</p>}
              </div>
              <div>
                <label className="mb-1.5 block text-sm font-medium text-foreground">Password</label>
                <input {...register('password')} type="password" autoComplete="new-password" className="input-base h-11 w-full" />
                {errors.password && <p className="mt-1 text-xs text-destructive">{errors.password.message}</p>}
              </div>
              <div>
                <label className="mb-1.5 block text-sm font-medium text-foreground">Confirm password</label>
                <input {...register('confirm_password')} type="password" autoComplete="new-password" className="input-base h-11 w-full" />
                {errors.confirm_password && <p className="mt-1 text-xs text-destructive">{errors.confirm_password.message}</p>}
              </div>

              {registerMutation.isError && (
                <div className="flex items-start gap-2 rounded-lg border border-destructive/20 bg-destructive/5 p-3">
                  <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-destructive" />
                  <p className="text-sm text-destructive">{(registerMutation.error as Error)?.message || 'Registration failed.'}</p>
                </div>
              )}

              <button
                type="submit"
                disabled={isSubmitting || registerMutation.isPending}
                className="btn h-11 w-full rounded-lg bg-primary text-sm font-semibold text-primary-foreground shadow-md hover:bg-primary/90"
              >
                {registerMutation.isPending ? (
                  <span className="flex items-center justify-center gap-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Creating account...
                  </span>
                ) : (
                  'Create account'
                )}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  )
}

export default function RegisterPage() {
  return (
    <Suspense fallback={<div className="flex min-h-screen items-center justify-center">Loading...</div>}>
      <RegisterForm />
    </Suspense>
  )
}