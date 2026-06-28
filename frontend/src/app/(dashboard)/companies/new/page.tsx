'use client'

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useRouter } from 'next/navigation'
import { ArrowLeft, Building2, Loader2 } from 'lucide-react'
import Link from 'next/link'
import { toast } from 'sonner'
import { useCreateCompany } from '@/hooks/useCompanies'
import { PageHeader } from '@/components/enterprise/PageHeader'
import { Button } from '@/components/ui/Button'
import { Card, CardContent } from '@/components/ui/card'

const schema = z.object({
  name: z.string().min(1, 'Company name is required').max(200),
  domain: z.string().optional(),
  website: z.string().url('Must be a valid URL').optional().or(z.literal('')),
  industry: z.string().optional(),
  country: z.string().optional(),
  city: z.string().optional(),
  employee_count: z.coerce.number().int().min(1).optional().or(z.literal('')),
  annual_revenue: z.coerce.number().min(0).optional().or(z.literal('')),
  founded_year: z.coerce.number().int().min(1800).max(new Date().getFullYear()).optional().or(z.literal('')),
  description: z.string().max(2000).optional(),
  linkedin_url: z.string().url('Must be a valid URL').optional().or(z.literal('')),
  phone: z.string().optional(),
})

type FormValues = z.infer<typeof schema>

const INDUSTRIES = [
  'Technology', 'Software', 'SaaS', 'FinTech', 'HealthTech', 'EdTech',
  'E-commerce', 'Retail', 'Manufacturing', 'Finance', 'Healthcare',
  'Real Estate', 'Media', 'Consulting', 'Legal', 'Marketing', 'Other',
]

export default function NewCompanyPage() {
  const router = useRouter()
  const createCompany = useCreateCompany()

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) })

  const onSubmit = async (values: FormValues) => {
    const payload = {
      name: values.name,
      domain: values.domain || undefined,
      website: values.website || undefined,
      industry: values.industry || undefined,
      country: values.country || undefined,
      city: values.city || undefined,
      employee_count: values.employee_count ? Number(values.employee_count) : undefined,
      annual_revenue: values.annual_revenue ? Number(values.annual_revenue) : undefined,
      founded_year: values.founded_year ? Number(values.founded_year) : undefined,
      description: values.description || undefined,
      linkedin_url: values.linkedin_url || undefined,
      phone: values.phone || undefined,
    }
    const created = await createCompany.mutateAsync(payload)
    toast.success(`${values.name} added successfully`)
    router.push(`/companies/${created.id}`)
  }

  return (
    <div className="page-container max-w-3xl space-y-6">
      <PageHeader
        title="Add Company"
        description="Create a new company record in your database."
        actions={
          <Button variant="ghost" size="sm" asChild>
            <Link href="/companies">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Companies
            </Link>
          </Button>
        }
      />

      <Card>
        <CardContent className="p-6">
          <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-8">
            {/* Core Info */}
            <section className="space-y-4">
              <div className="flex items-center gap-2 pb-2 border-b border-border">
                <Building2 className="h-4 w-4 text-muted-foreground" />
                <h2 className="text-sm font-semibold text-foreground">Company Details</h2>
              </div>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div className="sm:col-span-2">
                  <label className="mb-1.5 block text-sm font-medium text-foreground">
                    Company Name <span className="text-destructive">*</span>
                  </label>
                  <input
                    {...register('name')}
                    className="input-base"
                    placeholder="Acme Corporation"
                    autoFocus
                  />
                  {errors.name && (
                    <p className="mt-1 text-xs text-destructive">{errors.name.message}</p>
                  )}
                </div>

                <div>
                  <label className="mb-1.5 block text-sm font-medium text-foreground">Domain</label>
                  <input
                    {...register('domain')}
                    className="input-base"
                    placeholder="acme.com"
                  />
                </div>

                <div>
                  <label className="mb-1.5 block text-sm font-medium text-foreground">Website</label>
                  <input
                    {...register('website')}
                    className="input-base"
                    placeholder="https://acme.com"
                  />
                  {errors.website && (
                    <p className="mt-1 text-xs text-destructive">{errors.website.message}</p>
                  )}
                </div>

                <div>
                  <label className="mb-1.5 block text-sm font-medium text-foreground">Industry</label>
                  <select {...register('industry')} className="input-base">
                    <option value="">Select industry...</option>
                    {INDUSTRIES.map((i) => <option key={i} value={i}>{i}</option>)}
                  </select>
                </div>

                <div>
                  <label className="mb-1.5 block text-sm font-medium text-foreground">Phone</label>
                  <input
                    {...register('phone')}
                    type="tel"
                    className="input-base"
                    placeholder="+1 (555) 000-0000"
                  />
                </div>

                <div>
                  <label className="mb-1.5 block text-sm font-medium text-foreground">Country</label>
                  <input
                    {...register('country')}
                    className="input-base"
                    placeholder="United States"
                  />
                </div>

                <div>
                  <label className="mb-1.5 block text-sm font-medium text-foreground">City</label>
                  <input
                    {...register('city')}
                    className="input-base"
                    placeholder="San Francisco"
                  />
                </div>

                <div>
                  <label className="mb-1.5 block text-sm font-medium text-foreground">Employee Count</label>
                  <input
                    {...register('employee_count')}
                    type="number"
                    min={1}
                    className="input-base"
                    placeholder="500"
                  />
                  {errors.employee_count && (
                    <p className="mt-1 text-xs text-destructive">{errors.employee_count.message}</p>
                  )}
                </div>

                <div>
                  <label className="mb-1.5 block text-sm font-medium text-foreground">Annual Revenue (USD)</label>
                  <input
                    {...register('annual_revenue')}
                    type="number"
                    min={0}
                    className="input-base"
                    placeholder="10000000"
                  />
                </div>

                <div>
                  <label className="mb-1.5 block text-sm font-medium text-foreground">Founded Year</label>
                  <input
                    {...register('founded_year')}
                    type="number"
                    min={1800}
                    max={new Date().getFullYear()}
                    className="input-base"
                    placeholder="2015"
                  />
                </div>

                <div>
                  <label className="mb-1.5 block text-sm font-medium text-foreground">LinkedIn URL</label>
                  <input
                    {...register('linkedin_url')}
                    className="input-base"
                    placeholder="https://linkedin.com/company/acme"
                  />
                  {errors.linkedin_url && (
                    <p className="mt-1 text-xs text-destructive">{errors.linkedin_url.message}</p>
                  )}
                </div>

                <div className="sm:col-span-2">
                  <label className="mb-1.5 block text-sm font-medium text-foreground">Description</label>
                  <textarea
                    {...register('description')}
                    className="input-base min-h-[100px] resize-y"
                    placeholder="Brief description of the company..."
                  />
                </div>
              </div>
            </section>

            {createCompany.isError && (
              <div className="rounded-lg border border-destructive/20 bg-destructive/5 p-3 text-sm text-destructive">
                {(createCompany.error as Error)?.message || 'Failed to create company. Please try again.'}
              </div>
            )}

            <div className="flex items-center justify-end gap-3 pt-2 border-t border-border">
              <Button type="button" variant="outline" asChild>
                <Link href="/companies">Cancel</Link>
              </Button>
              <Button type="submit" disabled={isSubmitting || createCompany.isPending}>
                {createCompany.isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Creating...
                  </>
                ) : (
                  'Create Company'
                )}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
