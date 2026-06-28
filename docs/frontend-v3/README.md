# Frontend Architecture v3.0 — AI Lead Intelligence

**Version 3.0** | **Codename: Aurora** | **Status: Implementation-Ready**  
**Last Updated:** June 28, 2026  
**Audience:** Senior frontend engineers, design systems team, QA, product

---

## Executive Summary

Frontend v3.0 defines the enterprise-grade user interface for **AI Lead Intelligence** — a B2B lead discovery, enrichment, scoring, and CRM platform. This release consolidates Phase 4 architecture into a single authoritative specification aligned with the live codebase (`frontend/`), Aurora design tokens (`src/styles/tokens.css`), and Phase 3/5 backend APIs.

v3.0 is not a cosmetic refresh. It establishes:

- **AI-native workflows** — natural language search, assistant, scoring, and recommendations as first-class surfaces
- **Enterprise data density** — virtualized tables, saved views, bulk actions, 360° entity workspaces
- **Production engineering standards** — Next.js 14 App Router, TypeScript strict mode, TanStack Query + Zustand, shadcn/ui, WCAG 2.1 AA

---

## Document Index

| # | Document | Scope |
|---|----------|-------|
| 0 | **[README.md](./README.md)** (this file) | Index, stack, versioning, sprint roadmap |
| 1 | **[01-information-architecture.md](./01-information-architecture.md)** | IA hierarchy, navigation model, mental model, personas, content taxonomy |
| 2 | **[02-screens-and-flows.md](./02-screens-and-flows.md)** | Site map, 72-screen inventory, user journeys, per-page specs (layout, components, APIs) |
| 3 | **[03-design-system.md](./03-design-system.md)** | Aurora tokens, typography, spacing, color, motion, light/dark themes |
| 4 | **[04-component-library.md](./04-component-library.md)** | Full component catalog with props, variants, accessibility, composition |
| 5 | **[05-states-and-interactions.md](./05-states-and-interactions.md)** | Loading, error, empty, success, permissions, keyboard, responsive behavior |
| 6 | **[06-technical-handoff.md](./06-technical-handoff.md)** | Folder structure, state management, API map per screen, performance, a11y, Storybook, build roadmap |

---

## Technology Stack

| Layer | Technology | Version | Notes |
|-------|------------|---------|-------|
| Framework | Next.js (App Router) | 14.2.x | Server Components default; client islands for interactivity |
| Language | TypeScript | 5.x | `strict: true`, path alias `@/*` |
| Styling | Tailwind CSS | 3.4.x | Token-driven via `tokens.css` + `tailwind.config.ts` |
| Components | shadcn/ui + Radix | Latest | Primitives in `src/components/ui/` |
| Icons | Lucide React | Latest | Replaces Heroicons |
| Server State | TanStack Query (React Query) | 5.x | Query keys per feature module |
| Client State | Zustand | 4.x | UI shell, theme, tables, AI chat |
| Forms | React Hook Form + Zod | Latest | All create/edit flows |
| Tables | TanStack Table + Virtual | Latest | `EntityDataTable`, `DataTable` |
| Charts | Recharts | 2.x | Dashboard + analytics widgets |
| Command UI | cmdk | Latest | Command palette (`⌘K`) |
| Toasts | Sonner | Latest | Global feedback |
| Animation | CSS transitions + Framer Motion | Optional | Page enter, modals, kanban drag |
| Auth | JWT + refresh rotation | — | Middleware route protection |

---

## Platform Modules (v3.0)

```text
AI Lead Intelligence
├── Home          Dashboard (customizable widgets)
├── Discover      Lead Discovery, Search Results, Saved Searches, Lists, Segments
├── Records       Companies, Contacts (list + 360°)
├── Intelligence  AI Assistant, Lead Scoring
├── CRM           Pipeline, Deals, Tasks, Activities, Calendar
├── Analytics     Reports hub + 6 report types
├── Data Ops      Imports, Exports
├── Settings      Organization, Users, Integrations, Billing, API Keys, Profile
├── Admin         Audit, Feature Flags, System Health, Connectors
└── System        Auth, Notifications, Help, Developer Portal, Error pages
```

**Total screens:** 72 (see [02-screens-and-flows.md](./02-screens-and-flows.md))

---

## v3.0 vs Phase 4 — What Changed

| Area | Phase 4 (v1.0) | Frontend v3.0 |
|------|----------------|---------------|
| Design system | Blue primary (`#2563EB`) | Aurora indigo (`rgb(79 70 229)`) |
| Route prefix | `/discover` | `/search` (matches codebase) |
| Status bar | Not specified | 32px bottom bar (credits, sync, env) |
| Token format | Hex CSS vars | HSL channel vars (shadcn convention) |
| Screen count | 68 | 72 (+ Developer sub-pages, Calendar) |
| Implementation | Target architecture | Aligned to existing `frontend/src` structure |
| Backend | Phase 3 API | Phase 3 + Phase 5 discovery orchestrator |

---

## UX Pillars (Non-Negotiable)

1. **Command Palette** — `Ctrl+K` / `⌘K` for navigation, actions, quick search
2. **AI-First Global Search** — NL query in top bar with intent preview
3. **Customizable Dashboard** — drag/resize widgets, per-user layout persistence
4. **Enterprise Data Tables** — virtualization, column config, saved views, bulk actions
5. **360° Entity Views** — Company and Contact unified workspaces with AI side panel
6. **Accessibility & Keyboard** — WCAG 2.1 AA, full shortcut map, reduced motion
7. **Theme System** — Light, dark, system; high-contrast support

---

## Backend Integration Map

| Frontend Module | Primary API Namespace |
|-----------------|----------------------|
| Auth | `POST /auth/*` |
| Dashboard | `GET /analytics/dashboard`, `GET /analytics/full` |
| Companies | `GET/POST/PATCH/DELETE /companies`, `GET /companies/{id}` |
| Contacts | `GET/POST/PATCH/DELETE /contacts` |
| Lead Discovery | `POST /search`, `POST /search/ai`, `GET /search/{id}/results` |
| AI Assistant | `POST /search/ai`, `GET /ai/recommendations`, `POST /ai/score` |
| CRM | `GET/POST /crm/pipelines`, `/crm/deals`, `/crm/tasks`, `/crm/activities` |
| Imports/Exports | `POST /imports`, `GET /imports/{id}`, `POST /exports` |
| Analytics | `GET /analytics/*` |
| Settings | `PATCH /organizations/current`, `PATCH /users/me` |
| Admin | `GET /admin/audit-logs`, `/admin/feature-flags`, `/admin/health` |
| Notifications | `GET /notifications`, `PATCH /notifications/{id}/read` |

Full API reference: `docs/phase3/api-specification.md`, `docs/phase5/api-specification.md`

---

## Implementation Sprints (10-Week Roadmap)

| Sprint | Weeks | Deliverables |
|--------|-------|--------------|
| **S1** | 1–2 | App shell v3, Aurora tokens, shadcn migration, theme, command palette, status bar |
| **S2** | 3–4 | Data table system, saved views, Company/Contact 360°, global AI search |
| **S3** | 5–6 | Lead Discovery flow, Search Results, Saved Searches, Lists, Segments |
| **S4** | 7–8 | CRM Kanban, AI Assistant, imports/exports wizards |
| **S5** | 9–10 | Dashboard widgets, analytics reports, admin panel, a11y audit, E2E, Storybook |

Detailed task breakdown: [06-technical-handoff.md §12](./06-technical-handoff.md#12-build-roadmap)

---

## Source of Truth Files

| Artifact | Path |
|----------|------|
| Design tokens | `frontend/src/styles/tokens.css` |
| Navigation config | `frontend/src/config/navigation.ts` |
| App routes | `frontend/src/app/` |
| Domain types | `frontend/src/types/index.ts` |
| Zustand stores | `frontend/src/stores/` |
| Feature modules | `frontend/src/features/` |

---

## How to Use This Documentation

1. **Product / Design** — Start with [01](./01-information-architecture.md) and [02](./02-screens-and-flows.md) for flows and screen inventory
2. **Design Systems** — [03](./03-design-system.md) and [04](./04-component-library.md) for tokens and components
3. **Engineering** — [06](./06-technical-handoff.md) for folder structure, hooks, API wiring
4. **QA** — [05](./05-states-and-interactions.md) for state matrices and interaction specs

---

## Related Documentation

| Document | Location |
|----------|----------|
| Phase 4 (superseded) | `docs/phase4/` |
| Backend API v3.0 | `docs/phase3/api-specification.md` |
| Discovery Platform | `docs/phase5/discovery-platform-architecture.md` |
| Database schema | `docs/database.md` |

---

*Frontend Architecture v3.0 — AI Lead Intelligence Platform*