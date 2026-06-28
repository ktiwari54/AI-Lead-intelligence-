# Phase 4 — Screen Specifications

**Version 1.0** | Wireframes, screen inventory, and high-fidelity UI specs.

---

## 1. Screen Inventory

### Total: 68 screens

| Module | Screens | Count |
|--------|---------|-------|
| Auth | Login, Register, Forgot Password, Reset Password, 2FA | 5 |
| Dashboard | Executive Dashboard, Customize Mode | 2 |
| Discover | Lead Discovery, Search Results, Saved Searches, Lists, Segments, List Detail | 6 |
| Companies | List, 360° (6 tabs), Create, Edit, Merge | 10 |
| Contacts | List, 360° (5 tabs), Create, Edit, Merge | 10 |
| AI | Assistant (full), Scoring Dashboard | 2 |
| CRM | Pipeline, Deal Detail, Tasks, Activities, Calendar | 5 |
| Imports | Hub, Wizard (4 steps), Progress, History | 6 |
| Exports | Hub, Wizard (3 steps), History | 4 |
| Analytics | Hub, 6 report types | 7 |
| Notifications | Center, Preferences | 2 |
| Settings | 8 sub-pages | 8 |
| Admin | 6 sub-pages | 6 |
| System | 404, 403, Error, Loading | 4 |
| Developer | API Docs, Webhooks | 2 |

---

## 2. Wireframes

### 2.1 Dashboard (Executive)

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ Dashboard                                    [Customize] [+ Add Widget]      │
├─────────────────────────────────────────────────────────────────────────────┤
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐            │
│ │Companies │ │ Contacts │ │Avg Score │ │ Credits  │ │ Searches │            │
│ │  1,250   │ │  8,400   │ │  62.3    │ │  3,766   │ │   89     │            │
│ │  +12%    │ │  +8%     │ │  +2.1    │ │  remaining│ │  /month  │            │
│ └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘            │
├─────────────────────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────┐ ┌─────────────────────┐ ┌─────────────────┐ │
│ │ Lead Pipeline (funnel)      │ │ Industry Breakdown  │ │ Connector Health│ │
│ │                             │ │     [pie chart]     │ │ apollo    ✓     │ │
│ │  ████████████ Prospect 120  │ │                     │ │ clearbit  ✓     │ │
│ │  ████████ Qualified 85      │ │                     │ │ hunter    ⚠     │ │
│ │  ████ Proposal 42           │ │                     │ │                 │ │
│ │  ██ Closed 18               │ │                     │ │                 │ │
│ └─────────────────────────────┘ └─────────────────────┘ └─────────────────┘ │
├─────────────────────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────┐ ┌─────────────────────────────────────────┐ │
│ │ Search Trends (area chart)  │ │ Activity Feed                           │ │
│ │                             │ │ • John scored Acme Inc (2m ago)         │ │
│ │                             │ │ • Export completed: 250 contacts (1h)   │ │
│ │                             │ │ • New search: SaaS in CA (2h)           │ │
│ └─────────────────────────────┘ └─────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────┐ ┌─────────────────────┐                     │
│ │ Top Companies (table)       │ │ AI Recommendations  │                     │
│ │ Acme Inc        92          │ │ • Follow up TechCo  │                     │
│ │ TechStart       88          │ │ • Score 15 contacts │                     │
│ └─────────────────────────────┘ └─────────────────────┘                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Lead Discovery

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ Lead Discovery                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 🔍  Find logistics companies in Dubai with verified emails         [AI]│ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ ┌─ AI Interpretation ─────────────────────────────────────────────────────┐ │
│ │ Intent: find_companies · Location: Dubai, AE · Industry: logistics    │ │
│ │ Filter: email_verified=true · Connectors: apollo, clearbit             │ │
│ │                                              [Edit Filters] [Search →]  │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ ┌─ Advanced Filters (collapsible) ────────────────────────────────────────┐ │
│ │ Industry [____] Country [____] Employees [min__ max__]                  │ │
│ │ Technologies [____] Lead Score [min__] Seniority [____]                  │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ ┌─ Search History ─────────────┐  ┌─ Saved Searches ─────────────────────┐ │
│ │ SaaS companies in CA (2h)   │  │ ★ West Coast SaaS                    │ │
│ │ VP Eng fintech NYC (1d)     │  │ ★ Enterprise fintech                 │ │
│ └─────────────────────────────┘  └──────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.3 Search Results

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ Results: 42 companies · 10 credits used · 2.3s                              │
├─────────────────────────────────────────────────────────────────────────────┤
│ [☑ Select All]  3 selected  [Add to List] [Export] [Score] [Save Search]  │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ ☐ │ Name ▲      │ Domain      │ Industry  │ Country │ Score │ Conf.   │ │
│ │───┼─────────────┼─────────────┼───────────┼─────────┼───────┼─────────│ │
│ │ ☐ │ Acme Log    │ acmelog.com │ logistics │ AE      │ 85    │ 0.95    │ │
│ │ ☐ │ Gulf Trans  │ gulftrans.ae│ logistics │ AE      │ 78    │ 0.91    │ │
│ │ ☐ │ Dubai Ship  │ dship.com   │ logistics │ AE      │ 72    │ 0.87    │ │
│ │   │ ...         │             │           │         │       │         │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│ Showing 1-25 of 42                              [< 1 2 >]  [∞ Scroll]      │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.4 Company 360°

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ ← Companies    Acme Inc                                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│ [🏢] Acme Inc  acme.com  SaaS  San Francisco, US                           │
│ Lead Score: 82 ████████░░  Pursue                                          │
│ [Enrich] [Score] [Sync CRM ▾] [Export] [•••]                              │
├──────────────────────────────────────────────┬──────────────────────────────┤
│ Overview | Contacts(12) | Tech | Timeline    │ AI SUMMARY                   │
│              | Files | Relationships         │ "Acme Inc is a mid-market   │
├──────────────────────────────────────────────┤  SaaS platform serving..."    │
│ Description                                │                              │
│ Acme provides cloud-based workflow...       │ RECOMMENDATIONS              │
│                                             │ → Contact VP Engineering      │
│ Firmographics                               │ → Similar: TechCo Inc (89)   │
│ Employees: 250  Revenue: $50M               │                              │
│ Founded: 2015  Funding: Series B            │ CRM STATUS                   │
│                                             │ ✓ Salesforce (synced 2h ago) │
│ Social Links                                │                              │
│ [LinkedIn] [Twitter]                        │ TAGS                         │
│                                             │ [enterprise] [saas] [+Add]   │
└─────────────────────────────────────────────┴──────────────────────────────┘
```

### 2.5 CRM Pipeline (Kanban)

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ Pipeline: Enterprise Sales                    [+ Deal] [Filter] [View ▾]   │
├─────────────────────────────────────────────────────────────────────────────┤
│ ┌─ Prospect ────┐ ┌─ Qualified ───┐ ┌─ Proposal ────┐ ┌─ Closed Won ──┐  │
│ │ ┌───────────┐ │ │ ┌───────────┐ │ │ ┌───────────┐ │ │ ┌───────────┐ │  │
│ │ │Acme Corp  │ │ │ │TechStart  │ │ │ │DataFlow   │ │ │ │CloudNine  │ │  │
│ │ │$50,000    │ │ │ │$120,000   │ │ │ │$75,000    │ │ │ │$200,000   │ │  │
│ │ │John Smith │ │ │ │Jane Doe   │ │ │ │Bob Lee    │ │ │ │Alice Kim  │ │  │
│ │ │Score: 85  │ │ │ │Score: 91  │ │ │ │Score: 78  │ │ │ │Score: 95  │ │  │
│ │ └───────────┘ │ │ └───────────┘ │ │ └───────────┘ │ │ └───────────┘ │  │
│ │ ┌───────────┐ │ │               │ │               │ │               │  │
│ │ │NewCo Inc  │ │ │               │ │               │ │               │  │
│ │ │$30,000    │ │ │               │ │               │ │               │  │
│ │ └───────────┘ │ │               │ │               │ │               │  │
│ │  + Add Deal   │ │  + Add Deal   │ │  + Add Deal   │ │               │  │
│ └───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘  │
│ Total: $500K pipeline · 18 deals · 4 won this month                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.6 Import Wizard

```text
Step 1: Upload ── Step 2: Map ── Step 3: Preview ── Step 4: Import
                  ●────────────────○────────────────○

┌─────────────────────────────────────────────────────────────────────────────┐
│ Import Companies                                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│ ┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐ │
│ │                                                                       │ │
│ │         📁 Drag & drop CSV or Excel file here                         │ │
│ │              or [Browse Files]                                        │ │
│ │                                                                       │ │
│ │         Supported: .csv, .xlsx, .json (max 50MB)                   │ │
│ └ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘ │
│                                                                             │
│ Recent Imports                                                              │
│ companies_2026-06-15.csv · 1,250 rows · Completed · [View]                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.7 AI Assistant (Full Page)

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ AI Assistant                    [Pin] [History ▾] [New Chat]               │
├──────────────────────────────────────────────┬──────────────────────────────┤
│                                              │ CONTEXT                      │
│  🤖 Welcome! I can help you discover leads,  │ Entity: Acme Inc             │
│     score prospects, and draft outreach.     │ Score: 82                    │
│                                              │ Industry: SaaS               │
│  👤 Find VP of Engineering at fintech         │                              │
│     companies in NYC                         │ QUICK ACTIONS                │
│                                              │ [Score this company]         │
│  🤖 I found 23 contacts. Top matches:        │ [Find similar companies]     │
│  ┌────────────────────────────────────────┐  │ [Draft outreach email]      │
│  │ John Smith · VP Eng · FinTech Co · 91 │  │ [Summarize]                  │
│  │ Jane Doe · VP Eng · PayFlow · 88      │  │                              │
│  │ Bob Lee · CTO · DataBank · 85         │  │ PINNED CHATS                 │
│  └────────────────────────────────────────┘  │ • Fintech NYC search         │
│                                              │ • Q2 pipeline review         │
│  Suggested: "Score all 23" · "Add to list"   │                              │
├──────────────────────────────────────────────┤                              │
│ [📎 Attach] [🎤]  Ask anything...     [Send] │                              │
└──────────────────────────────────────────────┴──────────────────────────────┘
```

### 2.8 Command Palette

```text
                    ┌─────────────────────────────────────┐
                    │ 🔍 Type a command or search...       │
                    ├─────────────────────────────────────┤
                    │ RECENT                               │
                    │ → Acme Inc (company)                 │
                    │ → Lead Discovery                     │
                    ├─────────────────────────────────────┤
                    │ NAVIGATION                           │
                    │ → Go to Dashboard                    │
                    │ → Go to Companies                    │
                    │ → Go to Lead Discovery               │
                    ├─────────────────────────────────────┤
                    │ ACTIONS                              │
                    │ + Create new company                 │
                    │ + Start AI search                    │
                    │ + Export contacts                    │
                    │ ◐ Toggle dark mode                   │
                    └─────────────────────────────────────┘
```

---

## 3. High-Fidelity UI Specifications

### 3.1 Dashboard KPI Card

| Property | Value |
|----------|-------|
| Container | `bg-card border rounded-lg p-5 shadow-sm` |
| Title | `text-sm text-muted-foreground` |
| Value | `text-2xl font-bold text-foreground` |
| Trend | `text-xs` green (+) / red (-) with arrow icon |
| Icon container | `h-12 w-12 rounded-xl bg-primary/10` |
| Hover | `shadow-md transition-shadow 150ms` |
| Min width | 200px in grid |

### 3.2 Global Search Bar

| Property | Value |
|----------|-------|
| Width | `flex-1 max-w-2xl` |
| Height | 40px |
| Background | `bg-muted/50` |
| Border | `border border-border rounded-lg` |
| Focus | `ring-2 ring-ring border-primary` |
| Placeholder | `text-muted-foreground` — rotating AI examples |
| Left icon | `Search` 16px `text-muted-foreground` |
| Right badge | `⌘K` keyboard hint, `bg-muted rounded px-1.5 text-xs` |
| AI mode indicator | `Sparkles` icon glows when NL detected |

### 3.3 Data Table Row

| Property | Value |
|----------|-------|
| Row height | 48px (40px compact mode) |
| Hover | `bg-muted/50` |
| Selected | `bg-primary/5 border-l-2 border-l-primary` |
| Cell padding | `px-4 py-2` |
| Header | `text-xs font-medium uppercase text-muted-foreground` |
| Sortable header | Hover underline + arrow icon |
| Sticky header | `sticky top-0 bg-card z-10` |
| Checkbox column | 48px fixed width, pinned left |
| Score column | `ScoreGauge` inline, 32px |
| Actions column | `MoreHorizontal` icon, 48px pinned right |

### 3.4 Lead Score Gauge

| Property | Value |
|----------|-------|
| Type | Circular (48px) in tables, Linear (full width) in 360° |
| Track | `stroke-muted` 4px |
| Fill | Color by range (see design tokens) |
| Value | Center text `text-sm font-bold` |
| Animation | Animate from 0 on mount, 600ms ease-out |
| Label | "Pursue" / "Nurture" / "Deprioritize" below gauge |

### 3.5 Sidebar Nav Item

| State | Styles |
|-------|--------|
| Default | `text-muted-foreground px-3 py-2 rounded-lg text-sm` |
| Hover | `bg-accent text-foreground` |
| Active | `bg-primary/10 text-primary font-medium` |
| Collapsed | Icon only, tooltip on hover |
| Section label | `text-xs uppercase text-muted-foreground px-3 pt-4 pb-1` |

### 3.6 Notification Item

| Property | Value |
|----------|-------|
| Container | `flex gap-3 p-3 hover:bg-muted/50 rounded-lg` |
| Unread dot | `h-2 w-2 rounded-full bg-primary` |
| Title | `text-sm font-medium` |
| Body | `text-sm text-muted-foreground line-clamp-2` |
| Time | `text-xs text-muted-foreground` |
| Icon | Type-specific (score, export, search) 20px |

### 3.7 Widget (Dashboard)

| Property | Value |
|----------|-------|
| Container | `bg-card border rounded-xl p-4 shadow-sm` |
| Header | `flex justify-between items-center mb-3` |
| Title | `text-sm font-semibold` |
| Drag handle | `GripVertical` icon, visible in edit mode only |
| Resize | Bottom-right corner handle in edit mode |
| Min size | 1×1 grid unit (200×160px) |
| Loading | Skeleton matching chart/table shape |

---

*End of Phase 4 Screen Specifications*