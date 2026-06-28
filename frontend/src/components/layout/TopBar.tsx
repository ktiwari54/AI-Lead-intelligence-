'use client'

import Link from 'next/link'
import { Menu, Bell, LogOut, User, Settings, Sparkles, Moon, Sun } from 'lucide-react'
import { useSidebarStore } from '@/stores/sidebar-store'
import { useCommandPaletteStore } from '@/stores/command-palette-store'
import { useThemeStore } from '@/stores/theme-store'
import { useCurrentUser, useLogout } from '@/hooks/useAuth'
import { useKeyboardShortcut } from '@/hooks/useKeyboardShortcut'
import { GlobalSearch } from './GlobalSearch'
import { Breadcrumbs } from './Breadcrumbs'
import { Button } from '@/components/ui/Button'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useAIAssistantStore } from '@/stores/ai-assistant-store'

export function TopBar() {
  const toggleMobile = useSidebarStore((s) => s.toggleMobile)
  const toggleCollapsed = useSidebarStore((s) => s.toggleCollapsed)
  const setPaletteOpen = useCommandPaletteStore((s) => s.setOpen)
  const setTheme = useThemeStore((s) => s.setTheme)
  const resolvedTheme = useThemeStore((s) => s.resolvedTheme)
  const setDrawerOpen = useAIAssistantStore((s) => s.setDrawerOpen)
  const { data: user } = useCurrentUser()
  const logout = useLogout()

  useKeyboardShortcut('k', () => setPaletteOpen(true), { meta: true })
  useKeyboardShortcut('b', () => toggleCollapsed(), { meta: true })
  useKeyboardShortcut('j', () => setDrawerOpen(true), { meta: true })

  const initials = user?.full_name?.split(' ').map((n) => n[0]).join('').slice(0, 2).toUpperCase() ?? '?'

  return (
    <header className="sticky top-0 z-topbar flex h-topbar items-center gap-3 border-b border-border bg-card/90 px-4 shadow-sm backdrop-blur-xl lg:px-6">
      <Button variant="ghost" size="icon" onClick={toggleMobile} className="lg:hidden" aria-label="Open menu">
        <Menu className="h-5 w-5" />
      </Button>

      <div className="hidden min-w-0 lg:block">
        <Breadcrumbs />
      </div>

      <div className="flex flex-1 items-center justify-center gap-2">
        <GlobalSearch />
        <Button
          variant="outline"
          size="sm"
          onClick={() => setPaletteOpen(true)}
          className="hidden h-9 gap-2 text-muted-foreground sm:flex"
        >
          <span>Command</span>
          <kbd className="rounded border border-border bg-muted px-1.5 py-0.5 font-mono text-[10px]">⌘K</kbd>
        </Button>
      </div>

      <div className="flex items-center gap-1">
        <Button variant="ghost" size="icon" onClick={() => setDrawerOpen(true)} aria-label="AI Assistant" title="AI Assistant (⌘J)">
          <Sparkles className="h-4 w-4 text-primary" />
        </Button>

        <Button
          variant="ghost"
          size="icon"
          onClick={() => setTheme(resolvedTheme === 'dark' ? 'light' : 'dark')}
          aria-label="Toggle theme"
        >
          {resolvedTheme === 'dark' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
        </Button>

        <Button variant="ghost" size="icon" asChild>
          <Link href="/notifications" aria-label="Notifications">
            <Bell className="h-4 w-4" />
          </Link>
        </Button>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="h-9 gap-2 px-2">
              <Avatar className="h-7 w-7">
                <AvatarFallback className="text-[10px]">{initials}</AvatarFallback>
              </Avatar>
              <span className="hidden max-w-[100px] truncate text-sm font-medium sm:inline">
                {user?.full_name?.split(' ')[0] ?? 'User'}
              </span>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-52">
            <DropdownMenuLabel>
              <p className="text-sm font-medium">{user?.full_name}</p>
              <p className="text-xs font-normal text-muted-foreground">{user?.email}</p>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem asChild>
              <Link href="/settings" className="cursor-pointer">
                <User className="mr-2 h-4 w-4" /> Profile
              </Link>
            </DropdownMenuItem>
            <DropdownMenuItem asChild>
              <Link href="/settings" className="cursor-pointer">
                <Settings className="mr-2 h-4 w-4" /> Settings
              </Link>
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={logout} className="text-destructive focus:text-destructive">
              <LogOut className="mr-2 h-4 w-4" /> Sign out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  )
}