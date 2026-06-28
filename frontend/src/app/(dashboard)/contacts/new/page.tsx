'use client'

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useRouter } from 'next/navigation'
import { ArrowLeft, User, Loader2 } from 'lucide-react'
import Link from 'next/link'
import { toast } from 'sonner'
import { useCreateContact } from '@/hooks/useContacts'
import { PageHeader } from '@/components/enterprise/PageHeader'
import { Button } from '@/components/ui/Button'
import { Card, CardContent } from '@/components/ui/card'

const schema = z.object({
  first_name: z.string().min(1, 'First name is required').max(100),
  last_name: z.string().min(1, 'Last name is required').max(100),
  email: z.string().email('Must be a valid email').optional().or(z.literal('')),
  phone: z.string().optional(),
  title: z.string().optional(),
  department: z.string().optional(),
  linkedin_url: z.string().url('Must be a valid URL').optional().or(z.literal('')),
})

type FormValues = z.infer<typeof schema>

const DEPARTMENTS = [
  'Engineering', 'Sales', 'Marketing', 'Finance', 'HR',
  'Operations', 'Product', 'Legal', 'Design', 'Customer Success',
]

export default function NewContactPage() {
  const router = useRouter()
  const createContact = useCreateContact()

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) })

  const onSubmit = async (values: FormValues) => {
    const payload = {
      first_name: values.first_name,
      last_name: values.last_name,
      email: values.email || undefined,
      phone: values.phone || undefined,
      title: values.title || undefined,
      department: values.department || undefined,
      linkedin_url: values.linkedin_url || undefined,
    }
    const created = await createContact.mutateAsync(payload)
    toast.success(`${values.first_name} ${values.last_name} added successfully`)
    router.push(`/contacts/${created.id}`)
  }

  return (
    <div className="page-container max-w-3xl space-y-6">
      <PageHeader
        title="Add Contact"
        description="Create a new contact record in your database."
        actions={
          <Button variant="ghost" size="sm" asChild>
            <Link href="/contacts">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Contacts
            </Link>
          </Button>
        }
      />

      <Card>
        <CardContent className="p-6">
          <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-8">
            <section className="space-y-4">
              <div className="flex items-center gap-2 pb-2 border-b border-border">
                <User className="h-4 w-4 text-muted-foreground" />
                <h2 className="text-sm font-semibold text-foreground">Contact Details</h2>
              </div>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-foreground">
                    First Name <span className="text-destructive">*</span>
                  </label>
                  <input
                    {...register('first_name')}
                    className="input-base"
                    placeholder="Jane"
                    autoFocus
                  />
                  {errors.first_name && (
                    <p className="mt-1 text-xs text-destructive">{errors.first_name.message}</p>
                  )}
                </div>

                <div>
                  <label className="mb-1.5 block text-sm font-medium text-foreground">
                    Last Name <span className="text-destructive">*</span>
                  </label>
                  <input
                    {...register('last_name')}
                    className="input-base"
                    placeholder="Smith"
                  />
                  {errors.last_name && (
                    <p className="mt-1 text-xs text-destructive">{errors.last_name.message}</p>
                  )}
                </div>

                <div>
                  <label className="mb-1.5 block text-sm font-medium text-foreground">Email</label>
                  <input
                    {...register('email')}
                    type="email"
                    className="input-base"
                    placeholder="jane@company.com"
                  />
                  {errors.email && (
                    <p className="mt-1 text-xs text-destructive">{errors.email.message}</p>
                  )}
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
                  <label className="mb-1.5 block text-sm font-medium text-foreground">Job Title</label>
                  <input
                    {...register('title')}
                    className="input-base"
                    placeholder="VP of Sales"
                  />
                </div>

                <div>
                  <label className="mb-1.5 block text-sm font-medium text-foreground">Department</label>
                  <select {...register('department')} className="input-base">
                    <option value="">Select department...</option>
                    {DEPARTMENTS.map((d) => <option key={d} value={d}>{d}</option>)}
                  </select>
                </div>

                <div className="sm:col-span-2">
                  <label className="mb-1.5 block text-sm font-medium text-foreground">LinkedIn URL</label>
                  <input
                    {...register('linkedin_url')}
                    className="input-base"
                    placeholder="https://linkedin.com/in/janesmith"
                  />
                  {errors.linkedin_url && (
                    <p className="mt-1 text-xs text-destructive">{errors.linkedin_url.message}</p>
                  )}
                </div>
              </div>
            </section>

            {createContact.isError && (
              <div className="rounded-lg border border-destructive/20 bg-destructive/5 p-3 text-sm text-destructive">
                {(createContact.error as Error)?.message || 'Failed to create contact. Please try again.'}
              </div>
            )}

            <div className="flex items-center justify-end gap-3 pt-2 border-t border-border">
              <Button type="button" variant="outline" asChild>
                <Link href="/contacts">Cancel</Link>
              </Button>
              <Button type="submit" disabled={isSubmitting || createContact.isPending}>
                {createContact.isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Creating...
                  </>
                ) : (
                  'Create Contact'
                )}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
