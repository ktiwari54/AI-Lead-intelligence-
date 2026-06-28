'use client'

import { useCallback, useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { Command } from 'cmdk'
import {
  LayoutDashboard,
  Building2,
  Users,
  Search,
  Moon,
  Sun,
  Monitor,
  Plus,
  Download,
} from 'lucide-react'
import { useCommandPaletteStore } from '@/stores/command-palette-store'
import { useThemeStore, applyThemeClass, resolveTheme, type Theme } from '@/stores/theme-store'
import { commandPaletteRoutes, commandPaletteActions } from '@/config/navigation'
import { cn } from '@/lib/utils'

const ROUTE_ICONS: Record<string, React.ElementType> = {
  Dashboard: LayoutDashboard,
  Companies: Building2,
  Contacts: Users,
  'Lead Discovery': Search,
}

export function CommandPalette() {
  const router = useRouter()
  const open = useCommandPaletteStore((s) => s.open)
  const setOpen = useCommandPaletteStore((s) => s.setOpen)
  const setTheme = useThemeStore((s) => s.setTheme)
  const [search, setSearch] = useState('')

  const run = useCallback(
    (fn: () => void) => {
      setOpen(false)
      setSearch('')
      fn()
    },
    [setOpen]
  )

  const navigate = (href: string) => run(() => router.push(href))

  const toggleTheme = (theme: Theme) =>
    run(() => {
      setTheme(theme)
      applyThemeClass(resolveTheme(theme))
    })

  useEffect(() => {
    if (!open) setSearch('')
  }, [open])

  if (!open) return null

  return (
    <div className="fixed inset-0 z-overlay">
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={() => setOpen(false)}
        aria-hidden
      />
      <div className="absolute left-1/2 top-[20%] w-full max-w-lg -translate-x-1/2 px-4">
        <Command
          className="overflow-hidden rounded-xl border border-border bg-popover text-popover-foreground shadow-xl"
          shouldFilter
        >
          <div className="flex items-center border-b border-border px-3">
            <Search className="mr-2 h-4 w-4 shrink-0 text-muted-foreground" />
            <Command.Input
              value={search}
              onValueChange={setSearch}
              placeholder="Type a command or search..."
              className="flex h-12 w-full bg-transparent text-sm outline-none placeholder:text-muted-foreground"
              autoFocus
            />
          </div>
          <Command.List className="max-h-80 overflow-y-auto p-2">
            <Command.Empty className="py-6 text-center text-sm text-muted-foreground">
              No results found.
            </Command.Empty>

            <Command.Group heading="Navigation" className="[&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5 [&_[cmdk-group-heading]]:text-xs [&_[cmdk-group-heading]]:font-medium [&_[cmdk-group-heading]]:text-muted-foreground">
              {commandPaletteRoutes.map((route) => {
                const Icon = ROUTE_ICONS[route.label] ?? LayoutDashboard
                return (
                  <Command.Item
                    key={route.href + route.label}
                    value={`${route.label} ${route.keywords.join(' ')}`}
                    onSelect={() => navigate(route.href)}
                    className={cn(
                      'flex cursor-pointer items-center gap-2 rounded-lg px-2 py-2 text-sm',
                      'aria-selected:bg-accent aria-selected:text-accent-foreground'
                    )}
                  >
                    <Icon className="h-4 w-4 text-muted-foreground" />
                    {route.label}
                  </Command.Item>
                )
              })}
            </Command.Group>

            <Command.Group heading="Actions" className="[&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5 [&_[cmdk-group-heading]]:text-xs [&_[cmdk-group-heading]]:font-medium [&_[cmdk-group-heading]]:text-muted-foreground">
              {commandPaletteActions.map((action) => (
                <Command.Item
                  key={action.label}
                  value={`${action.label} ${action.keywords.join(' ')}`}
                  onSelect={() => navigate(action.href)}
                  className={cn(
                    'flex cursor-pointer items-center gap-2 rounded-lg px-2 py-2 text-sm',
                    'aria-selected:bg-accent aria-selected:text-accent-foreground'
                  )}
                >
                  <Plus className="h-4 w-4 text-muted-foreground" />
                  {action.label}
                </Command.Item>
              ))}
              <Command.Item
                value="export contacts download"
                onSelect={() => navigate('/contacts')}
                className={cn(
                  'flex cursor-pointer items-center gap-2 rounded-lg px-2 py-2 text-sm',
                  'aria-selected:bg-accent aria-selected:text-accent-foreground'
                )}
              >
                <Download className="h-4 w-4 text-muted-foreground" />
                Export contacts
              </Command.Item>
            </Command.Group>

            <Command.Group heading="Theme" className="[&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5 [&_[cmdk-group-heading]]:text-xs [&_[cmdk-group-heading]]:font-medium [&_[cmdk-group-heading]]:text-muted-foreground">
              <Command.Item
                value="light mode theme"
                onSelect={() => toggleTheme('light')}
                className={cn(
                  'flex cursor-pointer items-center gap-2 rounded-lg px-2 py-2 text-sm',
                  'aria-selected:bg-accent aria-selected:text-accent-foreground'
                )}
              >
                <Sun className="h-4 w-4 text-muted-foreground" />
                Light mode
              </Command.Item>
              <Command.Item
                value="dark mode theme"
                onSelect={() => toggleTheme('dark')}
                className={cn(
                  'flex cursor-pointer items-center gap-2 rounded-lg px-2 py-2 text-sm',
                  'aria-selected:bg-accent aria-selected:text-accent-foreground'
                )}
              >
                <Moon className="h-4 w-4 text-muted-foreground" />
                Dark mode
              </Command.Item>
              <Command.Item
                value="system theme"
                onSelect={() => toggleTheme('system')}
                className={cn(
                  'flex cursor-pointer items-center gap-2 rounded-lg px-2 py-2 text-sm',
                  'aria-selected:bg-accent aria-selected:text-accent-foreground'
                )}
              >
                <Monitor className="h-4 w-4 text-muted-foreground" />
                System theme
              </Command.Item>
            </Command.Group>
          </Command.List>
        </Command>
      </div>
    </div>
  )
}