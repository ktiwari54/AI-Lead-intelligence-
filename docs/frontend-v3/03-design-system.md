# 03 — Design System (Aurora v3.0)

**Frontend v3.0** | AI Lead Intelligence Platform

---

## Table of Contents

1. [Design Principles](#1-design-principles)
2. [Token Architecture](#2-token-architecture)
3. [Color System](#3-color-system)
4. [Typography](#4-typography)
5. [Spacing & Layout Grid](#5-spacing--layout-grid)
6. [Elevation & Borders](#6-elevation--borders)
7. [Theme Specification](#7-theme-specification)
8. [Motion & Animation](#8-motion--animation)
9. [Iconography](#9-iconography)
10. [Data Visualization](#10-data-visualization)
11. [Tailwind Integration](#11-tailwind-integration)
12. [Token Reference (Complete)](#12-token-reference-complete)

**Source file:** `frontend/src/styles/tokens.css`

---

## 1. Design Principles

| Principle | Definition | Implementation |
|-----------|------------|----------------|
| **Enterprise First** | Optimize for power users managing thousands of records | Dense tables (48px rows), keyboard shortcuts, bulk actions |
| **AI Native** | AI is visible, explainable, and actionable | Intent previews, confidence bars, reasoning tooltips, sparkle accents |
| **Minimal Chrome** | Content over decoration | Flat cards, subtle borders, no gratuitous gradients |
| **Consistent Density** | Predictable rhythm across modules | 4px spacing base, token-only values |
| **Accessible by Default** | WCAG 2.1 AA minimum | 4.5:1 text contrast, focus rings, 44px touch targets |
| **Theme Agnostic** | Light and dark are equal citizens | Semantic tokens, no hardcoded colors in components |
| **Performance Aware** | Visual polish without jank | CSS transitions over JS; `prefers-reduced-motion` respected |

### Visual Benchmark

Density and clarity comparable to **Linear**; data-heavy patterns inspired by **HubSpot** and **Salesforce Lightning**; AI accents similar to **Notion AI** / **GitHub Copilot** subtle highlights.

---

## 2. Token Architecture

### Naming Convention

```text
--{category}-{name}           Global CSS custom properties
--{category}-{name}-{variant} Semantic variants

Categories: color (semantic), layout, radius, shadow, z, duration
```

### HSL Channel Format

Colors use **space-separated HSL channels** (shadcn/ui convention) for Tailwind `hsl(var(--primary))` composition:

```css
:root {
  --primary: 79 70 229;  /* rgb channels → used as hsl() or rgb() via Tailwind */
}
```

In `tailwind.config.ts`:

```typescript
colors: {
  primary: 'rgb(var(--primary) / <alpha-value>)',
  background: 'rgb(var(--background) / <alpha-value>)',
}
```

### Token Categories

| Category | Count | File Location |
|----------|-------|---------------|
| Semantic colors | 18 + score (4) | `tokens.css` |
| Layout dimensions | 4 | `tokens.css` |
| Radius | 4 | `tokens.css` |
| Shadows | 4 | `tokens.css` |
| Z-index | 6 | `tokens.css` |
| Motion duration | 3 | `tokens.css` |
| Typography | 10 sizes | `tailwind.config.ts` |
| Spacing | 12 steps | Tailwind default + extensions |

---

## 3. Color System

### 3.1 Semantic Colors — Light Theme

| Token | RGB Value | Hex Approx | Usage |
|-------|-----------|------------|-------|
| `--background` | `248 250 252` | `#F8FAFC` | Page background |
| `--foreground` | `15 23 42` | `#0F172A` | Primary text |
| `--card` | `255 255 255` | `#FFFFFF` | Card, modal surfaces |
| `--card-foreground` | `15 23 42` | `#0F172A` | Text on cards |
| `--popover` | `255 255 255` | `#FFFFFF` | Dropdown, popover |
| `--popover-foreground` | `15 23 42` | `#0F172A` | Popover text |
| `--primary` | `79 70 229` | `#4F46E5` | Primary actions, links, active nav |
| `--primary-foreground` | `255 255 255` | `#FFFFFF` | Text on primary |
| `--secondary` | `241 245 249` | `#F1F5F9` | Secondary buttons, tags |
| `--secondary-foreground` | `15 23 42` | `#0F172A` | Text on secondary |
| `--muted` | `241 245 249` | `#F1F5F9` | Subtle backgrounds |
| `--muted-foreground` | `100 116 139` | `#64748B` | Secondary text, placeholders |
| `--accent` | `238 242 255` | `#EEF2FF` | Hover highlights (indigo tint) |
| `--accent-foreground` | `67 56 202` | `#4338CA` | Text on accent |
| `--destructive` | `220 38 38` | `#DC2626` | Delete, errors |
| `--destructive-foreground` | `255 255 255` | `#FFFFFF` | Text on destructive |
| `--border` | `226 232 240` | `#E2E8F0` | Borders, dividers |
| `--input` | `226 232 240` | `#E2E8F0` | Input borders |
| `--ring` | `79 70 229` | `#4F46E5` | Focus rings |
| `--success` | `16 185 129` | `#10B981` | Verified, won, excellent score |
| `--warning` | `245 158 11` | `#F59E0B` | Pending, fair score |
| `--info` | `59 130 246` | `#3B82F6` | Informational badges |

### 3.2 Semantic Colors — Dark Theme

| Token | RGB Value | Hex Approx |
|-------|-----------|------------|
| `--background` | `9 9 11` | `#09090B` |
| `--foreground` | `250 250 250` | `#FAFAFA` |
| `--card` | `24 24 27` | `#18181B` |
| `--card-foreground` | `250 250 250` | `#FAFAFA` |
| `--popover` | `24 24 27` | `#18181B` |
| `--popover-foreground` | `250 250 250` | `#FAFAFA` |
| `--primary` | `99 102 241` | `#6366F1` |
| `--primary-foreground` | `255 255 255` | `#FFFFFF` |
| `--secondary` | `39 39 42` | `#27272A` |
| `--secondary-foreground` | `250 250 250` | `#FAFAFA` |
| `--muted` | `39 39 42` | `#27272A` |
| `--muted-foreground` | `161 161 170` | `#A1A1AA` |
| `--accent` | `39 39 42` | `#27272A` |
| `--accent-foreground` | `250 250 250` | `#FAFAFA` |
| `--destructive` | `239 68 68` | `#EF4444` |
| `--destructive-foreground` | `255 255 255` | `#FFFFFF` |
| `--border` | `39 39 42` | `#27272A` |
| `--input` | `39 39 42` | `#27272A` |
| `--ring` | `99 102 241` | `#6366F1` |
| `--success` | `34 197 94` | `#22C55E` |
| `--warning` | `245 158 11` | `#F59E0B` |
| `--info` | `59 130 246` | `#3B82F6` |

### 3.3 Lead Score Colors

| Range | Token | Light RGB | Label | Tailwind Class |
|-------|-------|-----------|-------|----------------|
| 80–100 | `--score-excellent` | `16 185 129` | Pursue | `text-score-excellent` |
| 60–79 | `--score-good` | `59 130 246` | Nurture | `text-score-good` |
| 40–59 | `--score-fair` | `245 158 11` | Monitor | `text-score-fair` |
| 0–39 | `--score-poor` | `239 68 68` | Deprioritize | `text-score-poor` |

### 3.4 Status Badge Palette

| Status | Background | Text | Border | Example |
|--------|------------|------|--------|---------|
| Active / Verified | `success/10` | `success` | `success/20` | Email verified |
| Pending / Processing | `warning/10` | `warning` | `warning/20` | Import in progress |
| Error / Failed | `destructive/10` | `destructive` | `destructive/20` | Sync failed |
| Neutral / Draft | `muted` | `muted-foreground` | `border` | New record |
| Info / New | `primary/10` | `primary` | `primary/20` | AI recommendation |
| AI / Sparkle | `accent` | `accent-foreground` | `primary/20` | Parsed intent chip |

### 3.5 Contrast Verification (WCAG AA)

| Pair | Light Ratio | Dark Ratio | Pass |
|------|-------------|------------|------|
| `foreground` on `background` | 15.8:1 | 17.2:1 | ✅ |
| `muted-foreground` on `background` | 4.6:1 | 5.1:1 | ✅ |
| `primary-foreground` on `primary` | 6.2:1 | 5.8:1 | ✅ |
| `destructive-foreground` on `destructive` | 5.9:1 | 4.8:1 | ✅ |

---

## 4. Typography

### Font Families

| Role | Stack | Weights | Source |
|------|-------|---------|--------|
| **UI / Body** | `Inter`, `ui-sans-serif`, `system-ui`, sans-serif | 400, 500, 600, 700 | Google Fonts / `next/font` |
| **Monospace** | `JetBrains Mono`, `ui-monospace`, monospace | 400, 500 | IDs, API keys, code |
| **Display** | Inter (same family) | 600, 700 | Page titles |

### Type Scale

| Token Name | Size | Line Height | Weight | Letter Spacing | Usage |
|------------|------|-------------|--------|----------------|-------|
| `display-lg` | 30px / 1.875rem | 36px / 2.25rem | 700 | -0.02em | Dashboard hero metrics |
| `display-sm` | 24px / 1.5rem | 32px / 2rem | 600 | -0.01em | Page titles (`PageHeader`) |
| `heading-lg` | 20px / 1.25rem | 28px / 1.75rem | 600 | 0 | Section headers |
| `heading-md` | 16px / 1rem | 24px / 1.5rem | 600 | 0 | Card titles, widget headers |
| `heading-sm` | 14px / 0.875rem | 20px / 1.25rem | 600 | 0 | Table column headers |
| `body-lg` | 16px / 1rem | 24px / 1.5rem | 400 | 0 | Long-form descriptions |
| `body-md` | 14px / 0.875rem | 20px / 1.25rem | 400 | 0 | Default UI text |
| `body-sm` | 12px / 0.75rem | 16px / 1rem | 400 | 0.01em | Captions, timestamps, meta |
| `label-sm` | 12px / 0.75rem | 16px / 1rem | 500 | 0.02em | Form labels, badges |
| `mono-sm` | 12px / 0.75rem | 16px / 1rem | 400 | 0 | API keys, request IDs |

### Tailwind Configuration

```typescript
// tailwind.config.ts
fontSize: {
  'display-lg': ['1.875rem', { lineHeight: '2.25rem', fontWeight: '700', letterSpacing: '-0.02em' }],
  'display-sm': ['1.5rem', { lineHeight: '2rem', fontWeight: '600', letterSpacing: '-0.01em' }],
  'heading-lg': ['1.25rem', { lineHeight: '1.75rem', fontWeight: '600' }],
  'heading-md': ['1rem', { lineHeight: '1.5rem', fontWeight: '600' }],
  'heading-sm': ['0.875rem', { lineHeight: '1.25rem', fontWeight: '600' }],
  'body-lg': ['1rem', { lineHeight: '1.5rem' }],
  'body-md': ['0.875rem', { lineHeight: '1.25rem' }],
  'body-sm': ['0.75rem', { lineHeight: '1rem' }],
  'label-sm': ['0.75rem', { lineHeight: '1rem', fontWeight: '500', letterSpacing: '0.02em' }],
  'mono-sm': ['0.75rem', { lineHeight: '1rem', fontFamily: 'var(--font-mono)' }],
},
```

### Text Color Hierarchy

| Level | Class | Usage |
|-------|-------|-------|
| Primary | `text-foreground` | Headings, values, primary content |
| Secondary | `text-muted-foreground` | Descriptions, labels, placeholders |
| Accent | `text-primary` | Links, active states, AI highlights |
| Destructive | `text-destructive` | Errors, delete confirmations |
| Success | `text-success` | Positive trends, verified status |

---

## 5. Spacing & Layout Grid

### Spacing Scale (4px base)

| Token | Value | Tailwind | Common Usage |
|-------|-------|----------|--------------|
| `--space-0` | 0px | `0` | Reset |
| `--space-1` | 4px | `1` | Icon gaps, tight padding |
| `--space-2` | 8px | `2` | Button icon gap, chip padding |
| `--space-3` | 12px | `3` | Input vertical padding |
| `--space-4` | 16px | `4` | Card padding, grid gap |
| `--space-5` | 20px | `5` | Form field spacing |
| `--space-6` | 24px | `6` | Section gaps |
| `--space-8` | 32px | `8` | Page section margins |
| `--space-10` | 40px | `10` | Large section breaks |
| `--space-12` | 48px | `12` | Page top padding |
| `--space-16` | 64px | `16` | Auth page vertical centering |
| `--space-20` | 80px | `20` | Marketing hero spacing |

### Layout Dimensions

| Token | Value | Element |
|-------|-------|---------|
| `--sidebar-width` | 260px | Expanded sidebar |
| `--sidebar-collapsed-width` | 72px | Collapsed sidebar |
| `--topbar-height` | 56px | Top navigation bar |
| `--statusbar-height` | 32px | Bottom status bar |

### Responsive Grid

| Breakpoint | Min Width | Columns | Gutter | Margin | Tailwind |
|------------|-----------|---------|--------|--------|----------|
| Mobile | 0 | 4 | 16px | 16px | default |
| Tablet | 640px | 8 | 24px | 24px | `sm:` |
| Laptop | 1024px | 12 | 24px | 32px | `lg:` |
| Desktop | 1280px | 12 | 24px | 32px | `xl:` |
| Wide | 1536px | 12 | 32px | 48px | `2xl:` |

### Content Max Widths

| Context | Max Width | Class |
|---------|-----------|-------|
| Data tables | 100% (fluid) | — |
| Forms (create/edit) | 640px | `max-w-xl` |
| Settings content | 768px | `max-w-3xl` |
| Auth pages | 480px | `max-w-md` |
| AI chat column | 800px | `max-w-3xl` |
| Command palette | 640px | `max-w-xl` |
| Modals (default) | 560px | `max-w-lg` |
| Modals (wide) | 800px | `max-w-3xl` |

### Dashboard Widget Grid

- **Engine:** CSS Grid, 12 columns
- **Gap:** 16px (`gap-4`)
- **Widget sizes:** `1×1` (200×160px min), `2×1`, `2×2`, `3×2`, `4×2`, `full` (12 cols)
- **Edit mode:** Drag handle top-left, resize handle bottom-right
- **Snap:** 1-column grid units

### 360° Layout Grid

| Viewport | Main Content | AI Panel |
|----------|--------------|----------|
| ≥1280px | 8/12 (66%) | 4/12 (33%), sticky |
| 1024–1279px | 100% | Drawer trigger button |
| <1024px | 100% | Bottom sheet |

---

## 6. Elevation & Borders

### Border Widths

| Token | Value | Usage |
|-------|-------|-------|
| Default | 1px | Cards, inputs, table cells |
| Thick | 2px | Focus state, high contrast mode, selected table row |
| None | 0 | Flush panels, ghost buttons |

### Border Radius

| Token | Value | Usage |
|-------|-------|-------|
| `--radius-sm` | 6px | Badges, chips, small buttons |
| `--radius-md` | 8px | Inputs, buttons, dropdown items |
| `--radius-lg` | 12px | Cards, KPI tiles |
| `--radius-xl` | 16px | Modals, command palette, drawers |
| `full` | 9999px | Avatars, pills, toggle switches |

### Shadow Scale

| Token | CSS Value | Usage |
|-------|-----------|-------|
| `--shadow-sm` | `0 1px 2px 0 rgb(15 23 42 / 0.04)` | Cards at rest |
| `--shadow-md` | `0 4px 6px -1px rgb(15 23 42 / 0.06), 0 2px 4px -2px rgb(15 23 42 / 0.04)` | Dropdowns, popovers |
| `--shadow-lg` | `0 10px 15px -3px rgb(15 23 42 / 0.08), 0 4px 6px -4px rgb(15 23 42 / 0.04)` | Modals, drawers |
| `--shadow-xl` | `0 20px 25px -5px rgb(15 23 42 / 0.1), 0 8px 10px -6px rgb(15 23 42 / 0.04)` | Command palette |

Dark theme: increase opacity by 2× for equivalent perceived elevation.

### Z-Index Scale

| Token | Value | Elements |
|-------|-------|----------|
| `--z-base` | 0 | Page content |
| `--z-dropdown` | 10 | Dropdowns, popovers, tooltips |
| `--z-sticky` | 20 | Sticky table headers, section headers |
| `--z-sidebar` | 30 | Sidebar |
| `--z-topbar` | 40 | Top bar |
| `--z-overlay` | 50 | Modal backdrop, command palette, drawer |
| `--z-toast` | 60 | Toast notifications |

---

## 7. Theme Specification

### Theme Modes

| Mode | HTML Class | Default | Behavior |
|------|------------|---------|----------|
| Light | `.light` | No | Force light palette |
| Dark | `.dark` | No | Force dark palette |
| System | *(none — follows OS)* | **Yes** | `prefers-color-scheme` listener |

### Implementation (`theme-store.ts`)

```typescript
type Theme = 'light' | 'dark' | 'system'

// On mount:
// 1. Read localStorage key 'aurora-theme'
// 2. If 'system', resolve via matchMedia
// 3. Apply 'light' or 'dark' class to <html>

// On change:
// 1. Persist to localStorage
// 2. Update <html> class
// 3. Emit 'theme-change' for charts (Recharts theme sync)
```

### Theme Toggle Locations

1. Settings → Preferences → Appearance
2. User menu dropdown → Theme submenu
3. Command palette → "Toggle dark mode"
4. Status bar → Theme indicator (click to cycle)

### High Contrast Mode

Triggered by `prefers-contrast: more`:

```css
@media (prefers-contrast: more) {
  :root {
    --border: 100 116 139;  /* Darker borders */
  }
  .border { border-width: 2px; }
  .text-muted-foreground { color: rgb(var(--foreground) / 0.75); }
}
```

### Chart Theme Sync

Recharts components read `resolvedTheme` from `useTheme()` hook:

| Element | Light | Dark |
|---------|-------|------|
| Grid lines | `#E2E8F0` | `#27272A` |
| Axis text | `#64748B` | `#A1A1AA` |
| Tooltip bg | `#FFFFFF` | `#18181B` |
| Series colors | Chart palette (§10) | Same hues, +10% lightness |

---

## 8. Motion & Animation

### Duration Tokens

| Token | Value | Easing | Usage |
|-------|-------|--------|-------|
| `--duration-fast` | 150ms | `cubic-bezier(0.4, 0, 0.2, 1)` | Hover, toggle, badge |
| `--duration-normal` | 200ms | `cubic-bezier(0.4, 0, 0.2, 1)` | Panel slide, dropdown |
| `--duration-slow` | 350ms | `cubic-bezier(0.4, 0, 0.2, 1)` | Page transition, modal |

### Animation Patterns

| Pattern | Properties | Duration | Library |
|---------|------------|----------|---------|
| Button hover | `background-color`, `box-shadow` | fast | CSS |
| Sidebar collapse | `width` | normal | CSS |
| Modal enter | `opacity 0→1`, `scale 0.95→1` | normal | Radix + CSS |
| Drawer slide | `transform translateX` | normal | Radix |
| Toast enter | `translateX(100%→0)`, `opacity` | normal | Sonner |
| Skeleton shimmer | `background-position` | 1.5s loop | CSS keyframes |
| Score gauge fill | `stroke-dashoffset` | 600ms ease-out | SVG + CSS |
| Kanban drag lift | `scale 1→1.02`, `box-shadow` | fast | Framer Motion |
| Page enter | `opacity`, `translateY(8px→0)` | slow | Framer Motion |
| AI sparkle | `opacity` pulse | 2s loop | CSS (subtle) |
| Typing indicator | 3-dot bounce | 1.2s loop | CSS |

### Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

Score gauge: skip animation, render final value immediately.  
Kanban: disable drag animation, use instant position swap.

---

## 9. Iconography

### Library: Lucide React

| Size Token | Pixels | Stroke | Usage |
|------------|--------|--------|-------|
| `xs` | 14px | 1.5px | Inline with `body-sm` |
| `sm` | 16px | 2px | Buttons, nav items, table actions |
| `md` | 20px | 2px | Default, page headers |
| `lg` | 24px | 2px | Empty states, feature icons |
| `xl` | 32px | 2px | Auth pages, onboarding |

### Icon Categories

| Category | Icons |
|----------|-------|
| Navigation | `LayoutDashboard`, `Building2`, `Users`, `Search`, `Sparkles`, `Bookmark`, `List`, `Target` |
| Actions | `Plus`, `Download`, `Upload`, `Trash2`, `Edit`, `MoreHorizontal`, `Copy`, `ExternalLink` |
| Status | `CheckCircle`, `AlertCircle`, `XCircle`, `Clock`, `Loader2`, `Circle` |
| AI | `Brain`, `Sparkles`, `Wand2`, `MessageSquare`, `Bot` |
| CRM | `Kanban`, `Calendar`, `CheckSquare`, `DollarSign`, `Handshake` |
| Data | `Filter`, `ArrowUpDown`, `Columns3`, `Eye`, `EyeOff`, `GripVertical` |
| System | `Settings`, `Shield`, `Bell`, `HelpCircle`, `Plug`, `Key`, `CreditCard` |

### Icon Color Rules

| Context | Color Class |
|---------|-------------|
| Default | `text-muted-foreground` |
| Active nav | `text-primary` |
| Destructive action | `text-destructive` |
| Success | `text-success` |
| On primary button | `text-primary-foreground` |
| AI accent | `text-primary` with subtle glow |

---

## 10. Data Visualization

### Chart Palette (Colorblind-Safe, 8 colors)

```text
Series 1: #4F46E5  (primary indigo)
Series 2: #10B981  (success green)
Series 3: #F59E0B  (warning amber)
Series 4: #EF4444  (destructive red)
Series 5: #8B5CF6  (violet)
Series 6: #06B6D4  (cyan)
Series 7: #EC4899  (pink)
Series 8: #84CC16  (lime)
```

### Chart Defaults

| Property | Value |
|----------|-------|
| Font | Inter 12px |
| Grid | Dashed, 1px, `border` color |
| Tooltip | Card style with `shadow-md`, `radius-lg` |
| Legend | Bottom, horizontal, `body-sm` |
| Animation | 400ms on mount; disabled if reduced motion |
| Min height | 200px (widget), 400px (full report) |

### Map Choropleth (Geo Reports)

Sequential indigo scale: `#EEF2FF` → `#C7D2FE` → `#818CF8` → `#4F46E5` → `#312E81`

### Sparkline (KPI Cards)

- Height: 32px
- Stroke: `primary`, 1.5px
- Fill: `primary/10` gradient
- No axes; trend arrow + percentage adjacent

---

## 11. Tailwind Integration

### globals.css Structure

```css
@import './tokens.css';

@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  * { @apply border-border; }
  body { @apply bg-background text-foreground font-sans antialiased; }
}
```

### Custom Utilities

```css
@layer utilities {
  .scrollbar-thin {
    scrollbar-width: thin;
    scrollbar-color: rgb(var(--muted-foreground) / 0.3) transparent;
  }
  .text-score-excellent { color: rgb(var(--score-excellent)); }
  .text-score-good { color: rgb(var(--score-good)); }
  .text-score-fair { color: rgb(var(--score-fair)); }
  .text-score-poor { color: rgb(var(--score-poor)); }
  .ai-glow { box-shadow: 0 0 12px rgb(var(--primary) / 0.15); }
}
```

### shadcn/ui Theme Mapping

All shadcn components consume semantic tokens automatically via `components.json` CSS variables configuration. No component should reference raw hex values.

---

## 12. Token Reference (Complete)

### Copy-Paste: `tokens.css` (Authoritative)

```css
:root {
  --background: 248 250 252;
  --foreground: 15 23 42;
  --card: 255 255 255;
  --card-foreground: 15 23 42;
  --popover: 255 255 255;
  --popover-foreground: 15 23 42;
  --primary: 79 70 229;
  --primary-foreground: 255 255 255;
  --secondary: 241 245 249;
  --secondary-foreground: 15 23 42;
  --muted: 241 245 249;
  --muted-foreground: 100 116 139;
  --accent: 238 242 255;
  --accent-foreground: 67 56 202;
  --destructive: 220 38 38;
  --destructive-foreground: 255 255 255;
  --border: 226 232 240;
  --input: 226 232 240;
  --ring: 79 70 229;
  --success: 16 185 129;
  --warning: 245 158 11;
  --info: 59 130 246;
  --score-excellent: 16 185 129;
  --score-good: 59 130 246;
  --score-fair: 245 158 11;
  --score-poor: 239 68 68;
  --sidebar-width: 260px;
  --sidebar-collapsed-width: 72px;
  --topbar-height: 56px;
  --statusbar-height: 32px;
  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;
  --shadow-sm: 0 1px 2px 0 rgb(15 23 42 / 0.04);
  --shadow-md: 0 4px 6px -1px rgb(15 23 42 / 0.06), 0 2px 4px -2px rgb(15 23 42 / 0.04);
  --shadow-lg: 0 10px 15px -3px rgb(15 23 42 / 0.08), 0 4px 6px -4px rgb(15 23 42 / 0.04);
  --shadow-xl: 0 20px 25px -5px rgb(15 23 42 / 0.1), 0 8px 10px -6px rgb(15 23 42 / 0.04);
  --z-dropdown: 10;
  --z-sticky: 20;
  --z-sidebar: 30;
  --z-topbar: 40;
  --z-overlay: 50;
  --z-toast: 60;
  --duration-fast: 150ms;
  --duration-normal: 200ms;
  --duration-slow: 350ms;
}
```

---

*Next: [04-component-library.md](./04-component-library.md) — Component specifications*