# Phase 4 — Design System Documentation

**Version 1.0** | Codename: **Aurora**

Enterprise design system for AI Lead Intelligence Platform. Comparable density and clarity to Linear, with data-heavy patterns from HubSpot/Salesforce.

---

## Table of Contents

1. [Design Principles](#1-design-principles)
2. [Design Tokens](#2-design-tokens)
3. [Theme Specification](#3-theme-specification)
4. [Typography](#4-typography)
5. [Spacing & Grid](#5-spacing--grid)
6. [Elevation & Borders](#6-elevation--borders)
7. [Color System](#7-color-system)
8. [Component Library](#8-component-library)
9. [Responsive Layout](#9-responsive-layout)
10. [Motion & Animation](#10-motion--animation)
11. [States](#11-states)
12. [Icons](#12-icons)

---

## 1. Design Principles

| Principle | Implementation |
|-----------|----------------|
| Enterprise First | Dense data tables, keyboard shortcuts, bulk actions |
| Minimalist | Remove chrome; content-first layouts |
| Fast Navigation | Command palette, breadcrumbs, persistent sidebar |
| AI Native | Search bar prominence, AI panels, confidence indicators |
| Accessible | WCAG AA contrast, focus rings, screen reader labels |
| Consistent | Token-driven; no one-off colors or spacing |

---

## 2. Design Tokens

Tokens live in `frontend/src/styles/tokens.css` as CSS custom properties, consumed by Tailwind.

### Token Categories

```text
--color-*          Semantic colors
--font-*           Typography
--space-*          Spacing scale
--radius-*         Border radius
--shadow-*         Elevation
--z-*              Z-index scale
--duration-*       Animation timing
--sidebar-*        Layout dimensions
```

### Semantic Color Tokens

| Token | Light | Dark | Usage |
|-------|-------|------|-------|
| `--background` | `#FAFAFA` | `#09090B` | Page background |
| `--foreground` | `#18181B` | `#FAFAFA` | Primary text |
| `--card` | `#FFFFFF` | `#18181B` | Card surfaces |
| `--card-foreground` | `#18181B` | `#FAFAFA` | Card text |
| `--primary` | `#2563EB` | `#3B82F6` | Primary actions |
| `--primary-foreground` | `#FFFFFF` | `#FFFFFF` | On primary |
| `--secondary` | `#F4F4F5` | `#27272A` | Secondary surfaces |
| `--muted` | `#F4F4F5` | `#27272A` | Muted backgrounds |
| `--muted-foreground` | `#71717A` | `#A1A1AA` | Secondary text |
| `--accent` | `#F4F4F5` | `#27272A` | Hover states |
| `--destructive` | `#DC2626` | `#EF4444` | Delete, errors |
| `--border` | `#E4E4E7` | `#27272A` | Borders |
| `--ring` | `#2563EB` | `#3B82F6` | Focus rings |
| `--success` | `#16A34A` | `#22C55E` | Verified, won |
| `--warning` | `#D97706` | `#F59E0B` | Risky, pending |
| `--info` | `#2563EB` | `#3B82F6` | Informational |

### Lead Score Colors

| Range | Token | Color |
|-------|-------|-------|
| 80–100 | `--score-excellent` | `#16A34A` |
| 60–79 | `--score-good` | `#2563EB` |
| 40–59 | `--score-fair` | `#D97706` |
| 0–39 | `--score-poor` | `#DC2626` |

### Spacing Scale (4px base)

| Token | Value | Usage |
|-------|-------|-------|
| `--space-1` | 4px | Tight gaps |
| `--space-2` | 8px | Icon gaps |
| `--space-3` | 12px | Input padding |
| `--space-4` | 16px | Card padding |
| `--space-5` | 20px | — |
| `--space-6` | 24px | Section gaps |
| `--space-8` | 32px | Page sections |
| `--space-10` | 40px | — |
| `--space-12` | 48px | Large sections |

### Radius Scale

| Token | Value | Usage |
|-------|-------|-------|
| `--radius-sm` | 4px | Badges, chips |
| `--radius-md` | 6px | Inputs, buttons |
| `--radius-lg` | 8px | Cards |
| `--radius-xl` | 12px | Modals, panels |
| `--radius-full` | 9999px | Avatars, pills |

### Shadow Scale

| Token | Value | Usage |
|-------|-------|-------|
| `--shadow-sm` | `0 1px 2px rgba(0,0,0,0.05)` | Cards at rest |
| `--shadow-md` | `0 4px 6px rgba(0,0,0,0.07)` | Dropdowns |
| `--shadow-lg` | `0 10px 15px rgba(0,0,0,0.10)` | Modals |
| `--shadow-xl` | `0 20px 25px rgba(0,0,0,0.15)` | Command palette |

---

## 3. Theme Specification

### Theme Modes

| Mode | Class | Default |
|------|-------|---------|
| Light | `light` | No |
| Dark | `dark` | No |
| System | follows `prefers-color-scheme` | **Yes** |

### Implementation

```typescript
// stores/theme-store.ts
type Theme = 'light' | 'dark' | 'system'

// On mount: read localStorage → apply class to <html>
// On change: persist + toggle class
// System: listen to matchMedia('(prefers-color-scheme: dark)')
```

### Theme Toggle Locations

- Settings > Preferences
- User menu dropdown
- Command palette: "Toggle dark mode"

### High Contrast Mode

- Respects `prefers-contrast: more`
- Increases border width to 2px
- Removes subtle gray backgrounds

---

## 4. Typography

### Font Stack

| Role | Family | Weight |
|------|--------|--------|
| UI | `Inter`, system-ui, sans-serif | 400–700 |
| Mono | `JetBrains Mono`, monospace | 400–500 |
| Display | Inter (same) | 600–700 |

### Type Scale

| Name | Size | Line Height | Weight | Usage |
|------|------|-------------|--------|-------|
| `display-lg` | 30px / 1.875rem | 36px | 700 | Dashboard hero |
| `display-sm` | 24px / 1.5rem | 32px | 600 | Page titles |
| `heading-lg` | 20px / 1.25rem | 28px | 600 | Section headers |
| `heading-md` | 16px / 1rem | 24px | 600 | Card titles |
| `heading-sm` | 14px / 0.875rem | 20px | 600 | Table headers |
| `body-lg` | 16px / 1rem | 24px | 400 | Body text |
| `body-md` | 14px / 0.875rem | 20px | 400 | Default UI |
| `body-sm` | 12px / 0.75rem | 16px | 400 | Captions, meta |
| `mono-sm` | 12px / 0.75rem | 16px | 400 | Code, IDs |

### Tailwind Mapping

```typescript
fontSize: {
  'display-lg': ['1.875rem', { lineHeight: '2.25rem', fontWeight: '700' }],
  'display-sm': ['1.5rem', { lineHeight: '2rem', fontWeight: '600' }],
  // ...
}
```

---

## 5. Spacing & Grid

### Layout Grid

| Breakpoint | Columns | Gutter | Margin |
|------------|---------|--------|--------|
| Mobile (<640) | 4 | 16px | 16px |
| Tablet (640–1024) | 8 | 24px | 24px |
| Desktop (1024–1440) | 12 | 24px | 32px |
| Wide (1440+) | 12 | 32px | 48px |
| Ultra-wide (1920+) | 16 | 32px | 64px |

### Dashboard Widget Grid

- 12-column CSS Grid
- Widget sizes: `1×1`, `2×1`, `2×2`, `3×2`, `4×2`, `full`
- Gap: 16px (`gap-4`)
- Drag handle: top-right corner in edit mode

### Content Max Width

| Context | Max Width |
|---------|-----------|
| Data tables | 100% (fluid) |
| Forms | 640px |
| Settings | 768px |
| Marketing/auth | 480px |
| AI chat | 800px |

---

## 6. Elevation & Borders

### Border Widths

| Token | Value | Usage |
|-------|-------|-------|
| Default | 1px | Cards, inputs, tables |
| Thick | 2px | Focus, high contrast |
| None | 0 | Flush panels |

### Z-Index Scale

| Token | Value | Element |
|-------|-------|---------|
| `--z-base` | 0 | Content |
| `--z-dropdown` | 10 | Dropdowns |
| `--z-sticky` | 20 | Sticky headers |
| `--z-sidebar` | 30 | Sidebar |
| `--z-topbar` | 40 | Top navigation |
| `--z-overlay` | 50 | Modals, command palette |
| `--z-toast` | 60 | Toasts |

---

## 7. Color System

### Status Badge Colors

| Status | Background (light) | Text | Example |
|--------|-------------------|------|---------|
| Active | `success/10` | `success` | Verified |
| Pending | `warning/10` | `warning` | Processing |
| Error | `destructive/10` | `destructive` | Failed |
| Neutral | `muted` | `muted-foreground` | Draft |
| Info | `primary/10` | `primary` | New |

### Chart Palette (8 colors, colorblind-safe)

```text
#2563EB  #16A34A  #D97706  #DC2626
#7C3AED  #0891B2  #DB2777  #65A30D
```

### Map Choropleth

- Sequential blue scale for density
- Single hue: `#EFF6FF` → `#1E40AF`

---

## 8. Component Library

Built on **shadcn/ui** (Radix primitives + Tailwind). All components in `src/components/ui/`.

### Navigation Components

| Component | Props | Notes |
|-----------|-------|-------|
| `AppShell` | `children` | Root layout wrapper |
| `Sidebar` | `collapsed`, `onToggle` | Collapsible nav |
| `SidebarNav` | `items`, `activePath` | Nav link group |
| `TopBar` | `breadcrumbs`, `actions` | Header bar |
| `Breadcrumbs` | `items: {label, href}[]` | Auto from route |
| `OrgSwitcher` | `orgs`, `current` | Tenant switch |
| `GlobalSearch` | `onSearch`, `onAISearch` | AI-first search |
| `CommandPalette` | — | cmdk wrapper |
| `UserMenu` | `user`, `onLogout` | Avatar dropdown |

### Form Components

| Component | Variants |
|-----------|----------|
| `Button` | default, destructive, outline, secondary, ghost, link |
| `Input` | default, error, with-icon |
| `Textarea` | default, auto-resize |
| `Select` | single, multi, searchable |
| `Combobox` | async options (for autocomplete) |
| `DatePicker` | single, range |
| `Checkbox` | default, indeterminate |
| `RadioGroup` | horizontal, vertical |
| `Switch` | default |
| `Slider` | single, range |
| `FormField` | label + input + error (RHF wrapper) |
| `FileUpload` | drag-drop zone |

### Data Components

| Component | Key Features |
|-----------|--------------|
| `DataTable` | Virtual scroll, sort, filter, select |
| `DataTableToolbar` | Search, columns, views, bulk actions |
| `DataTablePagination` | Page size selector |
| `SavedViewsMenu` | CRUD saved views |
| `ColumnHeader` | Sort indicator, resize handle |
| `BulkActionBar` | Sticky bottom bar on selection |
| `EmptyState` | Icon + title + CTA |
| `Skeleton` | Table, card, text variants |

### Display Components

| Component | Usage |
|-----------|-------|
| `Card` | Widget container |
| `KpiCard` | Metric + trend + sparkline |
| `Badge` | Status, tag |
| `Chip` | Removable filter tag |
| `Avatar` | User, company logo |
| `ScoreGauge` | Circular/linear lead score |
| `ConfidenceBar` | AI result confidence |
| `Timeline` | Activity feed |
| `TechStack` | Technology badges grid |
| `VerificationBadge` | Email/phone status |

### Overlay Components

| Component | Usage |
|-----------|-------|
| `Dialog` | Confirmations, forms |
| `Drawer` | AI assistant, filters |
| `Sheet` | Mobile nav, side panels |
| `Popover` | Quick previews |
| `Tooltip` | Icon explanations |
| `Toast` | Success/error feedback (sonner) |
| `DropdownMenu` | Row actions, user menu |

### AI Components

| Component | Usage |
|-----------|-------|
| `AIChat` | Message list + input |
| `AIMessage` | User/assistant bubble |
| `AIResultCard` | Search result in chat |
| `RecommendationPanel` | Next-best-actions |
| `AISummaryCard` | Entity narrative |
| `SearchProgress` | Connector job progress |
| `ParsedIntentPreview` | NL → filters display |

### CRM Components

| Component | Usage |
|-----------|-------|
| `KanbanBoard` | Pipeline columns |
| `KanbanCard` | Deal card |
| `DealStageBar` | Stage progression |
| `TaskItem` | Checkbox + due date |
| `CalendarView` | Month/week/day |
| `ActivityFeed` | Chronological events |

### Chart Components

| Component | Chart Type |
|-----------|------------|
| `AreaChart` | Search trends |
| `BarChart` | Industry breakdown |
| `PieChart` | Score distribution |
| `LineChart` | Lead velocity |
| `MapWidget` | Country distribution |
| `Sparkline` | Inline KPI trend |

---

## 9. Responsive Layout

### Breakpoints

| Name | Min Width | Tailwind |
|------|-----------|----------|
| Mobile | 0 | default |
| Tablet | 640px | `sm:` |
| Laptop | 1024px | `lg:` |
| Desktop | 1280px | `xl:` |
| Wide | 1536px | `2xl:` |

### Responsive Behavior

| Component | Mobile | Tablet | Desktop |
|-----------|--------|--------|---------|
| Sidebar | Hidden (overlay) | Collapsed | Expanded |
| Top bar search | Icon → full screen | Compact | Full width |
| Data table | Card list view | Horizontal scroll | Full table |
| 360° layout | Single column | Tabs only | Tabs + right panel |
| Dashboard grid | 1 column | 2 columns | 12-col grid |
| Command palette | Full screen | Centered modal | Centered modal |
| Kanban | Single column scroll | 2 columns | All columns |

### Touch Targets

- Minimum: 44×44px (WCAG 2.5.5)
- Table row height: 48px on touch devices
- Button height: 40px default, 36px compact

---

## 10. Motion & Animation

### Timing

| Token | Duration | Easing | Usage |
|-------|----------|--------|-------|
| `--duration-fast` | 150ms | ease-out | Hover, toggle |
| `--duration-normal` | 250ms | ease-in-out | Panel slide |
| `--duration-slow` | 400ms | ease-in-out | Page transition |

### Framer Motion Patterns

| Pattern | Animation |
|---------|-----------|
| Page enter | Fade + slide up 8px |
| Modal | Scale 0.95 → 1 + fade |
| Sidebar collapse | Width transition |
| Toast | Slide in from right |
| Skeleton | Pulse shimmer |
| List item add | Height expand + fade |
| Kanban drag | Scale 1.02 + shadow lift |

### Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## 11. States

### Loading States

| Context | Pattern |
|---------|---------|
| Page | Full-page skeleton matching layout |
| Table | 10 skeleton rows |
| Card | Skeleton card with shimmer |
| Button | Spinner + disabled |
| Search | Pulsing search bar + "Searching..." |
| AI Chat | Typing indicator (3 dots) |

### Empty States

| Context | Icon | Title | CTA |
|---------|------|-------|-----|
| No companies | Building | "No companies yet" | "Add Company" |
| No search results | Search | "No results found" | "Broaden filters" |
| No notifications | Bell | "All caught up" | — |
| Empty pipeline | Kanban | "No deals in pipeline" | "Create Deal" |

### Error States

| Type | Display |
|------|---------|
| Page error | Error boundary with retry |
| Form field | Red border + message below |
| API error | Toast + inline message |
| 404 | Illustration + "Go to Dashboard" |
| 403 | "You don't have permission" |
| Network | Banner: "Connection lost. Retrying..." |

### Success States

- Toast notification (3s auto-dismiss)
- Inline checkmark animation (forms)
- Progress bar completion flash (imports)

---

## 12. Icons

### Library: Lucide React

| Category | Icons |
|----------|-------|
| Navigation | `LayoutDashboard`, `Building2`, `Users`, `Search`, `Sparkles` |
| Actions | `Plus`, `Download`, `Upload`, `Trash2`, `Edit`, `MoreHorizontal` |
| Status | `CheckCircle`, `AlertCircle`, `XCircle`, `Clock`, `Loader2` |
| AI | `Sparkles`, `Brain`, `Wand2`, `MessageSquare` |
| CRM | `Kanban`, `Calendar`, `CheckSquare`, `DollarSign` |
| Data | `Filter`, `ArrowUpDown`, `Columns3`, `Eye` |

### Icon Sizes

| Size | Pixels | Usage |
|------|--------|-------|
| `xs` | 14px | Inline with small text |
| `sm` | 16px | Buttons, nav |
| `md` | 20px | Default |
| `lg` | 24px | Page headers |
| `xl` | 32px | Empty states |

---

*End of Phase 4 Design System Documentation*