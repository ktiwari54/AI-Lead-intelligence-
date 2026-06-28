# 06 — Technical Handoff

**Frontend v3.0** | AI Lead Intelligence Platform | Engineering Implementation Guide

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Folder Structure](#2-folder-structure)
3. [State Management](#3-state-management)
4. [Routing & Middleware](#4-routing--middleware)
5. [API Integration](#5-api-integration)
6. [API Integration Per Screen](#6-api-integration-per-screen)
7. [Authentication Flow](#7-authentication-flow)
8. [Performance](#8-performance)
9. [Accessibility (WCAG 2.1 AA)](#9-accessibility-wcag-21-aa)
10. [Storybook](#10-storybook)
11. [Testing Strategy](#11-testing-strategy)
12. [Build Roadmap](#12-build-roadmap)
13. [Environment Configuration](#13-environment-configuration)
14. [Deployment Checklist](#14-deployment-checklist)

---

## 1. Prerequisites

### Required Tooling

| Tool | Version | Purpose |
|------|---------|---------|
| Node.js | 20 LTS | Runtime |
| npm / pnpm | 9+ / 8+ | Package management |
| TypeScript | 5.x | Type safety |
| Docker | 24+ | Local backend services |

### Local Development Setup

```bash
# Clone and install
cd frontend
npm install

# Environment
cp .env.example .env.local
# Set: NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

# Run dev server
npm run dev          # http://localhost:3000

# Run Storybook
npm run storybook    # http://localhost:6006

# Type check
npm run type-check

# Lint
npm run lint
```

### Key Dependencies

```json
{
  "next": "14.2.x",
  "react": "18.x",
  "typescript": "5.x",
  "@tanstack/react-query": "5.x",
  "@tanstack/react-table": "8.x",
  "@tanstack/react-virtual": "3.x",
  "zustand": "4.x",
  "react-hook-form": "7.x",
  "zod": "3.x",
  "tailwindcss": "3.4.x",
  "lucide-react": "latest",
  "cmdk": "latest",
  "sonner": "latest",
  "recharts": "2.x",
  "framer-motion": "11.x",
  "nuqs": "2.x",
  "@dnd-kit/core": "6.x",
  "axios": "1.x"
}
```

---

## 2. Folder Structure

### Complete Directory Tree

```text
frontend/
├── public/
│   ├── favicon.ico
│   ├── og-image.png
│   └── logos/                    # Integration logos (Salesforce, HubSpot)
│
├── src/
│   ├── app/                      # Next.js App Router
│   │   ├── (auth)/
│   │   │   ├── login/page.tsx
│   │   │   ├── register/page.tsx
│   │   │   ├── forgot-password/page.tsx
│   │   │   ├── reset-password/page.tsx
│   │   │   └── layout.tsx        # Auth layout (centered card)
│   │   │
│   │   ├── (dashboard)/          # Protected routes with AppShell
│   │   │   ├── layout.tsx        # AppShell wrapper + auth guard
│   │   │   ├── dashboard/page.tsx
│   │   │   ├── search/
│   │   │   │   ├── page.tsx
│   │   │   │   ├── results/page.tsx
│   │   │   │   └── saved/page.tsx
│   │   │   ├── lists/
│   │   │   │   ├── page.tsx
│   │   │   │   └── [id]/page.tsx
│   │   │   ├── segments/
│   │   │   │   ├── page.tsx
│   │   │   │   └── [id]/page.tsx
│   │   │   ├── companies/
│   │   │   │   ├── page.tsx
│   │   │   │   ├── new/page.tsx
│   │   │   │   ├── merge/page.tsx
│   │   │   │   └── [id]/
│   │   │   │       ├── page.tsx
│   │   │   │       └── edit/page.tsx
│   │   │   ├── contacts/
│   │   │   │   ├── page.tsx
│   │   │   │   ├── new/page.tsx
│   │   │   │   ├── merge/page.tsx
│   │   │   │   └── [id]/
│   │   │   │       ├── page.tsx
│   │   │   │       └── edit/page.tsx
│   │   │   ├── ai/page.tsx
│   │   │   ├── ai-scoring/page.tsx
│   │   │   ├── crm/
│   │   │   │   ├── page.tsx
│   │   │   │   ├── deals/[id]/page.tsx
│   │   │   │   ├── tasks/page.tsx
│   │   │   │   ├── activities/page.tsx
│   │   │   │   └── calendar/page.tsx
│   │   │   ├── analytics/
│   │   │   │   ├── page.tsx
│   │   │   │   └── [report]/page.tsx
│   │   │   ├── imports/
│   │   │   │   ├── page.tsx
│   │   │   │   ├── new/page.tsx
│   │   │   │   └── [id]/page.tsx
│   │   │   ├── exports/
│   │   │   │   ├── page.tsx
│   │   │   │   └── new/page.tsx
│   │   │   ├── notifications/page.tsx
│   │   │   ├── settings/
│   │   │   │   ├── layout.tsx
│   │   │   │   ├── page.tsx
│   │   │   │   ├── organization/page.tsx
│   │   │   │   ├── users/page.tsx
│   │   │   │   ├── integrations/page.tsx
│   │   │   │   ├── billing/page.tsx
│   │   │   │   └── api-keys/page.tsx
│   │   │   └── admin/
│   │   │       ├── layout.tsx
│   │   │       ├── page.tsx
│   │   │       ├── audit-logs/page.tsx
│   │   │       ├── feature-flags/page.tsx
│   │   │       ├── health/page.tsx
│   │   │       └── connectors/page.tsx
│   │   │
│   │   ├── layout.tsx            # Root: fonts, providers, theme
│   │   ├── globals.css
│   │   ├── not-found.tsx
│   │   ├── error.tsx
│   │   └── loading.tsx
│   │
│   ├── components/
│   │   ├── ui/                   # shadcn/ui primitives
│   │   ├── layout/               # AppShell, Sidebar, TopBar, CommandPalette
│   │   ├── data-table/           # DataTable, EntityDataTable, toolbar
│   │   ├── entity/               # Entity360Layout, EntityHeader, AISummaryPanel
│   │   ├── dashboard/            # DashboardGrid, KpiCard, WidgetCatalog
│   │   ├── charts/               # Recharts wrappers
│   │   ├── enterprise/           # PageHeader, StatusBar, EmptyState, MetricCard
│   │   └── shared/               # Cross-feature utilities
│   │
│   ├── features/                 # Feature modules (colocated logic)
│   │   ├── dashboard/
│   │   │   ├── hooks/useDashboard.ts
│   │   │   └── components/
│   │   ├── discovery/
│   │   │   ├── AISearchBar.tsx
│   │   │   ├── ParsedIntentPreview.tsx
│   │   │   ├── SearchProgress.tsx
│   │   │   ├── FilterBuilder.tsx
│   │   │   └── hooks/useAISearch.ts
│   │   ├── companies/
│   │   │   ├── columns.tsx
│   │   │   ├── schemas/company.schema.ts
│   │   │   └── hooks/useCompanies.ts
│   │   ├── contacts/
│   │   │   ├── columns.tsx
│   │   │   ├── schemas/contact.schema.ts
│   │   │   └── hooks/useContacts.ts
│   │   ├── ai/
│   │   │   ├── AIChat.tsx
│   │   │   ├── AIAssistantDrawer.tsx
│   │   │   └── hooks/useAIChat.ts
│   │   ├── crm/
│   │   │   ├── KanbanBoard.tsx
│   │   │   ├── KanbanColumn.tsx
│   │   │   ├── DealCard.tsx
│   │   │   └── hooks/usePipeline.ts
│   │   ├── imports/
│   │   │   ├── ImportWizard.tsx
│   │   │   └── hooks/useImport.ts
│   │   ├── exports/
│   │   │   ├── ExportWizard.tsx
│   │   │   └── hooks/useExport.ts
│   │   ├── analytics/
│   │   │   └── hooks/useAnalytics.ts
│   │   ├── admin/
│   │   │   └── hooks/useAdmin.ts
│   │   └── settings/
│   │       └── hooks/useSettings.ts
│   │
│   ├── hooks/                    # Shared hooks
│   │   ├── useAuth.ts
│   │   ├── usePermissions.ts
│   │   ├── useDebounce.ts
│   │   ├── useKeyboardShortcut.ts
│   │   ├── useMediaQuery.ts
│   │   ├── useSearch.ts
│   │   ├── useDataTable.ts
│   │   ├── useExports.ts
│   │   └── useAdmin.ts
│   │
│   ├── stores/                   # Zustand stores
│   │   ├── auth-store.ts
│   │   ├── theme-store.ts
│   │   ├── sidebar-store.ts
│   │   ├── command-palette-store.ts
│   │   ├── table-store.ts
│   │   ├── dashboard-store.ts
│   │   ├── ai-assistant-store.ts
│   │   └── keyboard-shortcuts-store.ts
│   │
│   ├── lib/
│   │   ├── api.ts                # Axios instance + interceptors
│   │   ├── auth.ts               # Token storage + refresh
│   │   ├── query-client.ts       # TanStack Query config
│   │   ├── query-keys.ts         # Centralized query key factory
│   │   ├── permissions.ts        # RBAC helpers
│   │   ├── normalize-api.ts      # Response envelope unwrap
│   │   ├── bulk-actions.ts       # Bulk operation helpers
│   │   ├── parse-search-intent.ts
│   │   ├── parse-csv.ts
│   │   └── utils.ts              # cn(), formatters
│   │
│   ├── config/
│   │   └── navigation.ts         # Sidebar + command palette routes
│   │
│   ├── styles/
│   │   └── tokens.css            # Aurora design tokens
│   │
│   ├── types/
│   │   ├── index.ts              # Domain entities
│   │   ├── api.ts                # API response types
│   │   └── table.ts              # Table config types
│   │
│   └── middleware.ts             # Auth route protection
│
├── .storybook/
│   ├── main.ts
│   ├── preview.ts
│   └── decorators/
│
├── components.json               # shadcn/ui config
├── tailwind.config.ts
├── next.config.ts
├── tsconfig.json
└── package.json
```

### Module Boundary Rules

| Rule | Enforcement |
|------|-------------|
| Features import from `components/`, `lib/`, `hooks/`, `types/` | ESLint `import/no-restricted-paths` |
| Features do NOT import from other features | Cross-feature via shared hooks or events |
| `components/ui/` has zero business logic | Code review |
| API calls only in `hooks/` and `lib/api.ts` | No `fetch` in components |
| Types shared via `types/` | No duplicate interfaces |

---

## 3. State Management

### 3.1 Architecture Decision

```text
┌─────────────────────────────────────────────────────────────┐
│                      STATE LAYERS                           │
├─────────────────────────────────────────────────────────────┤
│  Server State (TanStack Query)                              │
│  → API data: companies, contacts, analytics, search results │
├─────────────────────────────────────────────────────────────┤
│  Global UI State (Zustand)                                  │
│  → Shell: sidebar, theme, command palette, keyboard shortcuts│
│  → Feature UI: table views, dashboard layout, AI chat       │
├─────────────────────────────────────────────────────────────┤
│  URL State (nuqs / searchParams)                            │
│  → Filters, pagination, sort, active tab, search ID         │
├─────────────────────────────────────────────────────────────┤
│  Form State (React Hook Form)                               │
│  → Create/edit forms, wizard steps                          │
├─────────────────────────────────────────────────────────────┤
│  Ephemeral State (useState)                                 │
│  → Modal open, dropdown open, hover states                  │
├─────────────────────────────────────────────────────────────┤
│  Persistent Local (Zustand + localStorage)                  │
│  → Theme, recent entities, draft AI messages                │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 TanStack Query Configuration

```typescript
// lib/query-client.ts
import { QueryClient } from '@tanstack/react-query'

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,           // 30s before refetch
      gcTime: 5 * 60_000,          // 5min garbage collection
      retry: 3,
      retryDelay: (attempt) => Math.min(1000 * 2 ** attempt, 30_000),
      refetchOnWindowFocus: true,
      networkMode: 'offlineFirst',
    },
    mutations: {
      retry: 1,
      networkMode: 'offlineFirst',
    },
  },
})
```

### 3.3 Query Key Factory

```typescript
// lib/query-keys.ts
export const queryKeys = {
  companies: {
    all: ['companies'] as const,
    list: (params: CompanyListParams) => ['companies', 'list', params] as const,
    detail: (id: string) => ['companies', 'detail', id] as const,
    timeline: (id: string) => ['companies', 'timeline', id] as const,
    technologies: (id: string) => ['companies', 'technologies', id] as const,
  },
  contacts: {
    all: ['contacts'] as const,
    list: (params: ContactListParams) => ['contacts', 'list', params] as const,
    detail: (id: string) => ['contacts', 'detail', id] as const,
  },
  search: {
    results: (id: string, params?: PaginationParams) => ['search', 'results', id, params] as const,
    saved: ['search', 'saved'] as const,
    history: ['search', 'history'] as const,
  },
  analytics: {
    dashboard: ['analytics', 'dashboard'] as const,
    full: (period: string) => ['analytics', 'full', period] as const,
    report: (type: string, params: ReportParams) => ['analytics', 'report', type, params] as const,
  },
  crm: {
    pipelines: ['crm', 'pipelines'] as const,
    deals: (pipelineId: string) => ['crm', 'deals', pipelineId] as const,
    deal: (id: string) => ['crm', 'deal', id] as const,
    tasks: (params?: TaskParams) => ['crm', 'tasks', params] as const,
    activities: (params?: ActivityParams) => ['crm', 'activities', params] as const,
  },
  ai: {
    recommendations: (entityId?: string) => ['ai', 'recommendations', entityId] as const,
    summary: (entityType: string, entityId: string) => ['ai', 'summary', entityType, entityId] as const,
  },
  imports: {
    list: ['imports'] as const,
    detail: (id: string) => ['imports', 'detail', id] as const,
  },
  exports: {
    list: ['exports'] as const,
    detail: (id: string) => ['exports', 'detail', id] as const,
  },
  notifications: {
    list: (params?: NotificationParams) => ['notifications', 'list', params] as const,
    unreadCount: ['notifications', 'unread-count'] as const,
  },
  admin: {
    overview: ['admin', 'overview'] as const,
    auditLogs: (params: AuditParams) => ['admin', 'audit-logs', params] as const,
    featureFlags: ['admin', 'feature-flags'] as const,
    health: ['admin', 'health'] as const,
  },
  settings: {
    organization: ['settings', 'organization'] as const,
    users: ['settings', 'users'] as const,
    integrations: ['settings', 'integrations'] as const,
    billing: ['settings', 'billing'] as const,
    apiKeys: ['settings', 'api-keys'] as const,
  },
  user: {
    me: ['user', 'me'] as const,
  },
}
```

### 3.4 Zustand Stores

```typescript
// stores/theme-store.ts
interface ThemeStore {
  theme: 'light' | 'dark' | 'system'
  resolvedTheme: 'light' | 'dark'
  setTheme: (theme: Theme) => void
}
// persist: localStorage key 'aurora-theme'

// stores/sidebar-store.ts
interface SidebarStore {
  collapsed: boolean
  mobileOpen: boolean
  toggle: () => void
  setCollapsed: (v: boolean) => void
  setMobileOpen: (v: boolean) => void
}

// stores/command-palette-store.ts
interface CommandPaletteStore {
  open: boolean
  setOpen: (v: boolean) => void
  toggle: () => void
}

// stores/table-store.ts
interface TableStore {
  savedViews: Record<string, SavedView[]>  // keyed by entityType
  activeViewId: Record<string, string>
  columnConfigs: Record<string, ColumnConfig[]>
  setSavedViews: (entityType: string, views: SavedView[]) => void
  setActiveView: (entityType: string, viewId: string) => void
  setColumnConfig: (entityType: string, config: ColumnConfig[]) => void
}
// persist: localStorage key 'aurora-table-views'

// stores/dashboard-store.ts
interface DashboardStore {
  layout: WidgetLayout[]
  editMode: boolean
  dateRange: '7d' | '30d' | '90d' | 'custom'
  setLayout: (layout: WidgetLayout[]) => void
  setEditMode: (v: boolean) => void
  setDateRange: (range: string) => void
}

// stores/ai-assistant-store.ts
interface AIAssistantStore {
  messages: ChatMessage[]
  pinnedChats: PinnedChat[]
  entityContext: EntityContext | null
  drawerOpen: boolean
  addMessage: (message: ChatMessage) => void
  clearMessages: () => void
  setEntityContext: (ctx: EntityContext | null) => void
  setDrawerOpen: (v: boolean) => void
  pinChat: (chat: PinnedChat) => void
}
// persist: messages and pinnedChats to localStorage

// stores/keyboard-shortcuts-store.ts
interface KeyboardShortcutsStore {
  shortcuts: ShortcutDefinition[]
  dialogOpen: boolean
  setDialogOpen: (v: boolean) => void
}
```

### 3.5 Cache Invalidation Map

| Mutation | Invalidates |
|----------|-------------|
| Create company | `companies.list`, `analytics.dashboard` |
| Update company | `companies.detail(id)`, `companies.list` |
| Delete company | `companies.list`, `analytics.dashboard` |
| Score entity | `companies.detail(id)` or `contacts.detail(id)`, `ai.recommendations` |
| Run search | `search.results`, `analytics.dashboard`, `user.me` (credits) |
| Create deal | `crm.deals(pipelineId)`, `analytics.dashboard` |
| Move deal stage | `crm.deals`, `crm.deal(id)` |
| Complete import | `companies.list` or `contacts.list`, `imports.list` |
| Complete export | `exports.list` |
| Update settings | `user.me`, `settings.*` |

---

## 4. Routing & Middleware

### Middleware (`src/middleware.ts`)

```typescript
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

const PUBLIC_ROUTES = ['/login', '/register', '/forgot-password', '/reset-password']
const ADMIN_ROUTES = ['/admin']

export function middleware(request: NextRequest) {
  const token = request.cookies.get('access_token')?.value
  const { pathname } = request.nextUrl

  // Public routes: redirect to dashboard if authenticated
  if (PUBLIC_ROUTES.some(r => pathname.startsWith(r))) {
    if (token) return NextResponse.redirect(new URL('/dashboard', request.url))
    return NextResponse.next()
  }

  // Protected routes: redirect to login if not authenticated
  if (!token) {
    const loginUrl = new URL('/login', request.url)
    loginUrl.searchParams.set('redirect', pathname)
    return NextResponse.redirect(loginUrl)
  }

  // Admin routes: permission check done client-side (admin layout)
  return NextResponse.next()
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico|public).*)'],
}
```

### Root Layout Providers

```tsx
// app/layout.tsx
<html lang="en" suppressHydrationWarning>
  <body>
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        {children}
        <Toaster position="bottom-right" />
      </ThemeProvider>
    </QueryClientProvider>
  </body>
</html>
```

### Dashboard Layout

```tsx
// app/(dashboard)/layout.tsx
export default function DashboardLayout({ children }) {
  return (
    <AuthGuard>
      <AppShell>{children}</AppShell>
    </AuthGuard>
  )
}
```

---

## 5. API Integration

### 5.1 API Client

```typescript
// lib/api.ts
import axios from 'axios'
import { getAccessToken, refreshToken, clearAuth } from './auth'

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  timeout: 30_000,
  headers: { 'Content-Type': 'application/json' },
})

// Request interceptor: attach JWT
api.interceptors.request.use((config) => {
  const token = getAccessToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  config.headers['X-Request-ID'] = crypto.randomUUID()
  return config
})

// Response interceptor: handle 401 refresh, normalize envelope
api.interceptors.response.use(
  (response) => response.data,  // unwrap { success, data } envelope
  async (error) => {
    if (error.response?.status === 401) {
      const refreshed = await refreshToken()
      if (refreshed) return api(error.config)
      clearAuth()
      window.location.href = '/login'
    }
    return Promise.reject(normalizeError(error))
  }
)
```

### 5.2 Response Envelope

```typescript
// lib/normalize-api.ts
interface APIResponse<T> {
  success: boolean
  data: T
  message?: string
  pagination?: PaginationMeta
}

interface APIError {
  code: string
  message: string
  details?: Record<string, string[]>
  request_id?: string
}
```

### 5.3 Hook Pattern

```typescript
// features/companies/hooks/useCompanies.ts
export function useCompanies(params: CompanyListParams) {
  return useQuery({
    queryKey: queryKeys.companies.list(params),
    queryFn: () => api.get('/companies', { params }),
    placeholderData: keepPreviousData,
  })
}

export function useCreateCompany() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: CreateCompanyInput) => api.post('/companies', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.companies.all })
      queryClient.invalidateQueries({ queryKey: queryKeys.analytics.dashboard })
      toast.success('Company created')
    },
    onError: (error: APIError) => toast.error(error.message),
  })
}
```

### 5.4 Credit Cost Constants

```typescript
// lib/constants.ts
export const CREDIT_COSTS = {
  search: 10,
  aiSearch: 10,
  enrichCompany: 3,
  enrichContact: 2,
  score: 1,
  bulkScore: 1,      // per entity
  verifyEmail: 1,
} as const
```

---

## 6. API Integration Per Screen

### Auth

| Screen | Method | Endpoint | Hook |
|--------|--------|----------|------|
| Login | POST | `/auth/login` | `useLogin()` |
| Register | POST | `/auth/register` | `useRegister()` |
| Forgot Password | POST | `/auth/password/forgot` | `useForgotPassword()` |
| Reset Password | POST | `/auth/password/reset` | `useResetPassword()` |
| 2FA | POST | `/auth/2fa/verify` | `use2FAVerify()` |
| OAuth | GET | `/auth/oauth/{provider}` | redirect |

### Dashboard

| Widget/Data | Method | Endpoint | Hook |
|-------------|--------|----------|------|
| KPIs | GET | `/analytics/dashboard` | `useDashboard()` |
| Full analytics | GET | `/analytics/full?period=30d` | `useAnalyticsFull()` |
| Recommendations | GET | `/ai/recommendations` | `useRecommendations()` |
| Connector health | GET | `/connectors/status` | `useConnectorStatus()` |
| Pipeline summary | GET | `/crm/pipelines/{id}/summary` | `usePipelineSummary()` |
| Top companies | GET | `/companies?sort=-lead_score&limit=10` | `useCompanies()` |
| Activity feed | GET | `/notifications?limit=20` | `useNotifications()` |
| Save layout | PATCH | `/users/me` | `useUpdatePreferences()` |

### Lead Discovery

| Action | Method | Endpoint | Hook |
|--------|--------|----------|------|
| Parse NL query | POST | `/search/ai` | `useAISearch()` |
| Execute search | POST | `/search` | `useExecuteSearch()` |
| Get results | GET | `/search/{id}/results` | `useSearchResults()` |
| Poll progress | GET | `/search/{id}/status` | `useSearchStatus()` |
| Save search | POST | `/search/{id}/save` | `useSaveSearch()` |
| List saved | GET | `/search/saved` | `useSavedSearches()` |
| Delete saved | DELETE | `/search/saved/{id}` | `useDeleteSavedSearch()` |
| Search history | GET | `/search/history` | `useSearchHistory()` |

### Companies

| Action | Method | Endpoint | Hook |
|--------|--------|----------|------|
| List | GET | `/companies` | `useCompanies()` |
| Detail | GET | `/companies/{id}` | `useCompany(id)` |
| Create | POST | `/companies` | `useCreateCompany()` |
| Update | PATCH | `/companies/{id}` | `useUpdateCompany()` |
| Delete | DELETE | `/companies/{id}` | `useDeleteCompany()` |
| Bulk delete | DELETE | `/companies` | `useBulkDeleteCompanies()` |
| Merge | POST | `/companies/merge` | `useMergeCompanies()` |
| Timeline | GET | `/companies/{id}/timeline` | `useCompanyTimeline()` |
| Technologies | GET | `/companies/{id}/technologies` | `useCompanyTech()` |
| Enrich | POST | `/enrichment/companies/{id}` | `useEnrichCompany()` |
| Score | POST | `/ai/score` | `useScoreEntity()` |
| CRM sync | POST | `/crm/sync` | `useCRMSync()` |

### Contacts

| Action | Method | Endpoint | Hook |
|--------|--------|----------|------|
| List | GET | `/contacts` | `useContacts()` |
| Detail | GET | `/contacts/{id}` | `useContact(id)` |
| Create | POST | `/contacts` | `useCreateContact()` |
| Update | PATCH | `/contacts/{id}` | `useUpdateContact()` |
| Delete | DELETE | `/contacts/{id}` | `useDeleteContact()` |
| Verify email | POST | `/contacts/verify` | `useVerifyContacts()` |
| Merge | POST | `/contacts/merge` | `useMergeContacts()` |

### AI

| Action | Method | Endpoint | Hook |
|--------|--------|----------|------|
| Chat (NL search) | POST | `/search/ai` | `useAIChat()` |
| Score | POST | `/ai/score` | `useScoreEntity()` |
| Batch score | POST | `/ai/score/batch` | `useBatchScore()` |
| Recommendations | GET | `/ai/recommendations` | `useRecommendations()` |
| Summary | GET | `/ai/summary/{type}/{id}` | `useAISummary()` |

### CRM

| Action | Method | Endpoint | Hook |
|--------|--------|----------|------|
| Pipelines | GET | `/crm/pipelines` | `usePipelines()` |
| Deals | GET | `/crm/deals?pipeline_id=` | `useDeals()` |
| Deal detail | GET | `/crm/deals/{id}` | `useDeal(id)` |
| Create deal | POST | `/crm/deals` | `useCreateDeal()` |
| Update deal | PATCH | `/crm/deals/{id}` | `useUpdateDeal()` |
| Tasks | GET | `/crm/tasks` | `useTasks()` |
| Create task | POST | `/crm/tasks` | `useCreateTask()` |
| Activities | GET | `/crm/activities` | `useActivities()` |

### Analytics

| Action | Method | Endpoint | Hook |
|--------|--------|----------|------|
| Report list | GET | `/analytics/reports` | `useReportList()` |
| Lead velocity | GET | `/analytics/lead-velocity` | `useReport('lead-velocity')` |
| Score distribution | GET | `/analytics/score-distribution` | `useReport('score-distribution')` |
| Industry | GET | `/analytics/industry` | `useReport('industry')` |
| Geographic | GET | `/analytics/geographic` | `useReport('geographic')` |
| Connectors | GET | `/analytics/connectors` | `useReport('connectors')` |
| Search analytics | GET | `/analytics/search` | `useReport('search')` |

### Data Ops

| Action | Method | Endpoint | Hook |
|--------|--------|----------|------|
| List imports | GET | `/imports` | `useImports()` |
| Upload file | POST | `/imports/upload` | `useUploadImport()` |
| Get columns | GET | `/imports/{id}/columns` | `useImportColumns()` |
| Validate | POST | `/imports/{id}/validate` | `useValidateImport()` |
| Execute | POST | `/imports/{id}/execute` | `useExecuteImport()` |
| Poll status | GET | `/imports/{id}` | `useImportStatus()` |
| List exports | GET | `/exports` | `useExports()` |
| Create export | POST | `/exports` | `useCreateExport()` |
| Poll/download | GET | `/exports/{id}` | `useExportStatus()` |

### Settings

| Action | Method | Endpoint | Hook |
|--------|--------|----------|------|
| Current user | GET | `/users/me` | `useCurrentUser()` |
| Update profile | PATCH | `/users/me` | `useUpdateProfile()` |
| Organization | GET/PATCH | `/organizations/current` | `useOrganization()` |
| Users | GET/POST/PATCH/DELETE | `/users/*` | `useUsers()` |
| Integrations | GET/POST/DELETE | `/integrations/*` | `useIntegrations()` |
| Billing | GET | `/billing/subscription` | `useBilling()` |
| Purchase credits | POST | `/billing/purchase-credits` | `usePurchaseCredits()` |
| API keys | GET/POST/DELETE | `/api-keys/*` | `useAPIKeys()` |

### Admin

| Action | Method | Endpoint | Hook |
|--------|--------|----------|------|
| Overview | GET | `/admin/overview` | `useAdminOverview()` |
| Audit logs | GET | `/admin/audit-logs` | `useAuditLogs()` |
| Feature flags | GET/PATCH | `/admin/feature-flags/*` | `useFeatureFlags()` |
| System health | GET | `/admin/health` | `useSystemHealth()` |
| Connectors | GET/PATCH | `/connectors/*` | `useConnectors()` |

### Notifications

| Action | Method | Endpoint | Hook |
|--------|--------|----------|------|
| List | GET | `/notifications` | `useNotifications()` |
| Unread count | GET | `/notifications/unread-count` | `useUnreadCount()` |
| Mark read | PATCH | `/notifications/{id}/read` | `useMarkRead()` |
| Mark all read | PATCH | `/notifications/read-all` | `useMarkAllRead()` |

---

## 7. Authentication Flow

```text
1. User submits login form
2. POST /auth/login → { access_token, refresh_token }
3. Store tokens: access in memory + httpOnly cookie, refresh in httpOnly cookie
4. Fetch GET /users/me → populate auth-store (user, org, permissions)
5. Redirect to /dashboard or ?redirect param

Token refresh:
1. API returns 401
2. POST /auth/refresh with refresh_token cookie
3. Receive new token pair (rotation)
4. Retry original request
5. If refresh fails → clear auth → redirect /login

Logout:
1. POST /auth/logout with refresh_token
2. Clear cookies + auth-store
3. queryClient.clear()
4. Redirect /login
```

---

## 8. Performance

### 8.1 Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| LCP (Largest Contentful Paint) | < 2.5s | Lighthouse |
| FID (First Input Delay) | < 100ms | Lighthouse |
| CLS (Cumulative Layout Shift) | < 0.1 | Lighthouse |
| TTI (Time to Interactive) | < 3.5s | Lighthouse |
| Table render (10K rows) | < 100ms | React Profiler |
| Table scroll FPS | 60fps | Chrome DevTools |
| API response rendering | < 200ms after data | Profiler |
| Bundle size (initial) | < 250KB gzipped | `next build` analysis |
| Route transition | < 300ms | User perception |

### 8.2 Optimization Strategies

| Strategy | Implementation |
|----------|----------------|
| **Code splitting** | `next/dynamic` for charts, kanban, AI chat, import wizard |
| **Server Components** | Page shells, static headers, breadcrumb data |
| **Virtual scrolling** | `@tanstack/react-virtual` in `DataTable` for >100 rows |
| **Query caching** | `staleTime: 30s`, `placeholderData: keepPreviousData` for tables |
| **Image optimization** | `next/image` for logos/avatars, Clearbit CDN with fallback |
| **Font optimization** | `next/font` for Inter + JetBrains Mono, `display: swap` |
| **Prefetching** | `queryClient.prefetchQuery` on sidebar link hover |
| **Debouncing** | Search: 200ms, AI parse: 500ms, filters: 300ms |
| **Pagination** | Server-side default; cursor-based for search results >10K |
| **Optimistic updates** | Kanban drag, task toggle, notification read |
| **Request dedup** | TanStack Query automatic deduplication |
| **Bundle analysis** | `@next/bundle-analyzer` in CI |

### 8.3 Dynamic Imports

```typescript
const KanbanBoard = dynamic(() => import('@/features/crm/KanbanBoard'), {
  loading: () => <KanbanSkeleton />,
  ssr: false,
})

const AIChat = dynamic(() => import('@/features/ai/AIChat'), {
  loading: () => <ChatSkeleton />,
})

const ImportWizard = dynamic(() => import('@/features/imports/ImportWizard'), {
  loading: () => <WizardSkeleton />,
})
```

### 8.4 Data Table Performance

```typescript
// Virtualization config
const rowVirtualizer = useVirtualizer({
  count: rows.length,
  getScrollElement: () => tableContainerRef.current,
  estimateSize: () => 48,        // row height px
  overscan: 10,                   // render 10 extra rows
})

// Target: 10,000 rows at 60fps scroll
// Column resize: CSS transform, no layout reflow
// Sort/filter: server-side, no client-side full dataset
```

---

## 9. Accessibility (WCAG 2.1 AA)

### 9.1 Compliance Checklist

| Criterion | Requirement | Implementation |
|-----------|-------------|----------------|
| **1.1.1** Non-text Content | Alt text on images | `alt` on Avatar, company logos |
| **1.3.1** Info and Relationships | Semantic HTML | `<main>`, `<nav>`, `<table>`, `<th scope>` |
| **1.4.3** Contrast (Minimum) | 4.5:1 text, 3:1 large | Aurora tokens verified (see 03-design-system) |
| **1.4.11** Non-text Contrast | 3:1 UI components | Focus rings, borders, icons |
| **2.1.1** Keyboard | All functionality via keyboard | See 05 §7 shortcut map |
| **2.1.2** No Keyboard Trap | Focus can escape modals | Radix focus trap with Esc |
| **2.4.1** Bypass Blocks | Skip to content | Skip link: `<a href="#main-content" class="sr-only focus:not-sr-only">` |
| **2.4.3** Focus Order | Logical tab order | DOM order matches visual order |
| **2.4.7** Focus Visible | Visible focus indicator | `ring-2 ring-ring ring-offset-2` on all interactives |
| **2.5.5** Target Size | 44×44px minimum | Mobile buttons, table checkboxes |
| **3.3.1** Error Identification | Errors described in text | Form field errors with `aria-describedby` |
| **3.3.2** Labels or Instructions | Form labels | `<label htmlFor>` on all inputs |
| **4.1.2** Name, Role, Value | ARIA on custom widgets | Radix primitives handle role/state |

### 9.2 ARIA Patterns

| Component | ARIA |
|-----------|------|
| Sidebar nav | `<nav aria-label="Main navigation">` |
| Data table | `<table role="grid" aria-label="Companies">` |
| Sort header | `aria-sort="ascending\|descending\|none"` |
| Command palette | `role="combobox"`, `aria-expanded`, `aria-activedescendant` |
| Score gauge | `role="meter"`, `aria-valuenow`, `aria-valuemin="0"`, `aria-valuemax="100"` |
| Toast | `role="status"`, `aria-live="polite"` |
| Loading | `aria-busy="true"`, `aria-label="Loading companies"` |
| Tabs | Radix `Tabs` with `role="tablist"`, `role="tab"`, `role="tabpanel"` |
| Kanban | `aria-dnd` via `@dnd-kit` accessibility plugin |
| Progress | `role="progressbar"`, `aria-valuenow`, `aria-valuemin`, `aria-valuemax` |

### 9.3 Screen Reader Announcements

```typescript
// lib/announcer.ts — live region for dynamic updates
export function announce(message: string, priority: 'polite' | 'assertive' = 'polite') {
  const el = document.getElementById('sr-announcer')
  if (el) {
    el.setAttribute('aria-live', priority)
    el.textContent = message
  }
}

// Usage:
announce('12 companies selected')
announce('Search complete. 42 results found.')
announce('Error: Failed to save changes.', 'assertive')
```

### 9.4 Focus Management

| Action | Focus Behavior |
|--------|----------------|
| Open modal | Focus first focusable element in modal |
| Close modal | Return focus to trigger element |
| Open command palette | Focus search input |
| Close command palette | Return focus to trigger |
| Delete row | Focus next row (or previous if last) |
| Navigate to 360° | Focus main content heading |
| Tab switch | Focus tab panel content |
| Toast appears | No focus steal (polite live region) |

### 9.5 Accessibility Testing

| Tool | Usage |
|------|-------|
| axe-core | Automated CI check via `@axe-core/playwright` |
| Lighthouse | Performance + a11y audit per sprint |
| NVDA / VoiceOver | Manual screen reader testing |
| Keyboard-only | Manual tab-through of all flows |
| `prefers-reduced-motion` | Verify all animations disabled |
| `prefers-contrast: more` | Verify high contrast mode |
| Color blindness simulator | Chart palette verification |

---

## 10. Storybook

### 10.1 Setup

```typescript
// .storybook/main.ts
import type { StorybookConfig } from '@storybook/nextjs'

const config: StorybookConfig = {
  stories: ['../src/**/*.stories.@(ts|tsx)'],
  addons: [
    '@storybook/addon-essentials',
    '@storybook/addon-a11y',
    '@storybook/addon-themes',
    '@chromatic-com/storybook',
  ],
  framework: '@storybook/nextjs',
  staticDirs: ['../public'],
}
```

### 10.2 Global Decorators

```typescript
// .storybook/preview.ts
import { withTheme } from './decorators/withTheme'
import { withQueryClient } from './decorators/withQueryClient'

export const decorators = [withTheme, withQueryClient]

export const parameters = {
  a11y: { test: 'todo' },  // 'error' in CI
  themes: {
    default: 'light',
    list: [
      { name: 'light', class: 'light', color: '#F8FAFC' },
      { name: 'dark', class: 'dark', color: '#09090B' },
    ],
  },
}
```

### 10.3 Story File Convention

```typescript
// src/components/ui/Button.stories.tsx
import type { Meta, StoryObj } from '@storybook/react'
import { Button } from './Button'

const meta: Meta<typeof Button> = {
  title: 'Primitives/Button',
  component: Button,
  tags: ['autodocs'],
  argTypes: {
    variant: { control: 'select', options: ['default', 'destructive', 'outline', 'secondary', 'ghost', 'link'] },
    size: { control: 'select', options: ['default', 'sm', 'lg', 'icon'] },
  },
}
export default meta
type Story = StoryObj<typeof Button>

export const Default: Story = { args: { children: 'Button' } }
export const Loading: Story = { args: { children: 'Saving...', loading: true } }
export const Disabled: Story = { args: { children: 'Disabled', disabled: true } }
export const Destructive: Story = { args: { children: 'Delete', variant: 'destructive' } }
```

### 10.4 Priority Stories (Sprint 1)

| Component | Stories Required |
|-----------|-----------------|
| Button | All variants × sizes × states |
| Input | Default, error, disabled, with icons |
| DataTable | Empty, loading, 5 rows, 100 rows virtualized, selected |
| ScoreGauge | Scores: 0, 25, 50, 75, 95; circular + linear |
| KpiCard | With trend up/down, with sparkline, loading |
| EmptyState | All variants (see 05 §4.2) |
| AISearchBar | Idle, parsing, with intent |
| KanbanBoard | 4 columns, 3 deals each, empty column |
| Entity360Layout | Company mock, contact mock |
| CommandPalette | Navigation, actions, search groups |

### 10.5 Chromatic Visual Regression

- Run on every PR via GitHub Actions
- Baseline: `main` branch
- Review UI for: theme changes, component refactors, responsive breakpoints
- Threshold: 0.1% pixel diff tolerance

---

## 11. Testing Strategy

### 11.1 Test Pyramid

| Level | Tool | Coverage Target | Scope |
|-------|------|-----------------|-------|
| Unit | Vitest | 80% utils/hooks | `lib/`, `hooks/`, `stores/` |
| Component | Vitest + Testing Library | 70% components | `components/`, `features/` |
| Integration | Vitest + MSW | Key flows | Hook + API mock |
| E2E | Playwright | Critical paths | Full user journeys |
| Visual | Chromatic | All Storybook stories | Regression |
| A11y | axe-core | All pages | WCAG AA |

### 11.2 E2E Critical Paths

| Test | Steps |
|------|-------|
| Login → Dashboard | Login, verify KPIs render |
| AI Search → Results | NL query, confirm intent, view results |
| Create Company | Form fill, submit, verify in list |
| Company 360° | Open from list, verify tabs, score |
| Import CSV | Upload, map, preview, execute, verify |
| CRM drag | Create deal, drag to next stage |
| Command palette | Open, navigate to Companies |
| Dark mode toggle | Toggle, verify theme class |
| Bulk select + export | Select 3, export, verify toast |

### 11.3 MSW Mock Handlers

```typescript
// mocks/handlers.ts
export const handlers = [
  http.get('/api/v1/companies', () => HttpResponse.json({ data: mockCompanies, pagination })),
  http.post('/api/v1/search/ai', () => HttpResponse.json({ data: mockParsedIntent })),
  http.get('/api/v1/analytics/dashboard', () => HttpResponse.json({ data: mockDashboard })),
  // ... all endpoints for offline development
]
```

---

## 12. Build Roadmap

### Sprint 1 (Weeks 1–2): Foundation

| Task | Owner | Done When |
|------|-------|-----------|
| Aurora tokens finalization in `tokens.css` + Tailwind config | DS | All semantic colors mapped |
| shadcn/ui install: Button, Input, Card, Dialog, Tabs, Select, etc. | FE | 15+ primitives in `components/ui/` |
| `AppShell` + `Sidebar` + `TopBar` + `StatusBar` | FE | Responsive shell renders |
| `theme-store` + dark/light/system toggle | FE | Theme persists across refresh |
| `command-palette-store` + `CommandPalette` with cmdk | FE | ⌘K opens, navigates |
| `middleware.ts` auth guard | FE | Unauthenticated → /login |
| Auth pages (login, register) | FE | JWT flow works E2E |
| `api.ts` client + interceptors | FE | 401 refresh works |
| `query-client.ts` + provider in root layout | FE | Queries execute |
| Storybook setup + Button/Input stories | FE | `npm run storybook` works |

### Sprint 2 (Weeks 3–4): Data & Entities

| Task | Done When |
|------|-----------|
| `DataTable` + virtualization | 10K rows at 60fps |
| `EntityDataTable` + `DataTableToolbar` | Column config, sort, filter |
| `table-store` + saved views | Views persist per user |
| `BulkActionBar` + bulk API calls | Select + score 10 companies |
| Company list page with full table | CRUD from list |
| Contact list page | Same feature parity |
| `Entity360Layout` + `EntityHeader` | Company 360° renders |
| `AISummaryPanel` | AI summary loads |
| Company 360° all 6 tabs | Each tab fetches data |
| Contact 360° all 5 tabs | Each tab fetches data |
| `GlobalSearch` in TopBar | Keyword search works |
| `PageHeader` + `EmptyState` | Used on all list pages |

### Sprint 3 (Weeks 5–6): Discovery

| Task | Done When |
|------|-----------|
| `AISearchBar` + `ParsedIntentPreview` | NL → intent preview |
| `FilterBuilder` | Advanced filters work |
| `SearchProgress` | Connector progress displays |
| Lead Discovery page complete | Full search flow |
| Search Results page | Table + bulk actions |
| Saved Searches page | CRUD saved searches |
| Lists Hub + List Detail | Add/remove entities |
| Segments Hub + Segment Detail | Rule builder works |
| Search history (local + API) | Recent queries shown |
| Credit cost display + 402 handling | Insufficient credits dialog |

### Sprint 4 (Weeks 7–8): CRM & AI

| Task | Done When |
|------|-----------|
| `KanbanBoard` + drag-and-drop | Move deals between stages |
| `DealCard` + Deal Detail page | Full deal CRUD |
| Tasks page | Create, complete, filter |
| Activities page | Chronological feed |
| Calendar page | Month view with events |
| `AIChat` full page | Chat with AI responses |
| `AIAssistantDrawer` | Opens from 360° with context |
| Lead Scoring dashboard | Distribution charts + batch score |
| `ImportWizard` 4-step flow | CSV import works E2E |
| `ExportWizard` 3-step flow | CSV export downloads |

### Sprint 5 (Weeks 9–10): Polish & Ship

| Task | Done When |
|------|-----------|
| `DashboardGrid` + widget catalog | Customizable dashboard |
| All 6 analytics reports | Charts render with data |
| Admin panel (5 sub-pages) | Audit, flags, health, connectors |
| Settings (6 sub-pages) | All forms save |
| Notifications center | Read, mark read, preferences |
| Developer portal + webhooks | API docs render |
| Keyboard shortcuts (all maps) | `?` dialog complete |
| WCAG AA audit + fixes | axe-core 0 violations on critical paths |
| Performance audit | Lighthouse ≥90 performance |
| E2E test suite (9 paths) | All Playwright tests pass |
| Storybook complete (50+ stories) | Chromatic baselines set |
| Error/empty/loading states audit | Every screen has all states |
| Mobile responsive pass | All breakpoints tested |
| Production build + deploy | `next build` succeeds, deployed |

---

## 13. Environment Configuration

### Environment Variables

```bash
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_APP_URL=http://localhost:3000
NEXT_PUBLIC_ENV=development

# Optional
NEXT_PUBLIC_MAPBOX_TOKEN=           # Geographic analytics map
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY= # Billing
NEXT_PUBLIC_SENTRY_DSN=           # Error tracking
NEXT_PUBLIC_ANALYTICS_ID=           # Usage analytics
```

### Next.js Config

```typescript
// next.config.ts
const nextConfig = {
  images: {
    remotePatterns: [
      { hostname: 'logo.clearbit.com' },
      { hostname: 'avatars.githubusercontent.com' },
    ],
  },
  experimental: {
    optimizePackageImports: ['lucide-react', 'recharts'],
  },
}
```

---

## 14. Deployment Checklist

| Step | Verification |
|------|-------------|
| `npm run type-check` | 0 errors |
| `npm run lint` | 0 errors |
| `npm run test` | All pass |
| `npm run test:e2e` | Critical paths pass |
| `npm run build` | Successful, no warnings |
| Lighthouse audit | Performance ≥90, A11y ≥95 |
| axe-core scan | 0 critical violations |
| Bundle size check | Initial < 250KB gzipped |
| Environment variables set in production | All `NEXT_PUBLIC_*` configured |
| CORS configured on API | Frontend origin whitelisted |
| Cookie settings | `Secure`, `SameSite=Lax`, `httpOnly` for tokens |
| CSP headers configured | No unsafe-inline scripts |
| Error tracking live | Sentry receiving events |
| Chromatic baselines updated | Visual regression current |

---

*End of Frontend v3.0 Technical Handoff*

*Return to [README.md](./README.md) for document index.*