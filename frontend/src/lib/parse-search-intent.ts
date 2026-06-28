export interface ParsedIntent {
  intent: 'find_companies' | 'find_contacts' | 'find_both'
  query: string
  industries: string[]
  countries: string[]
  technologies: string[]
  seniority_levels: string[]
  min_employees?: number
  max_employees?: number
  email_verified?: boolean
  connectors: string[]
}

const INDUSTRY_KEYWORDS: Record<string, string> = {
  logistics: 'Logistics',
  saas: 'SaaS',
  fintech: 'Fintech',
  healthcare: 'Healthcare',
  ecommerce: 'E-commerce',
  manufacturing: 'Manufacturing',
  retail: 'Retail',
}

const LOCATION_KEYWORDS: Record<string, string> = {
  dubai: 'AE',
  'united arab emirates': 'AE',
  uae: 'AE',
  'new york': 'US',
  nyc: 'US',
  california: 'US',
  london: 'GB',
  uk: 'GB',
  europe: 'EU',
}

const SENIORITY_KEYWORDS: Record<string, string> = {
  ceo: 'C_LEVEL',
  cto: 'C_LEVEL',
  'vp': 'VP',
  'vice president': 'VP',
  director: 'DIRECTOR',
  manager: 'MANAGER',
}

const TECH_KEYWORDS = ['aws', 'react', 'kubernetes', 'docker', 'salesforce', 'hubspot']

export function parseSearchIntent(rawQuery: string): ParsedIntent {
  const query = rawQuery.trim()
  const lower = query.toLowerCase()

  const industries: string[] = []
  for (const [kw, label] of Object.entries(INDUSTRY_KEYWORDS)) {
    if (lower.includes(kw)) industries.push(label)
  }

  const countries: string[] = []
  for (const [kw, code] of Object.entries(LOCATION_KEYWORDS)) {
    if (lower.includes(kw) && !countries.includes(code)) countries.push(code)
  }

  const technologies: string[] = []
  for (const tech of TECH_KEYWORDS) {
    if (lower.includes(tech)) technologies.push(tech.toUpperCase())
  }

  const seniority_levels: string[] = []
  for (const [kw, level] of Object.entries(SENIORITY_KEYWORDS)) {
    if (lower.includes(kw) && !seniority_levels.includes(level)) seniority_levels.push(level)
  }

  let min_employees: number | undefined
  let max_employees: number | undefined
  const rangeMatch = lower.match(/(\d+)\s*[-–]\s*(\d+)\s*employees?/)
  if (rangeMatch) {
    min_employees = Number(rangeMatch[1])
    max_employees = Number(rangeMatch[2])
  }

  const email_verified = lower.includes('verified email') || lower.includes('verified emails')

  const findContacts =
    lower.includes('contact') ||
    lower.includes('vp ') ||
    lower.includes('cto') ||
    lower.includes('director') ||
    seniority_levels.length > 0

  const findCompanies =
    lower.includes('compan') ||
    lower.includes('startup') ||
    lower.includes('firm') ||
    industries.length > 0

  let intent: ParsedIntent['intent'] = 'find_both'
  if (findContacts && !findCompanies) intent = 'find_contacts'
  else if (findCompanies && !findContacts) intent = 'find_companies'

  return {
    intent,
    query,
    industries,
    countries,
    technologies,
    seniority_levels,
    min_employees,
    max_employees,
    email_verified,
    connectors: ['apollo', 'clearbit'],
  }
}

export function intentToSearchPayload(intent: ParsedIntent, page = 1) {
  return {
    query: intent.query,
    entity_type:
      intent.intent === 'find_companies'
        ? 'companies'
        : intent.intent === 'find_contacts'
          ? 'contacts'
          : 'both',
    industries: intent.industries,
    countries: intent.countries,
    technologies: intent.technologies,
    seniority_levels: intent.seniority_levels,
    min_employees: intent.min_employees,
    max_employees: intent.max_employees,
    email_status: intent.email_verified ? 'verified' : undefined,
    page,
    page_size: 25,
  }
}

/** Phase 5 discovery API payload (`POST /discovery/execute`). */
export function intentToDiscoveryPayload(
  intent: ParsedIntent,
  options?: { async_mode?: boolean; page?: number }
) {
  return {
    query: intent.query,
    entity_type:
      intent.intent === 'find_companies'
        ? 'company'
        : intent.intent === 'find_contacts'
          ? 'contact'
          : 'both',
    filters: {
      industries: intent.industries,
      countries: intent.countries,
      technologies: intent.technologies,
      seniority_levels: intent.seniority_levels,
      employee_min: intent.min_employees,
      employee_max: intent.max_employees,
      email_verified: intent.email_verified,
      page: options?.page ?? 1,
      page_size: 25,
    },
    connectors: intent.connectors,
    enrich: true,
    verify_contacts: intent.email_verified ?? false,
    async_mode: options?.async_mode ?? false,
  }
}