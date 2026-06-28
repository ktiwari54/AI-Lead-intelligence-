# Phase 4 — Implementation Guide & Developer Handoff

**Version 1.0** | Production implementation reference for frontend engineering.

---

## Table of Contents

1. [Folder Structure](#1-folder-structure)
2. [State Management](#2-state-management)
3. [Routing](#3-routing)
4. [API Integration](#4-api-integration)
5. [Accessibility](#5-accessibility)
6. [Performance](#6-performance)
7. [Testing](#7-testing)
8. [UI Implementation Guide](#8-ui-implementation-guide)
9. [Developer Handoff](#9-developer-handoff)

---

## 1. Folder Structure

### Target Structure

```text
frontend/
├── public/
│   ├── favicon.ico
│   └── og-image.png
│
├── src/
│   ├── app/                          # Next.js App Router
│   │   ├── (auth)/
│   │   │   ├── login/page.tsx
│   │   │   ├── register/page.tsx
│   │   │   └── layout.tsx
│   │   ├── (app)/                    # Authenticated app shell
│   │   │   ├── layout.tsx            # AppShell wrapper
│   │   │   ├── dashboard/page.tsx
│   │   │   ├── discover/
│   │   │   │   ├── page.tsx
│   │   │   │   ├── saved/page.tsx
│   │   │   │   ├── lists/page.tsx
│   │   │   │   └── segments/page.tsx
│   │   │   ├── companies/
│   │   │   │   ├── page.tsx
│   │   │   │   ├── [id]/page.tsx
│   │   │   │   └── new/page.tsx
│   │   │   ├── contacts/
│   │   │   │   ├── page.tsx
│   │   │   │   └── [id]/page.tsx
│   │   │   ├── ai/
│   │   │   │   ├── page.tsx
│   │   │   │   └── scoring/page.tsx
│   │   │   ├── crm/
│   │   │   │   ├── page.tsx
│   │   │   │   ├── deals/[id]/page.tsx
│   │   │   │   ├── tasks/page.tsx
│   │   │   │   └── calendar/page.tsx
│   │   │   ├── analytics/
│   │   │   │   ├── page.tsx
│   │   │   │   └── [report]/page.tsx
│   │   │   ├── imports/
│   │   │   ├── exports/
│   │   │   ├── notifications/page.tsx
│   │   │   └── settings/
│   │   │       ├── layout.tsx        # Settings sidebar
│   │   │       ├── organization/page.tsx
│   │   │       ├── users/page.tsx
│   │   │       ├── billing/page.tsx
│   │   │       └── profile/page.tsx
│   │   ├── (admin)/
│   │   │   ├── layout.tsx            # Admin guard
│   │   │   └── admin/
│   │   ├── developer/page.tsx
│   │   ├── layout.tsx                # Root: providers, theme
│   │   ├── globals.css
│   │   ├── not-found.tsx
│   │   └── error.tsx
│   │
│   ├── components/
│   │   ├── ui/                       # shadcn/ui primitives
│   │   ├── layout/                   # AppShell, Sidebar, TopBar
│   │   ├── data-table/               # DataTable system
│   │   ├── charts/                   # Recharts wrappers
│   │   └── shared/                   # Cross-feature components
│   │
│   ├── features/                     # Feature modules
│   │   ├── dashboard/
│   │   ├── discover/
│   │   ├── companies/
│   │   ├── contacts/
│   │   ├── ai/
│   │   ├── crm/
│   │   ├── imports/
│   │   ├── exports/
│   │   ├── analytics/
│   │   ├── admin/
│   │   └── settings/
│   │
│   ├── hooks/                        # Shared hooks
│   │   ├── useAuth.ts
│   │   ├── usePermissions.ts
│   │   ├── useDebounce.ts
│   │   ├── useKeyboardShortcut.ts
│   │   └── useMediaQuery.ts
│   │
│   ├── stores/                       # Zustand stores
│   │   ├── auth-store.ts
│   │   ├── theme-store.ts
│   │   ├── sidebar-store.ts
│   │   ├── command-palette-store.ts
│   │   ├── table-store.ts
│   │   ├── ai-chat-store.ts
│   │   └── notification-store.ts
│   │
│   ├── lib/
│   │   ├── api.ts                    # Axios client + interceptors
│   │   ├── auth.ts                   # Token management
│   │   ├── query-client.ts           # TanStack Query config
│   │   ├── permissions.ts            # RBAC helpers
│   │   └── utils.ts                  # cn(), formatters
│   │
│   ├── styles/
│   │   └── tokens.css                # Design tokens
│   │
│   └── types/
│       ├── api.ts                    # API response types
│       ├── entities.ts               # Domain types
│       └── table.ts                  # Table config types
│
├── components.json                   # shadcn/ui config
├── tailwind.config.ts
├── next.config.ts
└── package.json
```

### Migration from Current Structure

| Current | Target | Action |
|---------|--------|--------|
| `(dashboard)/` | `(app)/` | Rename route group |
| `src/hooks/use*.ts` | `src/features/*/hooks/` | Move per feature |
| `src/components/ui/` | Keep + migrate to shadcn | Replace custom with shadcn |
| `@heroicons/react` | `lucide-react` | Icon migration |
| `@headlessui/react` | Radix via shadcn | Component migration |
| No Zustand | `src/stores/` | Add stores |

---

## 2. State Management

### State Categories

| Category | Tool | Examples |
|----------|------|----------|
| Server state | TanStack Query | Companies, contacts, analytics |
| Global UI | Zustand | Sidebar, theme, command palette |
| Form state | React Hook Form | Create/edit forms |
| URL state | `nuqs` or searchParams | Filters, pagination, tabs |
| Ephemeral | `useState` | Modals, dropdowns |
| Persistent local | localStorage via Zustand persist | Theme, table views, widget layout |

### Zustand Stores

```typescript
// stores/auth-store.ts
interface AuthStore {
  user: User | null
  organization: Organization | null
  permissions: string[]
  setAuth: (user: User, org: Organization) => void
  clearAuth: () => void
  hasPermission: (perm: string) => boolean
}

// stores/theme-store.ts
interface ThemeStore {
  theme: 'light' | 'dark' | 'system'
  resolvedTheme: 'light' | 'dark'
  setTheme: (theme: Theme) => void
}

// stores/sidebar-store.ts
interface SidebarStore {
  collapsed: boolean
  mobileOpen: boolean
  toggle: () => void
  setCollapsed: (v: boolean) => void
}

// stores/command-palette-store.ts
interface CommandPaletteStore {
  open: boolean
  setOpen: (v: boolean) => void
  toggle: () => void
}

// stores/table-store.ts
interface TableStore {
  savedViews: Record<string, SavedView[]>
  addView: (entityType: string, view: SavedView) => void
  removeView: (entityType: string, id: string) => void
}
// persist: localStorage key 'ali-table-views'

// stores/ai-chat-store.ts
interface AIChatStore {
  conversations: Conversation[]
  activeId: string | null
  pinnedIds: string[]
  entityContext: { type: string; id: string } | null
  addMessage: (conversationId: string, msg: Message) => void
  pinConversation: (id: string) => void
  setEntityContext: (ctx: EntityContext | null) => void
}

// stores/notification-store.ts
interface NotificationStore {
  unreadCount: number
  setUnreadCount: (n: number) => void
  decrementUnread: () => void
}
```

### TanStack Query Key Convention

```typescript
// lib/query-keys.ts
export const queryKeys = {
  companies: {
    all: ['companies'] as const,
    list: (filters: CompanyFilters) => ['companies', 'list', filters] as const,
    detail: (id: string) => ['companies', 'detail', id] as const,
    intelligence: (id: string) => ['companies', 'intelligence', id] as const,
  },
  contacts: {
    all: ['contacts'] as const,
    list: (filters: ContactFilters) => ['contacts', 'list', filters] as const,
    detail: (id: string) => ['contacts', 'detail', id] as const,
  },
  search: {
    ai: (id: string) => ['search', 'ai', id] as const,
    saved: ['search', 'saved'] as const,
    history: ['search', 'history'] as const,
  },
  analytics: {
    dashboard: ['analytics', 'dashboard'] as const,
    report: (type: string) => ['analytics', 'report', type] as const,
  },
}
```

### Query Defaults

```typescript
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60_000,
      gcTime: 5 * 60_000,
      refetchOnWindowFocus: false,
      retry: (count, error) => {
        if (error.status === 401 || error.status === 403) return false
        return count < 2
      },
    },
    mutations: {
      onError: (error) => toast.error(error.message),
    },
  },
})
```

---

## 3. Routing

### Route Protection

```typescript
// middleware.ts
export function middleware(request: NextRequest) {
  const token = request.cookies.get('access_token')?.value
  const isAuthPage = request.nextUrl.pathname.startsWith('/login')
  const isPublic = PUBLIC_ROUTES.includes(request.nextUrl.pathname)

  if (!token && !isPublic) {
    return NextResponse.redirect(new URL('/login', request.url))
  }
  if (token && isAuthPage) {
    return NextResponse.redirect(new URL('/dashboard', request.url))
  }
  return NextResponse.next()
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
}
```

### Layout Nesting

```text
RootLayout (providers: Query, Theme, Toaster)
  └── (auth)/layout.tsx (centered card)
  └── (app)/layout.tsx (AppShell + auth guard)
        └── page.tsx
  └── (admin)/layout.tsx (AppShell + admin permission guard)
  └── settings/layout.tsx (settings sidebar)
```

### Error & Loading

| File | Scope | Behavior |
|------|-------|----------|
| `app/loading.tsx` | Root | Full-page skeleton |
| `app/error.tsx` | Root | Error boundary with retry |
| `app/not-found.tsx` | 404 | Custom 404 page |
| `app/(app)/companies/loading.tsx` | Companies | Table skeleton |
| `app/(app)/companies/[id]/loading.tsx` | 360° | Header + tab skeleton |

### Dynamic Route Params

```typescript
// companies/[id]/page.tsx
interface PageProps {
  params: { id: string }
  searchParams: { tab?: string }
}
```

---

## 4. API Integration

### Client Architecture

```typescript
// lib/api.ts
class APIClient {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: process.env.NEXT_PUBLIC_API_URL,
      timeout: 30_000,
    })
    this.setupInterceptors()
  }

  private setupInterceptors() {
    // Request: attach JWT from memory (not localStorage for XSS safety)
    // Response: handle 401 → refresh token → retry
    // Response: normalize APIResponse<T> envelope
  }

  async get<T>(url: string, params?: object): Promise<T> { ... }
  async post<T>(url: string, data?: unknown): Promise<T> { ... }
}
```

### JWT Storage Strategy

| Token | Storage | Reason |
|-------|---------|--------|
| Access token | Memory (Zustand) + httpOnly cookie (preferred) | XSS protection |
| Refresh token | httpOnly secure cookie | Never in JS |
| User profile | Zustand (non-sensitive) | Fast access |

**Dev fallback:** `sessionStorage` for access token when httpOnly cookies not configured.

### Response Normalization

```typescript
interface APIResponse<T> {
  success: boolean
  data: T
  message?: string
  pagination?: PaginationMeta
}

// lib/api.ts unwraps:
async function unwrap<T>(promise: Promise<AxiosResponse<APIResponse<T>>>): Promise<T> {
  const { data } = await promise
  if (!data.success) throw new APIError(data.error)
  return data.data
}
```

### Optimistic Updates

```typescript
// Example: mark notification as read
useMutation({
  mutationFn: (ids: string[]) => api.post('/notifications/mark-read', { notification_ids: ids }),
  onMutate: async (ids) => {
    await queryClient.cancelQueries({ queryKey: ['notifications'] })
    const previous = queryClient.getQueryData(['notifications'])
    queryClient.setQueryData(['notifications'], (old) =>
      old.map(n => ids.includes(n.id) ? { ...n, is_read: true } : n)
    )
    return { previous }
  },
  onError: (err, ids, context) => {
    queryClient.setQueryData(['notifications'], context.previous)
  },
})
```

### WebSocket (Notifications)

```typescript
// hooks/useNotificationSocket.ts
function useNotificationSocket() {
  const token = useAuthStore(s => s.accessToken)
  useEffect(() => {
    const ws = new WebSocket(`${WS_URL}/notifications/ws?token=${token}`)
    ws.onmessage = (event) => {
      const notification = JSON.parse(event.data)
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
      toast.info(notification.data.title)
    }
    return () => ws.close()
  }, [token])
}
```

---

## 5. Accessibility

### WCAG AA Checklist

| Requirement | Implementation | Status |
|-------------|----------------|--------|
| Color contrast 4.5:1 | Token pairs verified | Required |
| Focus visible | `ring-2 ring-ring` on all interactive | Required |
| Keyboard navigation | Tab order, arrow keys in tables/menus | Required |
| ARIA labels | All icon-only buttons labeled | Required |
| Screen reader | Semantic HTML, `aria-live` for toasts | Required |
| Skip link | "Skip to main content" in AppShell | Required |
| Form labels | Every input has associated `<label>` | Required |
| Error identification | `aria-invalid` + `aria-describedby` | Required |
| Touch targets 44px | Mobile button/table row sizing | Required |
| Reduced motion | `prefers-reduced-motion` respected | Required |
| Color blind | Don't rely on color alone; use icons | Required |
| High contrast | `prefers-contrast: more` overrides | Required |

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `⌘K` / `Ctrl+K` | Open command palette |
| `⌘B` / `Ctrl+B` | Toggle sidebar |
| `⌘/` | Focus global search |
| `⌘N` | New record (context-aware) |
| `Esc` | Close modal/palette/drawer |
| `?` | Show keyboard shortcuts dialog |
| `G then D` | Go to Dashboard |
| `G then C` | Go to Companies |
| `G then S` | Go to Lead Discovery |

### Focus Management

- Command palette: focus input on open, trap focus
- Modal: focus first interactive element, restore on close
- Drawer: focus trap within drawer
- Route change: focus main content heading

---

## 6. Performance

### Optimization Plan

| Technique | Application |
|-----------|-------------|
| Code splitting | `next/dynamic` for charts, maps, kanban |
| Server Components | Static layouts, metadata, initial data |
| Streaming | `Suspense` boundaries per widget |
| Virtual scrolling | `@tanstack/react-virtual` in all tables |
| Image optimization | `next/image` for logos, avatars |
| Font optimization | `next/font` for Inter, JetBrains Mono |
| Bundle analysis | `@next/bundle-analyzer` in CI |
| Prefetching | `queryClient.prefetchQuery` on nav hover |
| Debouncing | Search: 200ms, filters: 300ms |
| Caching | TanStack Query staleTime per data type |

### Lazy Load Targets

```typescript
const KanbanBoard = dynamic(() => import('@/features/crm/components/KanbanBoard'), {
  loading: () => <KanbanSkeleton />,
  ssr: false,
})

const MapWidget = dynamic(() => import('@/components/charts/MapWidget'), {
  loading: () => <Skeleton className="h-64" />,
  ssr: false,
})

const AIChat = dynamic(() => import('@/features/ai/components/AIChat'), {
  loading: () => <ChatSkeleton />,
})
```

### Performance Budgets

| Metric | Target |
|--------|--------|
| LCP | < 2.5s |
| FID | < 100ms |
| CLS | < 0.1 |
| Bundle (initial) | < 200KB gzipped |
| Bundle (per route) | < 100KB gzipped |
| Table render (10K rows) | < 100ms |
| Route transition | < 300ms |

---

## 7. Testing

### Test Pyramid

```text
        ╱  E2E (10%)  ╲          Playwright
       ╱ Integration (25%) ╲      RTL + MSW
      ╱  Component (35%)   ╲     RTL + Storybook
     ╱    Unit (30%)         ╲   Vitest
```

### Tooling

| Tool | Purpose |
|------|---------|
| Vitest | Unit tests (utils, stores, hooks) |
| React Testing Library | Component tests |
| MSW | API mocking |
| Playwright | E2E flows |
| `@axe-core/playwright` | Accessibility audits |
| Chromatic / Percy | Visual regression |
| Lighthouse CI | Performance budgets |

### Test Directory

```text
frontend/
├── src/
│   ├── features/companies/
│   │   ├── components/__tests__/
│   │   └── hooks/__tests__/
│   └── stores/__tests__/
├── e2e/
│   ├── auth.spec.ts
│   ├── lead-discovery.spec.ts
│   ├── company-360.spec.ts
│   └── crm-pipeline.spec.ts
└── .storybook/
    └── stories/
```

### Critical E2E Flows

1. Login → Dashboard loads with KPIs
2. AI Search → Results → Open Company 360°
3. Create Contact → Verify Email → Check status
4. Import CSV → Map fields → Complete
5. CRM: Create deal → Drag to next stage
6. Command palette: Navigate + action
7. Dark mode toggle persists on reload

### Accessibility Tests

```typescript
// e2e/accessibility.spec.ts
import { test, expect } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'

const pages = ['/dashboard', '/companies', '/discover', '/crm', '/settings']

for (const path of pages) {
  test(`${path} has no a11y violations`, async ({ page }) => {
    await page.goto(path)
    const results = await new AxeBuilder({ page }).analyze()
    expect(results.violations).toEqual([])
  })
}
```

---

## 8. UI Implementation Guide

### Sprint 1: Foundation (Week 1–2)

```bash
# Setup
npx shadcn@latest init
npm install zustand @tanstack/react-table @tanstack/react-virtual
npm install framer-motion cmdk sonner lucide-react nuqs
npm install @hookform/resolvers zod react-hook-form

# Add core shadcn components
npx shadcn@latest add button input card dialog drawer dropdown-menu
npx shadcn@latest add table tabs badge avatar skeleton toast command
npx shadcn@latest add select checkbox switch separator scroll-area
```

**Tasks:**
1. Implement `tokens.css` + update `tailwind.config.ts`
2. Build `AppShell`, `Sidebar`, `TopBar` components
3. Implement `ThemeProvider` + `theme-store`
4. Implement `CommandPalette` with `cmdk`
5. Add `GlobalSearch` with AI placeholder rotation
6. Wire `middleware.ts` for auth

### Sprint 2: Data Tables (Week 3–4)

**Tasks:**
1. Build `DataTable` with TanStack Table + Virtual
2. Implement column resize, reorder, visibility, pinning
3. Build `SavedViewsMenu` with localStorage persistence
4. Build `BulkActionBar`
5. Implement Company List page with table
6. Implement Contact List page with table
7. Build Company 360° page (tabs + right panel)
8. Build Contact 360° page

### Sprint 3: Discovery & AI (Week 5–6)

**Tasks:**
1. Lead Discovery page with `AISearchBar`
2. `ParsedIntentPreview` component
3. `SearchProgress` for async AI searches
4. Search Results page with confidence scores
5. AI Assistant full page + drawer variant
6. `AIChat` with message history

### Sprint 4: CRM & Data Ops (Week 7–8)

**Tasks:**
1. Kanban board with drag-and-drop (`@dnd-kit`)
2. Deal detail page
3. Tasks and calendar views
4. Import wizard (4 steps)
5. Export wizard (3 steps)
6. Dashboard with widget grid (`react-grid-layout`)

### Sprint 5: Polish (Week 9–10)

**Tasks:**
1. Analytics reports with Recharts
2. Admin panel
3. Settings pages
4. Keyboard shortcuts dialog
5. Accessibility audit + fixes
6. E2E test suite
7. Performance optimization pass

### Component Implementation Order

```text
1.  Button, Input, Badge, Card, Skeleton
2.  AppShell, Sidebar, TopBar, Breadcrumbs
3.  CommandPalette, GlobalSearch
4.  DataTable (+ toolbar, pagination, bulk actions)
5.  ScoreGauge, VerificationBadge, KpiCard
6.  Entity360 layout (tabs + side panel)
7.  AIChat, SearchProgress
8.  KanbanBoard, ImportWizard, ExportWizard
9.  Chart widgets, MapWidget
10. Settings forms, Admin tables
```

---

## 9. Developer Handoff

### Prerequisites

| Requirement | Version |
|-------------|---------|
| Node.js | 20+ |
| npm/pnpm | Latest |
| Backend API | Running at `localhost:8000` |
| Environment | `.env.local` configured |

### Environment Variables

```bash
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_WS_URL=ws://localhost:8000/api/v1
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

### Getting Started

```bash
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

### Key Documents

| Document | Purpose |
|----------|---------|
| [frontend-architecture.md](./frontend-architecture.md) | IA, navigation, flows, shell |
| [design-system.md](./design-system.md) | Tokens, components, themes |
| [screen-specifications.md](./screen-specifications.md) | Wireframes, UI specs |
| [../phase3/api-specification.md](../phase3/api-specification.md) | Backend API contracts |

### Design Assets

| Asset | Location |
|-------|----------|
| Design tokens | `frontend/src/styles/tokens.css` |
| Tailwind config | `frontend/tailwind.config.ts` |
| shadcn config | `frontend/components.json` |
| Icon set | Lucide React (import per component) |

### API → UI Mapping

| UI Action | API Call | Hook |
|-----------|----------|------|
| Load companies | `GET /companies` | `useCompanies(filters)` |
| Open 360° | `GET /companies/{id}` | `useCompany(id)` |
| AI search | `POST /search/ai` | `useAISearch()` |
| Poll search | `GET /search/{id}` | `useSearchStatus(id)` |
| Score contact | `POST /ai/score/contact/{id}` | `useScoreContact()` |
| Dashboard KPIs | `GET /analytics/dashboard` | `useDashboard()` |
| Import file | `POST /files/upload-url` → S3 → `POST /imports` | `useImport()` |
| Notifications | `GET /notifications` + WS | `useNotifications()` |

### Definition of Done (per screen)

- [ ] Matches wireframe layout and hi-fi spec
- [ ] Responsive across breakpoints
- [ ] Dark mode tested
- [ ] Keyboard navigable
- [ ] Loading, empty, error states implemented
- [ ] API integrated with TanStack Query
- [ ] Permission guards applied
- [ ] Component tests written
- [ ] No axe violations
- [ ] Lighthouse performance > 90

### Open Questions for Product

| # | Question | Default Assumption |
|---|----------|-------------------|
| 1 | Map provider: Mapbox vs Leaflet? | Mapbox (better DX, paid) |
| 2 | Real-time AI chat via WS or polling? | Polling initially |
| 3 | Widget layout per-user or per-org? | Per-user |
| 4 | SSO (Google/Microsoft) in Phase 4? | Login page only; OAuth Phase 5 |
| 5 | Mobile app needed? | Responsive web only |

---

*End of Phase 4 Implementation Guide*