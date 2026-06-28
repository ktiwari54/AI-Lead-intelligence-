# 04 — Component Library

**Frontend v3.0** | Aurora Design System | shadcn/ui + Custom Enterprise Components

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Primitive Components (shadcn/ui)](#2-primitive-components-shadcnui)
3. [Layout Components](#3-layout-components)
4. [Navigation Components](#4-navigation-components)
5. [Form Components](#5-form-components)
6. [Data Display Components](#6-data-display-components)
7. [Data Table System](#7-data-table-system)
8. [Entity Components](#8-entity-components)
9. [AI Components](#9-ai-components)
10. [CRM Components](#10-crm-components)
11. [Chart Components](#11-chart-components)
12. [Overlay Components](#12-overlay-components)
13. [Feedback Components](#13-feedback-components)
14. [Enterprise Components](#14-enterprise-components)
15. [Composition Patterns](#15-composition-patterns)
16. [Storybook Catalog](#16-storybook-catalog)

**Base path:** `frontend/src/components/` and `frontend/src/features/`

---

## 1. Architecture Overview

### Component Tiers

```text
Tier 1: Primitives (shadcn/ui)     → src/components/ui/
Tier 2: Shared patterns            → src/components/{layout,data-table,entity,charts,shared}/
Tier 3: Enterprise composites      → src/components/enterprise/
Tier 4: Feature-specific           → src/features/{module}/components/
```

### Conventions

| Rule | Standard |
|------|----------|
| File naming | PascalCase: `ScoreGauge.tsx` |
| Props interface | `{ComponentName}Props` |
| Variants | `class-variance-authority` (cva) |
| Styling | Tailwind + semantic tokens only |
| Client directive | `'use client'` when using hooks/events |
| Accessibility | Radix primitives, ARIA labels, keyboard nav |
| Data fetching | Never in Tier 1–2; hooks in Tier 4 |

---

## 2. Primitive Components (shadcn/ui)

Located in `src/components/ui/`. Installed via `npx shadcn@latest add {component}`.

### Button

```typescript
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'destructive' | 'outline' | 'secondary' | 'ghost' | 'link'
  size?: 'default' | 'sm' | 'lg' | 'icon'
  loading?: boolean
  asChild?: boolean
}
```

| Variant | Background | Text | Border | Usage |
|---------|------------|------|--------|-------|
| `default` | `primary` | `primary-foreground` | none | Primary CTA |
| `destructive` | `destructive` | `destructive-foreground` | none | Delete, irreversible |
| `outline` | transparent | `foreground` | `border` | Secondary actions |
| `secondary` | `secondary` | `secondary-foreground` | none | Tertiary actions |
| `ghost` | transparent | `foreground` | none | Icon buttons, toolbar |
| `link` | transparent | `primary` | none | Inline links |

| Size | Height | Padding | Font |
|------|--------|---------|------|
| `sm` | 32px | `px-3` | `body-sm` |
| `default` | 40px | `px-4` | `body-md` |
| `lg` | 44px | `px-6` | `body-md` |
| `icon` | 40×40px | — | — |

**Loading state:** `loading={true}` → show `Loader2` spinner, `disabled`, `aria-busy="true"`.

**Accessibility:** Focus ring `ring-2 ring-ring ring-offset-2`. Min touch target 44px on mobile.

---

### Input

```typescript
interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  error?: string
  leftIcon?: LucideIcon
  rightIcon?: LucideIcon
}
```

| State | Border | Ring |
|-------|--------|------|
| Default | `border-input` | — |
| Focus | `border-ring` | `ring-2 ring-ring` |
| Error | `border-destructive` | `ring-2 ring-destructive` |
| Disabled | `opacity-50` | none |

Height: 40px. Padding: `px-3 py-2`. Font: `body-md`.

---

### Textarea

Auto-resize variant via `useAutoResizeTextarea` hook. Min height 80px, max 320px.

---

### Select

Built on Radix `Select`. Variants: single, multi (via custom `MultiSelect`), searchable (via `Combobox`).

```typescript
interface SelectProps {
  options: { value: string; label: string; disabled?: boolean }[]
  placeholder?: string
  value?: string
  onValueChange: (value: string) => void
  disabled?: boolean
}
```

---

### Checkbox

```typescript
interface CheckboxProps {
  checked?: boolean | 'indeterminate'
  onCheckedChange?: (checked: boolean) => void
  disabled?: boolean
  id?: string
}
```

Indeterminate used for "select all" in data tables.

---

### Switch

Height: 24px. Width: 44px. Used in settings, feature flags, notification preferences.

---

### Badge

```typescript
interface BadgeProps {
  variant?: 'default' | 'secondary' | 'destructive' | 'outline' | 'success' | 'warning'
  children: React.ReactNode
}
```

Padding: `px-2 py-0.5`. Font: `label-sm`. Radius: `radius-sm`.

---

### Card

```typescript
// Compound component
<Card>
  <CardHeader>
    <CardTitle />
    <CardDescription />
  </CardHeader>
  <CardContent />
  <CardFooter />
</Card>
```

Container: `bg-card border rounded-lg shadow-sm`.

---

### Avatar

```typescript
interface AvatarProps {
  src?: string
  alt: string
  fallback: string  // initials
  size?: 'sm' | 'md' | 'lg'  // 24, 32, 40px
}
```

---

### Skeleton

```typescript
interface SkeletonProps {
  className?: string
  variant?: 'text' | 'circular' | 'rectangular'
}
```

Animation: shimmer pulse, 1.5s. Respects `prefers-reduced-motion`.

---

### Tabs

```typescript
<Tabs defaultValue="overview">
  <TabsList>
    <TabsTrigger value="overview">Overview</TabsTrigger>
  </TabsList>
  <TabsContent value="overview">...</TabsContent>
</Tabs>
```

`TabsList`: `bg-muted rounded-lg p-1`. Active trigger: `bg-card shadow-sm`.

---

### Separator

Horizontal/vertical divider. Color: `border`. Used in sidebar sections, settings nav.

---

### Dropdown Menu

```typescript
<DropdownMenu>
  <DropdownMenuTrigger asChild><Button variant="ghost" size="icon" /></DropdownMenuTrigger>
  <DropdownMenuContent align="end">
    <DropdownMenuItem />
    <DropdownMenuSeparator />
    <DropdownMenuLabel />
  </DropdownMenuContent>
</DropdownMenu>
```

Row actions menus use `align="end"`. Destructive items: `text-destructive`.

---

## 3. Layout Components

### AppShell

```typescript
interface AppShellProps {
  children: React.ReactNode
}
```

**Structure:**
```text
<div className="flex h-screen overflow-hidden">
  <Sidebar />
  <div className="flex flex-1 flex-col">
    <TopBar />
    <main className="flex-1 overflow-auto p-6">{children}</main>
    <StatusBar />
  </div>
  <CommandPalette />
  <AIAssistantDrawer />
  <Toaster />
</div>
```

**File:** `src/components/layout/AppShell.tsx`

---

### Sidebar

```typescript
interface SidebarProps {
  collapsed: boolean
  onToggle: () => void
}
```

| State | Width | Content |
|-------|-------|---------|
| Expanded | 260px | Icons + labels + section titles |
| Collapsed | 72px | Icons only + tooltips |
| Mobile | Overlay sheet | Full navigation |

**Nav item states:**

| State | Classes |
|-------|---------|
| Default | `text-muted-foreground px-3 py-2 rounded-lg text-sm` |
| Hover | `bg-accent text-foreground` |
| Active | `bg-primary/10 text-primary font-medium` |

**File:** `src/components/layout/Sidebar.tsx`

---

### TopBar

```typescript
interface TopBarProps {
  breadcrumbs?: BreadcrumbItem[]
}
```

Height: 56px (`h-14`). Contains: sidebar toggle, breadcrumbs, `GlobalSearch`, command palette trigger, notification bell, user menu.

**File:** `src/components/layout/TopBar.tsx`

---

### PageHeader

```typescript
interface PageHeaderProps {
  title: string
  description?: string
  actions?: React.ReactNode
  breadcrumbs?: boolean  // auto from route if true
}
```

Title: `display-sm`. Description: `body-md text-muted-foreground`. Actions: right-aligned button group.

**File:** `src/components/enterprise/PageHeader.tsx`

---

### StatusBar

```typescript
interface StatusBarProps {
  credits: number
  syncStatus?: 'synced' | 'syncing' | 'error'
  environment?: 'production' | 'staging' | 'development'
}
```

Height: 32px. Fixed bottom. Shows: credits remaining, last sync time, env badge, version.

**File:** `src/components/enterprise/StatusBar.tsx`

---

### Entity360Layout

```typescript
interface Entity360LayoutProps {
  header: React.ReactNode
  tabs: React.ReactNode
  aiPanel: React.ReactNode
}
```

Grid: `grid grid-cols-12 gap-6`. Main: `col-span-8`. Panel: `col-span-4 sticky top-20`.

Responsive: <1280px hides panel, shows drawer trigger.

**File:** `src/components/entity/Entity360Layout.tsx`

---

## 4. Navigation Components

### Breadcrumbs

```typescript
interface BreadcrumbItem {
  label: string
  href?: string  // undefined = current (non-clickable)
}

interface BreadcrumbsProps {
  items: BreadcrumbItem[]
  maxItems?: number  // default 4, truncate middle
}
```

Separator: `ChevronRight` 14px. Truncated: `MoreHorizontal` dropdown for hidden segments.

---

### OrgSwitcher

```typescript
interface OrgSwitcherProps {
  organizations: Organization[]
  current: Organization
  onSwitch: (orgId: string) => void
}
```

Dropdown with org name, plan badge, checkmark on current. Triggers full data refetch on switch.

**File:** `src/components/enterprise/OrgSwitcher.tsx`

---

### GlobalSearch

```typescript
interface GlobalSearchProps {
  onKeywordSearch: (query: string) => void
  onAISearch: (query: string) => void
  placeholder?: string
}
```

| Property | Value |
|----------|-------|
| Width | `flex-1 max-w-2xl` |
| Height | 40px |
| Background | `bg-muted/50` |
| Debounce | 200ms keyword, 500ms AI (10+ chars) |
| Shortcut hint | `⌘K` badge right |

AI mode: `Sparkles` icon glows when NL detected. `Ctrl+Enter` submits as AI search.

---

### CommandPalette

```typescript
// Uses cmdk via shadcn Command component
// State from command-palette-store.ts
```

| Group | Source |
|-------|--------|
| Recent | localStorage `recent-entities` |
| Navigation | `commandPaletteRoutes` from `navigation.ts` |
| Actions | `commandPaletteActions` |
| Search | Inline NL → redirect to `/search` |

Max height: 480px. Width: 640px centered. Z-index: `--z-overlay`.

**Keyboard:** `↑↓` navigate, `Enter` execute, `Esc` close.

---

### UserMenu

```typescript
interface UserMenuProps {
  user: User
  onLogout: () => void
}
```

Dropdown items: Profile, Settings, Theme submenu, Keyboard shortcuts, Logout.

---

## 5. Form Components

### FormField

```typescript
interface FormFieldProps {
  label: string
  error?: string
  hint?: string
  required?: boolean
  children: React.ReactNode
}
```

RHF wrapper pattern:
```typescript
<FormField label="Company Name" error={errors.name?.message} required>
  <Input {...register('name')} />
</FormField>
```

---

### Combobox (Async Searchable Select)

```typescript
interface ComboboxProps {
  options: { value: string; label: string }[]
  value?: string
  onValueChange: (value: string) => void
  onSearch?: (query: string) => Promise<{ value: string; label: string }[]>
  placeholder?: string
  loading?: boolean
}
```

Used for: company picker in contact form, industry autocomplete, country select.

Debounce on `onSearch`: 300ms.

---

### DatePicker

```typescript
interface DatePickerProps {
  value?: Date
  onChange: (date: Date | undefined) => void
  mode?: 'single' | 'range'
  disabled?: boolean
}
```

Built on `react-day-picker`. Used in: analytics date range, task due dates, CRM calendar.

---

### FileUpload

```typescript
interface FileUploadProps {
  accept: string[]          // ['.csv', '.xlsx', '.json']
  maxSize: number           // bytes, default 50MB
  onFileSelect: (file: File) => void
  onError: (message: string) => void
}
```

Drag-drop zone with dashed border. Shows file name, size, remove button after selection.

**File:** Used in Import Wizard step 1.

---

### FieldMapper

```typescript
interface FieldMapperProps {
  sourceColumns: string[]       // CSV headers
  targetFields: TargetField[]   // entity schema fields
  mapping: Record<string, string>
  onMappingChange: (mapping: Record<string, string>) => void
}
```

Two-column layout: source → target dropdowns. Auto-match by name similarity. Required fields highlighted.

---

### RuleBuilder (Segments)

```typescript
interface RuleBuilderProps {
  rules: SegmentRule[]
  onChange: (rules: SegmentRule[]) => void
  entityType: 'company' | 'contact'
}

interface SegmentRule {
  field: string
  operator: 'eq' | 'neq' | 'gt' | 'lt' | 'contains' | 'in'
  value: string | number | string[]
  conjunction: 'and' | 'or'
}
```

Visual: stacked rule rows with field/operator/value selectors. Add/remove rule buttons.

---

## 6. Data Display Components

### KpiCard / MetricCard

```typescript
interface KpiCardProps {
  title: string
  value: string | number
  trend?: { value: number; direction: 'up' | 'down' }
  icon?: LucideIcon
  sparkline?: number[]
  loading?: boolean
}
```

| Element | Style |
|---------|-------|
| Container | `bg-card border rounded-lg p-5 shadow-sm` |
| Title | `text-sm text-muted-foreground` |
| Value | `text-2xl font-bold` |
| Trend up | `text-success text-xs` + `TrendingUp` icon |
| Trend down | `text-destructive text-xs` + `TrendingDown` icon |
| Icon box | `h-12 w-12 rounded-xl bg-primary/10` |
| Hover | `shadow-md transition-shadow duration-fast` |

Min width: 200px in grid.

---

### ScoreGauge

```typescript
interface ScoreGaugeProps {
  score: number          // 0-100
  variant?: 'circular' | 'linear'
  size?: 'sm' | 'md' | 'lg'  // 32, 48, 64px (circular)
  showLabel?: boolean  // Pursue/Nurture/Monitor/Deprioritize
  animated?: boolean
}
```

| Range | Color Token | Label |
|-------|-------------|-------|
| 80–100 | `score-excellent` | Pursue |
| 60–79 | `score-good` | Nurture |
| 40–59 | `score-fair` | Monitor |
| 0–39 | `score-poor` | Deprioritize |

Circular: SVG arc, 4px stroke, value centered `text-sm font-bold`. Animation: 600ms ease-out from 0.

Linear: full-width bar, 8px height, label below.

---

### ConfidenceBar

```typescript
interface ConfidenceBarProps {
  value: number  // 0.0-1.0
  showValue?: boolean
}
```

Width: 64px. Height: 6px. Fill color scales: <0.7 warning, ≥0.7 success. Value text: `body-sm`.

---

### VerificationBadge

```typescript
interface VerificationBadgeProps {
  type: 'email' | 'phone'
  status: 'verified' | 'unverified' | 'invalid' | 'unknown'
}
```

| Status | Icon | Color |
|--------|------|-------|
| verified | `CheckCircle` | `success` |
| unverified | `Clock` | `warning` |
| invalid | `XCircle` | `destructive` |
| unknown | `HelpCircle` | `muted-foreground` |

---

### TechStack

```typescript
interface TechStackProps {
  technologies: { name: string; category?: string; confidence?: number }[]
}
```

Grid of `Badge` components grouped by category (Languages, Frameworks, Infrastructure, etc.).

---

### Timeline

```typescript
interface TimelineProps {
  events: TimelineEvent[]
  loading?: boolean
}

interface TimelineEvent {
  id: string
  type: 'note' | 'email' | 'call' | 'meeting' | 'system' | 'score' | 'enrichment'
  title: string
  description?: string
  timestamp: string
  actor?: { name: string; avatar?: string }
}
```

Vertical line with type-specific icons. Grouped by date. Infinite scroll for long histories.

---

### EmptyState

```typescript
interface EmptyStateProps {
  icon: LucideIcon
  title: string
  description?: string
  action?: { label: string; onClick: () => void }
  variant?: 'default' | 'not-found' | 'no-results' | 'no-permission'
}
```

Centered layout. Icon: 48px `text-muted-foreground`. Title: `heading-md`. CTA: `Button` primary.

**File:** `src/components/enterprise/EmptyState.tsx`

---

### Chip (Filter Tag)

```typescript
interface ChipProps {
  label: string
  onRemove?: () => void
  variant?: 'default' | 'ai'
}
```

AI variant: `bg-accent text-accent-foreground` with `Sparkles` icon.

---

## 7. Data Table System

### DataTable (Core)

```typescript
interface DataTableProps<T> {
  data: T[]
  columns: ColumnDef<T>[]
  loading?: boolean
  pagination?: PaginationState
  onPaginationChange?: (state: PaginationState) => void
  sorting?: SortingState
  onSortingChange?: (state: SortingState) => void
  rowSelection?: RowSelectionState
  onRowSelectionChange?: (state: RowSelectionState) => void
  virtualized?: boolean
  estimatedRowHeight?: number  // default 48
  emptyState?: React.ReactNode
}
```

**File:** `src/components/data-table/DataTable.tsx`

---

### EntityDataTable

```typescript
interface EntityDataTableProps {
  entityType: 'company' | 'contact'
  data: Company[] | Contact[]
  savedViewId?: string
  onBulkAction?: (action: BulkAction, ids: string[]) => void
  loading?: boolean
  totalCount?: number
}
```

Wraps `DataTable` with entity-specific columns from `features/{entity}/columns.tsx`, toolbar, and bulk actions.

**File:** `src/components/data-table/EntityDataTable.tsx`

---

### DataTableToolbar

```typescript
interface DataTableToolbarProps {
  globalFilter: string
  onGlobalFilterChange: (value: string) => void
  columns: ColumnConfig[]
  onColumnVisibilityChange: (config: ColumnConfig[]) => void
  savedViews: SavedView[]
  activeViewId?: string
  onViewChange: (viewId: string) => void
  onSaveView: (view: SavedView) => void
  selectedCount: number
  bulkActions?: BulkAction[]
}
```

---

### ColumnHeader

Sortable: click toggles asc/desc/none. Shows `ArrowUpDown` / `ArrowUp` / `ArrowDown`. Resize handle on right edge (drag, min 80px, max 400px).

Sticky: `sticky top-0 bg-card z-sticky`.

---

### BulkActionBar

```typescript
interface BulkActionBarProps {
  selectedCount: number
  actions: BulkAction[]
  onClear: () => void
}
```

Sticky bottom bar when `selectedCount > 0`. Shows "{n} selected" + action buttons + clear.

| Entity | Actions |
|--------|---------|
| Companies | Export, Score, Add to List, Enrich, Delete |
| Contacts | Export, Verify Email, Score, Add to List, Delete |
| Search Results | Save to List, Export, Score |

---

### SavedViewsMenu

CRUD for saved table views. Dropdown with: default views, user views, "Save current view", "Manage views".

Persisted: `table-store.ts` (localStorage) + `PATCH /users/me/preferences.table_views`.

---

### Row Actions Menu

`MoreHorizontal` icon button → dropdown: View, Edit, Score, Enrich, Add to List, Delete.

Delete requires confirmation `Dialog`.

---

### Table Row Spec

| Property | Value |
|----------|-------|
| Row height | 48px (40px compact mode) |
| Hover | `bg-muted/50` |
| Selected | `bg-primary/5 border-l-2 border-l-primary` |
| Cell padding | `px-4 py-2` |
| Header font | `heading-sm uppercase text-muted-foreground` |
| Checkbox column | 48px fixed, pinned left |
| Actions column | 48px fixed, pinned right |

---

## 8. Entity Components

### EntityHeader

```typescript
interface EntityHeaderProps {
  entityType: 'company' | 'contact'
  entity: Company | Contact
  onEnrich?: () => void
  onScore?: () => void
  onSyncCRM?: () => void
  onExport?: () => void
  onEdit?: () => void
}
```

Renders logo/avatar, primary fields, score gauge, action buttons. Permission-gated actions.

**File:** `src/components/entity/EntityHeader.tsx`

---

### AISummaryPanel

```typescript
interface AISummaryPanelProps {
  entityType: 'company' | 'contact'
  entityId: string
  summary?: string
  recommendations?: Recommendation[]
  crmStatus?: CRMStatus
  tags?: string[]
  onTagAdd?: (tag: string) => void
  onTagRemove?: (tag: string) => void
}
```

Sections: AI Summary (markdown), Recommendations (clickable actions), CRM Status, Tags.

**File:** `src/components/entity/AISummaryPanel.tsx`

---

### DuplicatePreview

```typescript
interface DuplicatePreviewProps {
  duplicates: { existing: Entity; incoming: Partial<Entity>; matchScore: number }[]
  strategy: 'skip' | 'update' | 'merge'
  onStrategyChange: (strategy: string) => void
  onFieldResolution?: (field: string, winner: 'existing' | 'incoming') => void
}
```

Used in Import Wizard step 3.

---

## 9. AI Components

### AISearchBar

```typescript
interface AISearchBarProps {
  value: string
  onChange: (value: string) => void
  onSubmit: (query: string) => void
  onAISubmit: (query: string) => void
  parsing?: boolean
  intent?: ParsedIntent
  placeholder?: string
}
```

Large search input with AI badge. Debounced intent parsing triggers `ParsedIntentPreview` below.

**File:** `src/features/discovery/AISearchBar.tsx`

---

### ParsedIntentPreview

```typescript
interface ParsedIntentPreviewProps {
  intent: ParsedIntent
  onEditFilters: () => void
  onConfirm: () => void
  estimatedCredits: number
}

interface ParsedIntent {
  action: 'find_companies' | 'find_contacts'
  filters: SearchFilters
  connectors: string[]
  confidence: number
}
```

Chip display of parsed filters. `[Edit Filters]` expands `FilterBuilder`. `[Search →]` executes.

**File:** `src/features/discovery/ParsedIntentPreview.tsx`

---

### SearchProgress

```typescript
interface SearchProgressProps {
  searchId: string
  connectors: { name: string; status: 'pending' | 'running' | 'completed' | 'failed'; resultCount?: number }[]
  overallProgress: number  // 0-100
}
```

Per-connector progress bars. Overall progress. Cancel button. Auto-redirect to results on completion.

**File:** `src/features/discovery/SearchProgress.tsx`

---

### AIChat

```typescript
interface AIChatProps {
  messages: ChatMessage[]
  onSend: (message: string) => void
  onAttach?: (file: File) => void
  loading?: boolean
  suggestions?: string[]
}

interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  resultCards?: AIResultCardData[]
  timestamp: string
}
```

Streaming support via SSE. Typing indicator when `loading`. Suggested follow-up chips below last assistant message.

**File:** `src/features/ai/AIChat.tsx`

---

### AIAssistantDrawer

```typescript
interface AIAssistantDrawerProps {
  open: boolean
  onClose: () => void
  entityContext?: { type: 'company' | 'contact'; id: string; name: string }
}
```

Slide-over from right (480px). Contains mini `AIChat` + `ContextPanel`. Triggered from 360° pages.

**File:** `src/features/ai/AIAssistantDrawer.tsx`

---

### AIResultCard

```typescript
interface AIResultCardData {
  entityType: 'company' | 'contact'
  id: string
  name: string
  subtitle: string
  score?: number
  confidence?: number
}
```

Compact card in chat messages. Click → navigate to 360°. Actions: Score, Add to List.

---

### RecommendationPanel

```typescript
interface RecommendationPanelProps {
  recommendations: Recommendation[]
  onAction: (recommendation: Recommendation) => void
  loading?: boolean
}

interface Recommendation {
  id: string
  type: 'follow_up' | 'score' | 'similar' | 'outreach' | 'enrich'
  title: string
  description: string
  entityId?: string
  priority: 'high' | 'medium' | 'low'
}
```

Used in Dashboard widget and 360° AI panel.

---

## 10. CRM Components

### KanbanBoard

```typescript
interface KanbanBoardProps {
  pipeline: CRMPipeline
  deals: CRMDeal[]
  onDealMove: (dealId: string, newStageId: string) => void
  onDealClick: (dealId: string) => void
  onAddDeal: (stageId: string) => void
}
```

Horizontal scroll container. Columns from `CRMStage[]`. Drag-and-drop via `@dnd-kit/core`.

**File:** `src/features/crm/KanbanBoard.tsx`

---

### KanbanColumn

```typescript
interface KanbanColumnProps {
  stage: CRMStage
  deals: CRMDeal[]
  onDealMove: (dealId: string) => void
  onAddDeal: () => void
}
```

Header: stage name, deal count, total value. Footer: "+ Add Deal" ghost button.

Column min-width: 280px.

---

### DealCard

```typescript
interface DealCardProps {
  deal: CRMDeal
  onClick: () => void
}
```

Card: `bg-card border rounded-lg p-3 shadow-sm`. Shows title, `$value`, contact name, company, score badge. Drag handle on hover.

**File:** `src/features/crm/DealCard.tsx`

---

### DealStageBar

Horizontal step indicator showing deal progression through pipeline stages. Current stage highlighted `primary`.

---

### TaskItem

```typescript
interface TaskItemProps {
  task: CRMTask
  onToggle: (completed: boolean) => void
  onClick: () => void
}
```

Checkbox + title + due date + assignee avatar + priority badge (`high`=destructive, `medium`=warning, `low`=muted).

---

### CalendarView

```typescript
interface CalendarViewProps {
  events: CalendarEvent[]
  view: 'month' | 'week' | 'day'
  onViewChange: (view: string) => void
  onEventClick: (eventId: string) => void
  onDateSelect: (date: Date) => void
}
```

Month grid with event dots. Week/day show timed blocks.

---

### ActivityFeed

```typescript
interface ActivityFeedProps {
  activities: Activity[]
  loading?: boolean
  groupByDate?: boolean
}
```

Chronological list with type icons, actor, timestamp, deep links.

---

## 11. Chart Components

All charts wrap Recharts with Aurora theme defaults.

### AreaChart

```typescript
interface AreaChartProps {
  data: { date: string; value: number }[]
  height?: number
  color?: string
  showGrid?: boolean
}
```

Used in: Search Trends widget, Lead Velocity report.

---

### BarChart

```typescript
interface BarChartProps {
  data: { label: string; value: number }[]
  orientation?: 'vertical' | 'horizontal'
  height?: number
}
```

Used in: Score Distribution, Industry Breakdown.

---

### PieChart / DonutChart

```typescript
interface PieChartProps {
  data: { name: string; value: number; color?: string }[]
  innerRadius?: number  // 0 = pie, >0 = donut
  height?: number
}
```

Used in: Industry Breakdown widget, Grade breakdown.

---

### FunnelChart

```typescript
interface FunnelChartProps {
  stages: { name: string; count: number; value?: number }[]
}
```

Custom SVG component (not Recharts). Horizontal bars decreasing width.

---

### Sparkline

Inline 32px height line chart for `KpiCard` trend visualization. No axes.

---

### MapWidget

```typescript
interface MapWidgetProps {
  data: { country: string; count: number }[]
}
```

Choropleth map (Mapbox GL or simplified SVG world map). Sequential indigo scale.

---

## 12. Overlay Components

### Dialog (Modal)

```typescript
interface DialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  title: string
  description?: string
  children: React.ReactNode
  footer?: React.ReactNode
  size?: 'default' | 'wide'  // 560px | 800px
}
```

Animation: scale 0.95→1 + fade, `--duration-normal`. Backdrop: `bg-background/80 backdrop-blur-sm`.

Used for: confirmations, create forms, widget catalog.

---

### Drawer

```typescript
interface DrawerProps {
  open: boolean
  onClose: () => void
  side?: 'left' | 'right'
  width?: number  // default 480px
  children: React.ReactNode
}
```

Slide animation from side. Used for: AI Assistant, advanced filters, mobile nav.

---

### Sheet

Mobile-optimized drawer (full width). Used for sidebar on mobile.

---

### Popover

```typescript
interface PopoverProps {
  trigger: React.ReactNode
  content: React.ReactNode
  align?: 'start' | 'center' | 'end'
}
```

Used for: quick previews, column config, date picker trigger.

---

### Tooltip

Delay: 300ms show, 0ms hide. Max width: 240px. Used for: collapsed sidebar icons, icon buttons, truncated text.

---

### KeyboardShortcutsDialog

```typescript
interface KeyboardShortcutsDialogProps {
  open: boolean
  onClose: () => void
}
```

Grouped shortcut list from `keyboard-shortcuts-store.ts`. Triggered by `?` key.

**File:** `src/components/layout/KeyboardShortcutsDialog.tsx`

---

## 13. Feedback Components

### Toast (Sonner)

```typescript
// Usage
toast.success('Company created successfully')
toast.error('Failed to export contacts')
toast.loading('Importing 1,250 rows...')
toast.promise(promise, { loading, success, error })
```

Position: bottom-right. Duration: 3s (success), 5s (error), persistent (loading). Z-index: `--z-toast`.

---

### Alert

```typescript
interface AlertProps {
  variant: 'info' | 'success' | 'warning' | 'destructive'
  title: string
  description?: string
  action?: React.ReactNode
}
```

Used for: credit warnings, connector failures, network errors (banner at top of page).

---

### Progress

```typescript
interface ProgressProps {
  value: number  // 0-100
  label?: string
  showValue?: boolean
  variant?: 'default' | 'success' | 'destructive'
}
```

Height: 8px. Used in: import progress, search progress, file upload.

---

## 14. Enterprise Components

### DashboardGrid

```typescript
interface DashboardGridProps {
  layout: WidgetLayout[]
  editMode: boolean
  onLayoutChange: (layout: WidgetLayout[]) => void
  children: React.ReactNode
}

interface WidgetLayout {
  id: string
  widgetType: string
  x: number
  y: number
  w: number
  h: number
}
```

12-column CSS grid with `react-grid-layout`. Drag/resize in edit mode.

**File:** `src/components/dashboard/DashboardGrid.tsx`

---

### WidgetCatalog

```typescript
interface WidgetCatalogProps {
  open: boolean
  onClose: () => void
  onAdd: (widgetType: string) => void
  availableWidgets: WidgetDefinition[]
}
```

Categorized modal: KPIs, Charts, Tables, AI. Preview thumbnail per widget.

---

### ConnectorHealthList

```typescript
interface ConnectorHealthListProps {
  connectors: { name: string; status: 'healthy' | 'degraded' | 'down'; latencyMs?: number; lastSync?: string }[]
}
```

List with status dot (green/amber/red), name, latency, last sync time.

---

### FilterBuilder

```typescript
interface FilterBuilderProps {
  filters: SearchFilters
  onChange: (filters: SearchFilters) => void
  entityType: 'company' | 'contact'
}
```

Collapsible panel with field-specific inputs: multi-select industries, country combobox, employee range slider, technology tags, score range.

---

### ExportWizard / ImportWizard

Multi-step wizard containers with `StepIndicator`, navigation (Back/Next/Confirm), and per-step content slots.

**Files:**
- `src/features/imports/ImportWizard.tsx`
- `src/features/exports/ExportWizard.tsx`

---

### ColumnPicker

```typescript
interface ColumnPickerProps {
  availableColumns: { id: string; label: string }[]
  selectedColumns: string[]
  onChange: (columns: string[]) => void
}
```

Drag-to-reorder checklist. Used in Export Wizard step 2.

---

## 15. Composition Patterns

### Page Template (List Page)

```tsx
<PageHeader title="Companies" actions={<><Button>+ New</Button><Button variant="outline">Import</Button></>} />
<DataTableToolbar {...toolbarProps} />
<EntityDataTable entityType="company" {...tableProps} />
<BulkActionBar {...bulkProps} />
```

### Page Template (360° Page)

```tsx
<Entity360Layout
  header={<EntityHeader entityType="company" entity={company} {...actions} />}
  tabs={<Tabs>...</Tabs>}
  aiPanel={<AISummaryPanel entityType="company" entityId={id} />}
/>
```

### Page Template (Wizard)

```tsx
<PageHeader title="Import Companies" />
<StepIndicator steps={['Upload', 'Map', 'Preview', 'Import']} current={step} />
<Card className="max-w-3xl mx-auto">{stepContent}</Card>
<div className="flex justify-between max-w-3xl mx-auto">
  <Button variant="outline" onClick={back}>Back</Button>
  <Button onClick={next}>Next</Button>
</div>
```

### Permission Gating Pattern

```tsx
const { hasPermission } = usePermissions()

{hasPermission('companies:write') && (
  <Button onClick={onCreate}>+ New Company</Button>
)}
```

### Credit Gating Pattern

```tsx
const { credits } = useOrganization()
const canAfford = credits >= CREDIT_COSTS.enrich

<Button disabled={!canAfford} onClick={onEnrich}>
  Enrich {!canAfford && <Badge variant="warning">3 credits</Badge>}
</Button>
```

---

## 16. Storybook Catalog

### Configuration

```text
frontend/.storybook/
├── main.ts          # @storybook/nextjs framework
├── preview.ts       # Aurora theme decorator, QueryClient provider
└── decorators/
    ├── withTheme.tsx
    ├── withAppShell.tsx
    └── withQueryClient.tsx
```

### Story Organization

| Category | Stories |
|----------|---------|
| Primitives | Button, Input, Select, Badge, Card, Avatar, Skeleton, Tabs |
| Layout | AppShell, Sidebar, TopBar, PageHeader, StatusBar, Entity360Layout |
| Data | DataTable, EntityDataTable, KpiCard, ScoreGauge, ConfidenceBar |
| AI | AISearchBar, ParsedIntentPreview, AIChat, AIResultCard, SearchProgress |
| CRM | KanbanBoard, DealCard, TaskItem, ActivityFeed |
| Charts | AreaChart, BarChart, PieChart, FunnelChart, Sparkline |
| Feedback | EmptyState, Toast, Alert, Progress |
| Overlays | Dialog, Drawer, CommandPalette, KeyboardShortcutsDialog |

### Story Naming Convention

```
{Category}/{Component}/{Variant}
Example: Data/ScoreGauge/Circular
         Data/ScoreGauge/Linear
         AI/AISearchBar/WithIntent
```

### Required Story States per Component

Every component story must include:

1. **Default** — typical usage
2. **Loading** — skeleton/spinner state
3. **Empty** — no data
4. **Error** — error prop/message
5. **Disabled** — if applicable
6. **Dark theme** — via theme decorator

### Visual Regression

Chromatic integration for: Button variants, DataTable states, ScoreGauge ranges, EmptyState variants, KanbanBoard with cards.

---

*Next: [05-states-and-interactions.md](./05-states-and-interactions.md) — States and interaction specifications*