// ---- Core Entities ----

export interface Organization {
  id: string
  name: string
  slug: string
  plan: 'free' | 'starter' | 'professional' | 'enterprise'
  credits: number
  created_at: string
  updated_at: string
}

export interface User {
  id: string
  email: string
  full_name: string
  role: 'owner' | 'admin' | 'member' | 'viewer'
  organization_id: string
  organization?: Organization
  avatar_url?: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface Company {
  id: string
  name: string
  domain?: string
  industry?: string
  sub_industry?: string
  country?: string
  city?: string
  employee_count?: number
  annual_revenue?: number
  description?: string
  website?: string
  linkedin_url?: string
  phone?: string
  founded_year?: number
  tags: string[]
  status: 'new' | 'contacted' | 'qualified' | 'unqualified' | 'customer'
  organization_id: string
  lead_score?: LeadScore
  created_at: string
  updated_at: string
}

export interface Contact {
  id: string
  first_name: string
  last_name: string
  email?: string
  phone?: string
  title?: string
  department?: string
  linkedin_url?: string
  company_id?: string
  company?: Company
  status: 'new' | 'contacted' | 'qualified' | 'unqualified' | 'customer'
  tags: string[]
  organization_id: string
  lead_score?: LeadScore
  created_at: string
  updated_at: string
}

export interface LeadScore {
  id: string
  entity_type: 'company' | 'contact'
  entity_id: string
  score: number
  grade: 'A' | 'B' | 'C' | 'D' | 'F'
  factors: ScoreFactor[]
  reasoning: string
  generated_at: string
  model_version: string
}

export interface ScoreFactor {
  name: string
  weight: number
  score: number
  description: string
}

// ---- Search ----

export interface Search {
  id: string
  name?: string
  query: string
  filters: SearchFilters
  result_count: number
  organization_id: string
  created_at: string
}

export interface SearchFilters {
  industries?: string[]
  countries?: string[]
  employee_min?: number
  employee_max?: number
  revenue_min?: number
  revenue_max?: number
  keywords?: string[]
}

export interface SearchResult {
  companies: Company[]
  contacts: Contact[]
  total_companies: number
  total_contacts: number
  search_id: string
}

export interface SavedSearch {
  id: string
  name: string
  query: string
  filters: SearchFilters
  organization_id: string
  created_at: string
  updated_at: string
}

// ---- CRM ----

export interface CRMPipeline {
  id: string
  name: string
  stages: CRMStage[]
  organization_id: string
  created_at: string
  updated_at: string
}

export interface CRMStage {
  id: string
  name: string
  order: number
  pipeline_id: string
  color?: string
}

export interface CRMDeal {
  id: string
  title: string
  value?: number
  currency: string
  stage_id: string
  pipeline_id: string
  company_id?: string
  company?: Company
  contact_id?: string
  contact?: Contact
  owner_id?: string
  owner?: User
  close_date?: string
  probability?: number
  notes?: string
  organization_id: string
  created_at: string
  updated_at: string
}

export interface CRMTask {
  id: string
  title: string
  description?: string
  due_date?: string
  completed: boolean
  priority: 'low' | 'medium' | 'high'
  deal_id?: string
  company_id?: string
  contact_id?: string
  assignee_id?: string
  assignee?: User
  organization_id: string
  created_at: string
  updated_at: string
}

// ---- Billing ----

export interface Subscription {
  id: string
  organization_id: string
  plan: 'free' | 'starter' | 'professional' | 'enterprise'
  status: 'active' | 'canceled' | 'past_due' | 'trialing'
  current_period_start: string
  current_period_end: string
  cancel_at_period_end: boolean
  created_at: string
  updated_at: string
}

export interface CreditTransaction {
  id: string
  organization_id: string
  amount: number
  type: 'purchase' | 'usage' | 'refund' | 'bonus'
  description: string
  balance_after: number
  created_at: string
}

// ---- Notifications & Exports ----

export interface Notification {
  id: string
  user_id: string
  title: string
  message: string
  type: 'info' | 'success' | 'warning' | 'error'
  read: boolean
  action_url?: string
  created_at: string
}

export interface Export {
  id: string
  organization_id: string
  user_id: string
  format: 'csv' | 'xlsx' | 'json'
  entity_type: 'companies' | 'contacts'
  filters?: Record<string, unknown>
  status: 'pending' | 'processing' | 'completed' | 'failed'
  file_url?: string
  record_count?: number
  created_at: string
  completed_at?: string
}

// ---- API Helpers ----

export interface ApiResponse<T> {
  data: T
  message?: string
  success: boolean
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  per_page: number
  total_pages: number
}

// ---- Auth ----

export interface LoginRequest {
  email: string
  password: string
}

export interface TokenResponse {
  access_token: string
  refresh_token?: string
  token_type: string
  expires_in: number
  user?: User
}
