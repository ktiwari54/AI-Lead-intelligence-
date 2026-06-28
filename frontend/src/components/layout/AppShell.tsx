'use client'

import { Sidebar } from './Sidebar'
import { TopBar } from './TopBar'
import { CommandPalette } from './CommandPalette'
import { AIAssistantDrawer } from '@/features/ai/AIAssistantDrawer'
import { KeyboardShortcutsDialog } from './KeyboardShortcutsDialog'
import { StatusBar } from '@/components/enterprise/StatusBar'
import { useKeyboardShortcutsStore } from '@/stores/keyboard-shortcuts-store'
import { useKeyboardShortcut } from '@/hooks/useKeyboardShortcut'
import { useSidebarStore } from '@/stores/sidebar-store'
import { cn } from '@/lib/utils'

function ShellShortcuts() {
  const toggle = useKeyboardShortcutsStore((s) => s.toggle)
  useKeyboardShortcut('?', toggle, { shift: false })
  return null
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const collapsed = useSidebarStore((s) => s.collapsed)

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-toast focus:rounded-lg focus:bg-primary focus:px-4 focus:py-2 focus:text-primary-foreground"
      >
        Skip to main content
      </a>

      <div className="flex flex-1">
        <Sidebar />

        <div
          className={cn(
            'flex min-h-screen flex-1 flex-col transition-all duration-normal',
            collapsed ? 'lg:pl-sidebar-collapsed' : 'lg:pl-sidebar'
          )}
        >
          <TopBar />
          <main
            id="main-content"
            className="relative flex-1 overflow-y-auto bg-gradient-to-br from-background via-background to-primary/[0.03] p-4 lg:p-8"
          >
            <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_rgba(79,70,229,0.06),_transparent_50%)]" aria-hidden />
            <div className="relative">{children}</div>
          </main>
          <StatusBar />
        </div>
      </div>

      <ShellShortcuts />
      <CommandPalette />
      <AIAssistantDrawer />
      <KeyboardShortcutsDialog />
    </div>
  )
}