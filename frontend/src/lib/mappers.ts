import { Company, Contact } from '@/types'

export function mapCompany(raw: Record<string, unknown>): Company {
  const score = raw.lead_score as number | undefined
  return {
    id: String(raw.id ?? ''),
    name: String(raw.company_name ?? raw.name ?? ''),
    domain: raw.domain ? String(raw.domain) : raw.website ? String(raw.website) : undefined,
    industry: raw.industry ? String(raw.industry) : undefined,
    country: raw.country ? String(raw.country) : undefined,
    city: raw.city ? String(raw.city) : undefined,
    employee_count: raw.employee_count != null ? Number(raw.employee_count) : undefined,
    annual_revenue: raw.revenue != null ? Number(raw.revenue) : raw.annual_revenue != null ? Number(raw.annual_revenue) : undefined,
    description: raw.description ? String(raw.description) : undefined,
    website: raw.website ? String(raw.website) : undefined,
    phone: raw.phone ? String(raw.phone) : undefined,
    founded_year: raw.founded_year != null ? Number(raw.founded_year) : undefined,
    tags: Array.isArray(raw.tags) ? (raw.tags as string[]) : [],
    status: (raw.status as Company['status']) ?? 'new',
    organization_id: String(raw.organization_id ?? ''),
    lead_score: score != null
      ? {
          id: String(raw.id),
          entity_type: 'company',
          entity_id: String(raw.id),
          score,
          grade: score >= 80 ? 'A' : score >= 60 ? 'B' : score >= 40 ? 'C' : 'D',
          factors: [],
          reasoning: '',
          generated_at: '',
          model_version: '',
        }
      : undefined,
    created_at: String(raw.created_at ?? ''),
    updated_at: String(raw.updated_at ?? ''),
  }
}

export function mapContact(raw: Record<string, unknown>): Contact {
  const score = raw.lead_score as number | undefined
  return {
    id: String(raw.id ?? ''),
    first_name: String(raw.first_name ?? ''),
    last_name: String(raw.last_name ?? ''),
    email: raw.email ? String(raw.email) : undefined,
    phone: raw.phone ? String(raw.phone) : undefined,
    title: raw.designation ? String(raw.designation) : raw.title ? String(raw.title) : undefined,
    department: raw.department ? String(raw.department) : undefined,
    linkedin_url: raw.linkedin_url ? String(raw.linkedin_url) : undefined,
    company_id: raw.company_id ? String(raw.company_id) : undefined,
    tags: Array.isArray(raw.tags) ? (raw.tags as string[]) : [],
    status: (raw.status as Contact['status']) ?? 'new',
    organization_id: String(raw.organization_id ?? ''),
    lead_score: score != null
      ? {
          id: String(raw.id),
          entity_type: 'contact',
          entity_id: String(raw.id),
          score,
          grade: score >= 80 ? 'A' : score >= 60 ? 'B' : score >= 40 ? 'C' : 'D',
          factors: [],
          reasoning: '',
          generated_at: '',
          model_version: '',
        }
      : undefined,
    created_at: String(raw.created_at ?? ''),
    updated_at: String(raw.updated_at ?? ''),
  }
}