# Phase 4 — Enterprise Frontend Architecture & Design System

**Version 1.0** | AI Lead Intelligence Platform

---

## Deliverables Index

| # | Deliverable | Document |
|---|-------------|----------|
| 1 | Information Architecture | [frontend-architecture.md §1](./frontend-architecture.md#1-information-architecture) |
| 2 | Navigation Map | [frontend-architecture.md §2](./frontend-architecture.md#2-navigation-map) |
| 3 | User Flows | [frontend-architecture.md §3](./frontend-architecture.md#3-user-flows) |
| 4 | Screen Inventory | [screen-specifications.md §1](./screen-specifications.md#1-screen-inventory) |
| 5 | Wireframes (low fidelity) | [screen-specifications.md §2](./screen-specifications.md#2-wireframes) |
| 6 | High-Fidelity UI Specifications | [screen-specifications.md §3](./screen-specifications.md#3-high-fidelity-ui-specifications) |
| 7 | Design System Documentation | [design-system.md](./design-system.md) |
| 8 | Component Library Specification | [design-system.md §8](./design-system.md#8-component-library) |
| 9 | Responsive Layout Guidelines | [design-system.md §9](./design-system.md#9-responsive-layout) |
| 10 | Frontend Folder Structure | [implementation-guide.md §1](./implementation-guide.md#1-folder-structure) |
| 11 | State Management Architecture | [implementation-guide.md §2](./implementation-guide.md#2-state-management) |
| 12 | Routing Architecture | [implementation-guide.md §3](./implementation-guide.md#3-routing) |
| 13 | API Integration Strategy | [implementation-guide.md §4](./implementation-guide.md#4-api-integration) |
| 14 | Accessibility Checklist | [implementation-guide.md §5](./implementation-guide.md#5-accessibility) |
| 15 | Performance Optimization Plan | [implementation-guide.md §6](./implementation-guide.md#6-performance) |
| 16 | Testing Strategy | [implementation-guide.md §7](./implementation-guide.md#7-testing) |
| 17 | UI Implementation Guide | [implementation-guide.md §8](./implementation-guide.md#8-ui-implementation-guide) |
| 18 | Design Tokens | `frontend/src/styles/tokens.css` + [design-system.md §2](./design-system.md#2-design-tokens) |
| 19 | Theme Specification | [design-system.md §3](./design-system.md#3-theme-specification) |
| 20 | Developer Handoff Documentation | [implementation-guide.md §9](./implementation-guide.md#9-developer-handoff) |

---

## Technology Stack (Target)

| Layer | Technology | Current | Migration |
|-------|------------|---------|-----------|
| Framework | Next.js App Router | 14.2 ✅ | Upgrade to 15.x |
| Language | TypeScript | ✅ | — |
| Styling | Tailwind CSS | ✅ | Adopt design tokens |
| Components | shadcn/ui | ❌ Headless UI | Migrate |
| Icons | Lucide React | ❌ Heroicons | Migrate |
| Client State | Zustand | ❌ | Add |
| Server State | TanStack Query | ✅ | Extend query keys |
| Forms | React Hook Form + Zod | Partial ✅ | Standardize |
| Tables | TanStack Table | ❌ Custom | Add + virtualize |
| Charts | Recharts | ✅ | Extend |
| Animations | Framer Motion | ❌ | Add |
| Maps | Mapbox GL | ❌ | Add for geo views |

---

## UX Pillars (Day-One Features)

These are **not** post-launch additions — they are core to Phase 4:

1. **Command Palette** (`⌘K` / `Ctrl+K`) — navigation, actions, search
2. **AI-First Global Search** — natural language in top bar
3. **Customizable Dashboards** — draggable widgets, saved layouts
4. **Enterprise Data Tables** — virtualization, column config, saved views, bulk actions
5. **Company 360° / Contact 360°** — unified entity workspaces
6. **Dark Mode + Keyboard Shortcuts + Responsive** — first-class from launch

---

## Relationship to Backend (Phase 3)

| Frontend Module | Backend API (Phase 3) |
|-----------------|----------------------|
| Dashboard | `GET /analytics/dashboard`, `/analytics/full` |
| Companies | `GET/POST/PATCH/DELETE /companies` |
| Contacts | `GET/POST/PATCH/DELETE /contacts` |
| Lead Discovery | `POST /search`, `POST /search/ai` |
| AI Assistant | `POST /search/ai`, `GET /ai/recommendations` |
| CRM | `GET/POST /crm/*` |
| Imports/Exports | `POST /imports`, `POST /exports` |
| Admin | `GET /admin/*` |
| Settings | `PATCH /organizations/current`, `/users/me` |

---

## Implementation Phases

| Sprint | Focus |
|--------|-------|
| 1–2 | App shell, design tokens, shadcn/ui, theme, command palette |
| 3–4 | Data table system, Company/Contact 360°, global AI search |
| 5–6 | Lead Discovery, CRM Kanban, imports/exports wizards |
| 7–8 | Dashboard widgets, analytics, admin panel |
| 9–10 | Accessibility audit, performance, E2E tests, polish |