# 05 — States & Interactions

**Frontend v3.0** | AI Lead Intelligence Platform

---

## Table of Contents

1. [State Model Overview](#1-state-model-overview)
2. [Loading States](#2-loading-states)
3. [Error States](#3-error-states)
4. [Empty States](#4-empty-states)
5. [Success States](#5-success-states)
6. [Permission States](#6-permission-states)
7. [Keyboard Interactions](#7-keyboard-interactions)
8. [Responsive Behavior](#8-responsive-behavior)
9. [Form Interaction States](#9-form-interaction-states)
10. [Data Table Interactions](#10-data-table-interactions)
11. [AI Interaction States](#11-ai-interaction-states)
12. [Async Operation States](#12-async-operation-states)
13. [Global State Matrix](#13-global-state-matrix)

---

## 1. State Model Overview

Every screen and component implements a consistent state hierarchy:

```text
Initial → Loading → Success
                  → Empty (zero results)
                  → Error (recoverable / fatal)
                  → Partial (some data + some errors)
```

### State Priority (what to show when multiple apply)

1. **Fatal error** — full-page error boundary
2. **Permission denied** — 403 or inline gate
3. **Loading** — skeleton matching final layout
4. **Empty** — contextual empty state with CTA
5. **Partial error** — inline alert + available data
6. **Success** — full content

### State Storage

| State Type | Storage | Scope |
|------------|---------|-------|
| Server data | TanStack Query cache | Global per query key |
| UI chrome | Zustand stores | Global |
| Form input | React Hook Form | Component |
| URL filters | `searchParams` / `nuqs` | Per route |
| Ephemeral UI | `useState` | Component |
| Persistent prefs | localStorage + API | Per user |

---

## 2. Loading States

### 2.1 Page-Level Loading

**Pattern:** Route-level `loading.tsx` or in-page skeleton matching final layout shape.

| Screen | Skeleton Layout |
|--------|-----------------|
| Dashboard | 5 KPI skeletons + 4 chart rectangle skeletons |
| Company List | Toolbar skeleton + 10 table row skeletons |
| Company 360° | Header skeleton + tab bar + 2-column content skeleton |
| Lead Discovery | Search bar skeleton + 2 card skeletons |
| Search Results | Summary line skeleton + table skeleton |
| CRM Pipeline | 4 column skeletons with 2 card skeletons each |
| AI Assistant | Chat bubble skeletons + input skeleton |
| Import Wizard | Upload zone skeleton |
| Settings | Sidebar + form field skeletons |

**Duration behavior:**
- Show skeleton after **200ms** delay (avoid flash on fast loads)
- Minimum display: **500ms** (avoid flicker)
- Timeout at **30s** → show error with retry

```tsx
// Pattern
if (isLoading) return <PageSkeleton variant="company-list" />
if (isError) return <ErrorState onRetry={refetch} />
if (!data?.length) return <EmptyState ... />
return <CompanyList data={data} />
```

---

### 2.2 Component-Level Loading

| Component | Loading Pattern |
|-----------|-----------------|
| `Button` | `Loader2` spinner replaces label, `disabled`, `aria-busy="true"` |
| `DataTable` | 10 skeleton rows matching column widths |
| `KpiCard` | Skeleton value + skeleton trend line |
| `ScoreGauge` | Gray track, no animation |
| `AIChat` | 3-dot typing indicator in assistant bubble |
| `SearchProgress` | Per-connector progress bars animating |
| `KanbanBoard` | Column skeletons with card placeholders |
| `Chart` | Gray rectangle with pulse, 200px min height |
| `EntityHeader` | Avatar circle + 2 text line skeletons |
| `AISummaryPanel` | 3 paragraph skeletons |
| `FileUpload` | Spinner overlay on drop zone during upload |

---

### 2.3 Inline / Background Loading

| Action | UI Feedback |
|--------|-------------|
| Sort table column | Subtle opacity 0.6 on table, no full skeleton |
| Filter change | Debounce 300ms, then table skeleton rows |
| Pagination | Table opacity 0.6 + spinner in pagination bar |
| Save form | Button loading state, form fields disabled |
| Bulk score | `BulkActionBar` shows progress "{n}/{total} scoring..." |
| CRM drag | Optimistic UI — card moves immediately, revert on error |
| Autocomplete | `Combobox` shows `Loader2` in dropdown |
| Infinite scroll | Sentinel triggers 3 skeleton rows at bottom |

---

### 2.4 Search-Specific Loading

**Lead Discovery AI parsing:**
```text
1. User types (10+ chars)
2. After 500ms debounce → search bar shows pulsing Sparkles icon
3. ParsedIntentPreview skeleton appears (3 chip skeletons)
4. Intent loads → chips populate with fade-in
5. On submit → SearchProgress replaces preview
```

**Search execution:**
```text
1. Redirect to /search/results?searchId={id} (or inline progress)
2. SearchProgress panel: per-connector bars
3. Results stream in as connectors complete (progressive loading)
4. Full table renders when all connectors done
```

---

## 3. Error States

### 3.1 Error Classification

| Class | HTTP Status | Recovery | Display |
|-------|-------------|----------|---------|
| Network | — (no response) | Auto-retry 3× | Top banner |
| Auth expired | 401 | Redirect to login | Full page |
| Forbidden | 403 | None | 403 page or inline |
| Not found | 404 | Navigate away | 404 page |
| Validation | 422 | Fix input | Inline field errors |
| Conflict | 409 | User decision | Dialog |
| Insufficient credits | 402 | Purchase credits | Dialog + billing link |
| Rate limited | 429 | Wait + retry | Toast with countdown |
| Server error | 500 | Retry | Error boundary |
| Connector failure | 502 | Partial results | Inline warning per connector |

---

### 3.2 Page-Level Errors

**Error Boundary (`error.tsx`):**
```text
┌─────────────────────────────────────────┐
│  ⚠️ Something went wrong                │
│                                         │
│  Error ID: req_abc123                   │
│  We couldn't load this page.            │
│                                         │
│  [Try Again]  [Go to Dashboard]         │
└─────────────────────────────────────────┘
```

- Log error to observability with request ID
- "Try Again" calls `reset()` from error boundary
- Show stack trace only in development

---

### 3.3 Inline Errors

**Form field:**
```text
┌──────────────────────────┐
│ Company Name *           │
│ ┌──────────────────────┐ │
│ │                      │ │  ← border-destructive
│ └──────────────────────┘ │
│ ⚠ Name is required       │  ← text-destructive body-sm
└──────────────────────────┘
```

**API action failure:**
- Toast: `toast.error('Failed to score 3 contacts')` with action "Retry"
- Table row: red left border + tooltip with error message
- Bulk action: summary dialog "12 succeeded, 3 failed" with expandable error list

---

### 3.4 Network Error Banner

Persistent banner at top of `AppShell` when offline or API unreachable:

```text
┌─────────────────────────────────────────────────────────────┐
│ ⚠️ Connection lost. Retrying... (attempt 2/3)    [Dismiss]  │
└─────────────────────────────────────────────────────────────┘
```

- Auto-retry with exponential backoff: 2s, 4s, 8s
- On reconnect: banner changes to success green "Back online" (auto-dismiss 3s)
- TanStack Query `networkMode: 'offlineFirst'` caches last good data

---

### 3.5 Credit Insufficient (402)

```text
┌─────────────────────────────────────────┐
│  Insufficient Credits                   │
│                                         │
│  This action requires 10 credits.       │
│  You have 3 remaining.                  │
│                                         │
│  [Purchase Credits]  [Cancel]           │
└─────────────────────────────────────────┘
```

Triggered before API call when `credits < cost`. Also handles 402 response as fallback.

---

### 3.6 Per-Screen Error Specs

| Screen | Error Scenarios | Recovery |
|--------|-----------------|----------|
| Dashboard | Analytics API down | Show KPIs from cache, "Some data unavailable" alert |
| Company List | List fetch fails | Full error state with retry |
| Company 360° | Entity not found | Redirect to 404 |
| Company 360° | AI summary fails | Panel shows "Summary unavailable" + retry |
| Lead Discovery | AI parse fails | Show raw keyword search fallback |
| Search Results | Connector timeout | Partial results + warning per failed connector |
| Import | Validation errors | Step 3 shows error rows with download link |
| CRM Kanban | Stage update fails | Revert card position + toast error |
| AI Assistant | Stream interrupted | "Response interrupted" + regenerate button |

---

## 4. Empty States

### 4.1 Empty State Component Spec

Every empty state uses `EmptyState` with:

| Field | Requirement |
|-------|-------------|
| Icon | 48px, `text-muted-foreground`, contextually relevant |
| Title | `heading-md`, actionable language |
| Description | `body-md text-muted-foreground`, 1-2 sentences |
| CTA | Primary `Button` when user can take action |
| Secondary | Link to documentation or alternative path |

---

### 4.2 Per-Context Empty States

| Context | Icon | Title | Description | CTA |
|---------|------|-------|-------------|-----|
| No companies | `Building2` | "No companies yet" | "Add your first company or import from CSV." | "Add Company" |
| No contacts | `Users` | "No contacts yet" | "Create a contact or discover leads with AI search." | "Find Contacts" |
| No search results | `Search` | "No results found" | "Try broadening your filters or using different keywords." | "Edit Filters" |
| No saved searches | `Bookmark` | "No saved searches" | "Save a search from Lead Discovery to quickly replay it." | "Start Searching" |
| No lists | `List` | "No lists created" | "Organize leads into lists for targeted outreach." | "Create List" |
| No segments | `Target` | "No segments defined" | "Create dynamic segments based on rules." | "Create Segment" |
| No deals | `Kanban` | "No deals in pipeline" | "Create your first deal to start tracking revenue." | "Create Deal" |
| No tasks | `CheckSquare` | "No tasks" | "Stay organized by creating tasks linked to deals and contacts." | "Create Task" |
| No notifications | `Bell` | "All caught up" | "You'll see alerts for searches, exports, and scores here." | — |
| No imports | `Upload` | "No imports yet" | "Upload a CSV to bulk-add companies or contacts." | "New Import" |
| No exports | `Download` | "No exports yet" | "Export your data to CSV, Excel, or JSON." | "New Export" |
| No AI recommendations | `Sparkles` | "No recommendations" | "Run more searches and scores to get AI suggestions." | "Go to Discovery" |
| Empty pipeline stage | `Inbox` | "No deals" | "Drag deals here or create a new one." | "+ Add Deal" |
| No audit logs | `Shield` | "No audit events" | "Admin actions will be logged here." | — |
| Search table (filtered) | `Filter` | "No matches" | "No records match your current filters." | "Clear Filters" |

---

### 4.3 Differentiating Zero Data vs Zero Results

| Condition | Title | CTA |
|-----------|-------|-----|
| Entity list, no records exist | "No {entities} yet" | Create / Import |
| Entity list, filters exclude all | "No matches" | Clear Filters |
| Search, valid query, no matches | "No results found" | Edit Filters |
| Search, invalid/blocked query | Error state | Fix query |

Detection: `total === 0 && !hasActiveFilters` → true empty. `total === 0 && hasActiveFilters` → filtered empty.

---

## 5. Success States

### 5.1 Feedback Patterns

| Action | Primary Feedback | Secondary Feedback |
|--------|------------------|-------------------|
| Create entity | Toast: "{name} created" | Navigate to 360° |
| Update entity | Toast: "Changes saved" | Inline checkmark fade (forms) |
| Delete entity | Toast: "{name} deleted" | Remove from table (optimistic) |
| Bulk delete | Toast: "{n} deleted" | Clear selection |
| Import complete | Toast + redirect | Progress page summary card |
| Export complete | Toast: "Export ready" | Download link + notification |
| Score complete | Toast: "Score updated: 82" | Score gauge animates |
| Search saved | Toast: "Search saved" | Appears in Saved Searches |
| Deal stage change | Toast: "Moved to Qualified" | Card animates to column |
| CRM sync | Toast: "Synced to Salesforce" | CRM status panel updates |
| Layout saved | Toast: "Dashboard layout saved" | Exit edit mode |
| Settings saved | Toast: "Preferences updated" | — |
| Copy to clipboard | Toast: "Copied" | Brief icon flash |

### 5.2 Toast Specifications

| Property | Value |
|----------|-------|
| Position | Bottom-right |
| Duration | 3s (success), 5s (error), persistent (loading/promise) |
| Max visible | 3 stacked |
| Dismiss | Click or swipe right |
| Action button | Optional (e.g., "Undo", "View", "Retry") |
| Icon | Type-specific: `CheckCircle`, `AlertCircle`, `Loader2` |

### 5.3 Optimistic Updates

| Action | Optimistic Behavior | Rollback on Error |
|--------|--------------------|--------------------|
| Delete row | Remove from table immediately | Re-insert row + error toast |
| Toggle task | Checkbox flips immediately | Revert checkbox |
| Kanban drag | Card moves to column | Animate back + error toast |
| Mark notification read | Remove unread dot | Restore dot |
| Add tag | Tag appears in list | Remove tag + error toast |

### 5.4 Completion Celebrations (Subtle)

| Action | Celebration |
|--------|-------------|
| Import 1000+ rows | Progress bar flashes green + confetti-free checkmark |
| First search | Tooltip hint: "Great! Now score your top results." |
| Dashboard customize save | Brief green border flash on grid |

No heavy animations. Enterprise tone.

---

## 6. Permission States

### 6.1 Permission Levels

| Level | UI Behavior |
|-------|-------------|
| **Full access** | All actions visible and enabled |
| **Read only** | View data, no write actions; Edit/Delete/Create hidden |
| **No access** | Nav item hidden; direct URL → 403 page |
| **Credit gated** | Action visible but disabled with credit cost tooltip |
| **Feature flagged** | Hidden or "Coming soon" badge |

### 6.2 RBAC Permission Strings

| Permission | Gates |
|------------|-------|
| `dashboard:read` | Dashboard page |
| `companies:read` | Company list, 360° view |
| `companies:write` | Create, edit, delete, merge, import companies |
| `contacts:read` | Contact list, 360° view |
| `contacts:write` | Create, edit, delete, merge, verify |
| `search:execute` | Lead Discovery, run searches |
| `search:read` | Saved searches, search history |
| `ai:use` | AI Assistant |
| `ai:score` | Score actions, Lead Scoring dashboard |
| `crm:read` | CRM views |
| `crm:write` | Create/edit deals, tasks, activities |
| `imports:execute` | Import wizard |
| `exports:execute` | Export wizard |
| `analytics:read` | Analytics hub and reports |
| `org:manage` | Organization settings |
| `users:manage` | User management |
| `billing:read` | Billing page |
| `api_keys:manage` | API key CRUD |
| `admin:read` | Admin panel view |
| `admin:write` | Feature flags, system config |
| `connectors:manage` | Connector configuration |

### 6.3 UI Gating Patterns

**Hidden nav item:**
```typescript
// navigation.ts
{ name: 'Admin', href: '/admin', permission: 'admin:read' }
// Sidebar filters items where !permission || hasPermission(permission)
```

**Disabled button with tooltip:**
```tsx
<Tooltip content="You don't have permission to delete companies">
  <span>
    <Button variant="destructive" disabled>Delete</Button>
  </span>
</Tooltip>
```

**Read-only 360°:**
- Hide: Enrich, Score, Edit, Delete, Sync CRM buttons
- Show: View-only data, export (if `exports:execute`)
- AI panel: read-only summary, no action buttons

**403 Page:**
```text
┌─────────────────────────────────────────┐
│  🛡️ Access Denied                       │
│                                         │
│  You don't have permission to view      │
│  this page. Contact your administrator. │
│                                         │
│  [Go Back]  [Go to Dashboard]           │
└─────────────────────────────────────────┘
```

### 6.4 Role-Based Empty CTAs

| Role | Company List Empty CTA |
|------|------------------------|
| `owner`, `admin`, `member` | "Add Company" + "Import" |
| `viewer` | "No companies yet" (no CTA) |

---

## 7. Keyboard Interactions

### 7.1 Global Shortcuts

| Shortcut | Action | Context |
|----------|--------|---------|
| `Ctrl+K` / `⌘K` | Open command palette | Global |
| `Ctrl+Shift+P` / `⌘⇧P` | Command palette (actions only) | Global |
| `Ctrl+B` / `⌘B` | Toggle sidebar | Global |
| `Ctrl+/` / `⌘/` | Focus global search | Global |
| `Ctrl+Enter` / `⌘↵` | Submit as AI search | Global search focused |
| `?` | Open keyboard shortcuts dialog | Global (not in input) |
| `Esc` | Close overlay / clear selection | Global |
| `G` then `D` | Go to Dashboard | Global (vim-style) |
| `G` then `C` | Go to Companies | Global |
| `G` then `O` | Go to Contacts | Global |
| `G` then `L` | Go to Lead Discovery | Global |
| `G` then `A` | Go to AI Assistant | Global |
| `G` then `R` | Go to CRM Pipeline | Global |
| `G` then `S` | Go to Settings | Global |

**Vim-style sequences:** `G` starts sequence, second key within 1s completes navigation. Show brief indicator in status bar: "Go to..."

---

### 7.2 Command Palette Shortcuts

| Key | Action |
|-----|--------|
| `↑` / `↓` | Navigate items |
| `Enter` | Execute selected item |
| `Esc` | Close palette |
| `Tab` | Cycle command groups |
| `Backspace` (empty input) | Show recent items |

---

### 7.3 Data Table Shortcuts

| Shortcut | Action | Context |
|----------|--------|---------|
| `↑` / `↓` | Navigate rows | Table focused |
| `Shift+↑` / `Shift+↓` | Extend selection | Table focused |
| `Ctrl+A` / `⌘A` | Select all (current page) | Table focused |
| `Enter` | Open selected row (360°) | Row selected |
| `Space` | Toggle row selection | Row focused |
| `Delete` | Delete selected (with confirm) | Rows selected + permission |
| `E` | Edit selected | Row selected + permission |
| `/` | Focus table filter | Table page |
| `Ctrl+Shift+F` | Clear all filters | Table page |

---

### 7.4 Form Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+S` / `⌘S` | Save form |
| `Esc` | Cancel / close modal |
| `Tab` / `Shift+Tab` | Navigate fields |
| `Enter` | Submit form (single-field) |

---

### 7.5 360° Page Shortcuts

| Shortcut | Action |
|----------|--------|
| `1`–`6` | Switch tabs |
| `E` | Edit entity |
| `S` | Score entity |
| `N` | Add note |
| `Ctrl+Shift+A` | Open AI Assistant drawer |

---

### 7.6 CRM Kanban Shortcuts

| Shortcut | Action |
|----------|--------|
| `←` / `→` | Move focus between columns |
| `↑` / `↓` | Move focus between cards |
| `Enter` | Open focused deal |
| `Ctrl+→` | Move deal to next stage |
| `Ctrl+←` | Move deal to previous stage |
| `N` | New deal in focused column |

---

### 7.7 AI Assistant Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+Enter` | Send message |
| `Ctrl+Shift+N` | New chat |
| `Ctrl+Shift+H` | Toggle chat history |
| `↑` (empty input) | Edit last message |

---

### 7.8 Shortcut Conflicts & Guards

- Global shortcuts **disabled** when focus is in `<input>`, `<textarea>`, or `contenteditable`
- Exception: `Esc` always works; `Ctrl+S` always saves form
- `?` disabled in inputs (types literal `?`)
- Store shortcuts in `keyboard-shortcuts-store.ts` for customization (future)

---

## 8. Responsive Behavior

### 8.1 Breakpoint Summary

| Name | Min Width | Tailwind |
|------|-----------|----------|
| Mobile | 0 | default |
| Tablet | 640px | `sm:` |
| Laptop | 1024px | `lg:` |
| Desktop | 1280px | `xl:` |
| Wide | 1536px | `2xl:` |

---

### 8.2 Component Responsive Matrix

| Component | Mobile (<640) | Tablet (640–1023) | Desktop (≥1024) |
|-----------|---------------|-------------------|-----------------|
| **Sidebar** | Hidden; hamburger opens `Sheet` overlay | Collapsed (72px) | Expanded (260px) |
| **TopBar** | Logo + hamburger + bell + avatar | + collapsed search icon | Full search bar + breadcrumbs |
| **GlobalSearch** | Icon tap → full-screen search overlay | Compact (max 320px) | Full width (max 2xl) |
| **PageHeader** | Title + actions in overflow menu | Title + 2 visible actions | Title + all actions |
| **DataTable** | Card list view (stacked fields) | Horizontal scroll table | Full table with all columns |
| **BulkActionBar** | Fixed bottom sheet | Fixed bottom bar | Inline above pagination |
| **Entity 360°** | Single column; tabs only | Single column; AI via drawer | 8/4 column split |
| **Dashboard grid** | 1 column stacked | 2 columns | 12-column grid |
| **Command palette** | Full screen | Centered modal (90vw) | Centered modal (640px) |
| **Kanban** | Single column vertical scroll | 2 visible columns + scroll | All columns visible |
| **AI Assistant** | Full screen chat | Full screen chat | Split panel |
| **Settings** | Stacked nav dropdown | Side nav (200px) | Side nav (240px) |
| **Import wizard** | Full width steps | Max 640px centered | Max 768px centered |
| **Charts** | Full width, 200px height | 50% width in grid | Widget-sized |
| **StatusBar** | Credits only | Credits + sync | Full bar |
| **Dialogs** | Full screen (sheet style) | Centered 90vw | Centered fixed width |

---

### 8.3 Mobile-Specific Interactions

| Pattern | Implementation |
|---------|----------------|
| Pull to refresh | Not implemented (use refresh button) |
| Swipe row actions | Swipe left on table card → Delete, Edit |
| Bottom navigation | Not used (sidebar sheet instead) |
| FAB | Contextual FAB for primary action on mobile list pages |
| Touch targets | Minimum 44×44px for all interactive elements |
| Table → cards | `EntityDataTable` renders `EntityCard` list below 640px |

---

### 8.4 Responsive Typography

| Element | Mobile | Desktop |
|---------|--------|---------|
| Page title | `heading-lg` (20px) | `display-sm` (24px) |
| KPI value | `text-xl` | `text-2xl` |
| Table text | `body-md` (14px) | `body-md` (14px) |
| Sidebar labels | Hidden | `body-md` |

---

## 9. Form Interaction States

### 9.1 Field States

| State | Border | Label | Helper |
|-------|--------|-------|--------|
| Default | `border-input` | `text-foreground` | `text-muted-foreground` |
| Focus | `ring-2 ring-ring` | `text-primary` | — |
| Filled | `border-input` | `text-foreground` | — |
| Error | `border-destructive ring-destructive` | `text-destructive` | Error message below |
| Disabled | `opacity-50` | `text-muted-foreground` | — |
| Read-only | `bg-muted` | `text-foreground` | — |

### 9.2 Validation Timing

| Trigger | When |
|---------|------|
| On blur | Individual field validation |
| On change | Password strength, character count |
| On submit | Full form schema validation (Zod) |
| Async | Domain uniqueness check (debounced 500ms) |

### 9.3 Multi-Step Wizard States

| Step State | Visual |
|------------|--------|
| Completed | Green checkmark, clickable to go back |
| Current | Primary dot, bold label |
| Upcoming | Gray dot, not clickable |
| Error | Red dot on step with errors, block forward navigation |

---

## 10. Data Table Interactions

### 10.1 Selection

| Action | Behavior |
|--------|----------|
| Click checkbox | Toggle single row |
| Click header checkbox | Toggle all on current page |
| `Shift+click` | Range select from last clicked |
| `Ctrl+click` | Toggle without clearing others |
| Click row (not checkbox) | Navigate to 360° (unless selection mode active) |
| Right-click row | Context menu (Edit, Score, Delete, Copy ID) |

### 10.2 Sorting

- Click header: none → asc → desc → none
- Multi-sort: `Shift+click` header adds secondary sort
- Sort indicator: `ArrowUp` / `ArrowDown` icon in header
- Server-side sort: updates URL `?sort=name&order=asc`, triggers API refetch

### 10.3 Column Management

| Action | Trigger |
|--------|---------|
| Resize column | Drag right edge of header |
| Reorder column | Drag header horizontally (in column config mode) |
| Show/hide column | Column visibility dropdown |
| Pin column | Pin left/right in column config |
| Reset columns | "Reset to default" in column menu |

### 10.4 Filtering

| Filter Type | UI Control |
|-------------|------------|
| Text search | Toolbar search input (debounced 300ms) |
| Status | Multi-select dropdown |
| Score range | Dual-handle slider |
| Date range | DatePicker range |
| Tags | Combobox multi-select |
| Country | Searchable select |

Active filters shown as `Chip` components below toolbar. "Clear all" link.

### 10.5 Pagination

| Mode | UI |
|------|-----|
| Standard | Page numbers + prev/next + page size selector (25/50/100) |
| Infinite scroll | Sentinel at bottom, "Load more" fallback button |
| Cursor-based | For very large datasets (search results) |

Show: "Showing 1–25 of 1,250" with total count.

---

## 11. AI Interaction States

### 11.1 AI Search States

| State | UI |
|-------|-----|
| Idle | Search bar with rotating placeholder examples |
| Typing | Standard input state |
| Parsing | Pulsing `Sparkles` icon, "Understanding your query..." |
| Parsed | `ParsedIntentPreview` with filter chips |
| Confirming | Credit cost badge visible, "Search" button enabled |
| Executing | `SearchProgress` with connector bars |
| Results | Redirect to results table |
| Parse failed | "Couldn't understand query" + "Try advanced filters" link |

### 11.2 AI Chat States

| State | UI |
|-------|-----|
| Empty | Welcome message with capability list + 3 suggested prompts |
| User typing | Standard input |
| Sending | Input disabled, send button shows spinner |
| Streaming | Assistant bubble grows with streamed text + cursor |
| Complete | Full message with optional result cards + suggestion chips |
| Error | "Failed to get response" + retry button in bubble |
| Context attached | Context panel shows entity card with "Remove" button |

### 11.3 Score States

| State | UI |
|-------|-----|
| Unscored | Gray gauge with "—" |
| Scoring | Gauge pulses, "Scoring..." label |
| Scored | Animated fill to score value, color by range, grade label |
| Stale | Clock icon + "Score from 30 days ago" + "Re-score" button |
| Failed | Red gauge outline + "Score failed" + retry |

---

## 12. Async Operation States

### 12.1 Polling Operations

| Operation | Poll Interval | Terminal States |
|-----------|---------------|-----------------|
| Import progress | 2s | `completed`, `failed`, `cancelled` |
| Export generation | 3s | `ready`, `failed` |
| Search execution | 1s | `completed`, `failed`, `partial` |
| Enrichment | 2s | `completed`, `failed` |
| CRM sync | 2s | `synced`, `failed` |

### 12.2 Cancel Operations

| Operation | Cancel Behavior |
|-----------|-----------------|
| Search | `DELETE /search/{id}` — stop connectors, show partial results |
| Import | `POST /imports/{id}/cancel` — stop at current row |
| Export | Client-side only (server completes) |
| AI chat stream | AbortController abort |

### 12.3 Background Operations

Operations that continue after navigation:

| Operation | Notification on Complete |
|-----------|-------------------------|
| Export | "Export ready: {filename}" → download link |
| Import | "Import complete: {n} records" → view link |
| Bulk score | "{n} entities scored" |
| Bulk enrich | "{n} entities enriched" |

User can navigate away; toast + notification bell on completion.

---

## 13. Global State Matrix

### Dashboard

| State | Condition | UI |
|-------|-----------|-----|
| Loading | `isLoading` | Full page skeleton |
| Empty | New org, no data | Default widgets with zero values |
| Success | Data loaded | Populated widgets |
| Error | API down | Error alert + cached data if available |
| Edit mode | `editMode: true` | Drag handles, widget catalog button |

### Entity List (Companies/Contacts)

| State | Condition | UI |
|-------|-----------|-----|
| Loading | `isLoading` | Table skeleton |
| Empty | `total === 0`, no filters | EmptyState with CTA |
| Filtered empty | `total === 0`, has filters | "No matches" + clear |
| Success | `data.length > 0` | Populated table |
| Error | `isError` | ErrorState with retry |
| Selecting | `selectedCount > 0` | BulkActionBar visible |

### Entity 360°

| State | Condition | UI |
|-------|-----------|-----|
| Loading | `isLoading` | Header + tab skeleton |
| Success | Entity loaded | Full 360° view |
| Not found | 404 | Redirect to 404 page |
| AI loading | Summary fetching | AI panel skeleton |
| AI error | Summary failed | "Summary unavailable" + retry |
| Read-only | `viewer` role | No write actions |

### Lead Discovery → Results

| State | Condition | UI |
|-------|-----------|-----|
| Idle | No query | Search hero + history |
| Parsing | AI debounce active | Intent preview skeleton |
| Ready | Intent parsed | Confirm UI |
| Searching | API in flight | SearchProgress |
| Results | Data returned | Results table |
| Partial | Some connectors failed | Results + per-connector warnings |
| No results | Zero matches | EmptyState "No results" |

### CRM Pipeline

| State | Condition | UI |
|-------|-----------|-----|
| Loading | Pipeline fetching | Column skeletons |
| Empty | No deals | EmptyState per column |
| Success | Deals loaded | Kanban board |
| Dragging | Card being dragged | Lifted card + column highlight |
| Error | Update failed | Revert + toast |

---

*Next: [06-technical-handoff.md](./06-technical-handoff.md) — Technical implementation handoff*